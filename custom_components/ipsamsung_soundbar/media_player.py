from __future__ import annotations

from datetime import timedelta

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_NAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    SOURCE_LIST,
    SOURCE_WIFI,
    WIFI_INFERENCE_THRESHOLD,
)
from .device import soundbar_device_info
from .uic_client import UicClient

SCAN_INTERVAL = timedelta(seconds=5)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    async_add_entities([SamsungSoundbarEntity(hass, host, port, name)], True)


class SamsungSoundbarEntity(MediaPlayerEntity):
    _attr_supported_features = SUPPORTED_FEATURES
    _attr_icon = "mdi:soundbar"

    def __init__(self, hass: HomeAssistant, host: str, port: int, name: str) -> None:
        self.hass = hass
        self._client = UicClient(hass, host, port)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{host}_{port}"
        self._attr_device_info = soundbar_device_info(host, port, name)
        self._attr_source_list = SOURCE_LIST
        self._attr_state = MediaPlayerState.OFF
        self._attr_volume_level = None
        self._attr_is_volume_muted = None
        self._attr_source = None
        self._func_fail_count = 0

    async def _refresh_power_status(self) -> None:
        # GetPowerStatus is reliable in both power states on the HW-Q960A -
        # unlike GetFunc, it doesn't need a fallback assumption when it responds.
        power_root = await self._client.request("<name>GetPowerStatus</name>")
        if power_root is not None:
            power = power_root.findtext(".//powerStatus")
            if power == "1":
                self._attr_state = MediaPlayerState.ON
            elif power == "0":
                self._attr_state = MediaPlayerState.OFF

    async def async_update(self) -> None:
        vol_root = await self._client.request("<name>GetVolume</name>")
        if vol_root is not None:
            vol_text = vol_root.findtext(".//volume")
            if vol_text is not None and vol_text.isdigit():
                self._attr_volume_level = max(0.0, min(1.0, int(vol_text) / 100.0))

        mute_root = await self._client.request("<name>GetMute</name>")
        if mute_root is not None:
            mute_text = mute_root.findtext(".//mute")
            if mute_text is not None:
                self._attr_is_volume_muted = mute_text.lower() == "on"

        await self._refresh_power_status()

        func_root = await self._client.request("<name>GetFunc</name>")
        func_text = func_root.findtext(".//function") if func_root is not None else None
        if func_text:
            self._func_fail_count = 0
            self._attr_source = func_text
        else:
            # On the HW-Q960A, GetFunc stops returning <function> while the unit
            # is on a network-audio source (Wi-Fi/AirPlay/Spotify Connect) and
            # instead echoes an unrelated queued status message. Only infer
            # Wi-Fi after repeated failures while powered on, so a single
            # dropped request isn't mistaken for a source change.
            self._func_fail_count += 1
            if (
                self._func_fail_count >= WIFI_INFERENCE_THRESHOLD
                and self._attr_state == MediaPlayerState.ON
            ):
                self._attr_source = SOURCE_WIFI

    async def async_turn_on(self) -> None:
        # Raw PowerOn is confirmed non-functional on the HW-Q960A; SetPowerStatus
        # is the reliable command, and unlike raw PowerOn/PowerOff its ack has
        # matched the actual outcome in every test. Set state optimistically
        # (like async_select_source) so HA reflects it immediately instead of
        # waiting on an extra confirmatory round trip; the regular poll still
        # corrects it if a command is ever silently ignored.
        if await self._client.send('<name>SetPowerStatus</name><p type="dec" name="power" val="1"/>'):
            self._attr_state = MediaPlayerState.ON

    async def async_turn_off(self) -> None:
        # See async_turn_on - SetPowerStatus's ack is trustworthy, so set state
        # optimistically instead of paying for a confirmatory GetPowerStatus call.
        if await self._client.send('<name>SetPowerStatus</name><p type="dec" name="power" val="0"/>'):
            self._attr_state = MediaPlayerState.OFF

    async def async_set_volume_level(self, volume: float) -> None:
        value = int(max(0, min(100, round(volume * 100))))
        if await self._client.send(f'<name>SetVolume</name><p type="dec" name="volume" val="{value}"/>'):
            self._attr_volume_level = value / 100.0

    async def async_volume_up(self) -> None:
        if self._attr_volume_level is None:
            await self.async_update()
        current = int((self._attr_volume_level or 0) * 100)
        target = min(100, current + 1)
        await self.async_set_volume_level(target / 100.0)

    async def async_volume_down(self) -> None:
        if self._attr_volume_level is None:
            await self.async_update()
        current = int((self._attr_volume_level or 0) * 100)
        target = max(0, current - 1)
        await self.async_set_volume_level(target / 100.0)

    async def async_mute_volume(self, mute: bool) -> None:
        value = "on" if mute else "off"
        if await self._client.send(f'<name>SetMute</name><p type="str" name="mute" val="{value}"/>'):
            self._attr_is_volume_muted = mute

    async def async_select_source(self, source: str) -> None:
        if source not in SOURCE_LIST:
            return
        if await self._client.send(f'<name>SetFunc</name><p type="str" name="function" val="{source}"/>'):
            self._attr_source = source
