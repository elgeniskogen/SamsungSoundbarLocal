from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_NAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    HARMONY_DEVICE,
    HARMONY_REMOTE_ENTITY_ID,
    HARMONY_SOUND_MODE_COMMAND,
    SOUND_MODE_LIST,
    SOUND_MODE_MAX_PRESSES,
    SOUND_MODE_POLL_INTERVAL,
    SOUND_MODE_STEP_TIMEOUT,
)
from .uic_client import UicClient

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    async_add_entities([SamsungSoundModeSelect(hass, host, port, name)], True)


class SamsungSoundModeSelect(SelectEntity):
    """Sound Mode select entity.

    GetSoundMode is a working local read on the HW-Q960A, but there is no
    working local write command for it. Setting it instead drives the
    soundbar's physical Sound Mode button via an existing Harmony remote,
    which cycles through modes rather than selecting one directly. Every
    press is verified against a real GetSoundMode read - a press is never
    assumed to have succeeded or to know which mode it landed on.
    """

    _attr_options = SOUND_MODE_LIST
    _attr_icon = "mdi:surround-sound"

    def __init__(self, hass: HomeAssistant, host: str, port: int, name: str) -> None:
        self.hass = hass
        self._client = UicClient(hass, host, port)
        self._attr_name = f"{name} Sound Mode"
        self._attr_unique_id = f"{DOMAIN}_{host}_{port}_sound_mode"
        self._attr_current_option = None
        self._lock = asyncio.Lock()

    async def _get_sound_mode(self) -> str | None:
        root = await self._client.request("<name>GetSoundMode</name>")
        if root is None:
            return None
        mode = root.findtext(".//soundMode")
        if mode and mode not in SOUND_MODE_LIST:
            _LOGGER.warning("Soundbar reported unknown sound mode: %s", mode)
        return mode

    async def async_update(self) -> None:
        # Held during select_option() so a concurrent scheduled poll can't
        # read a stale value mid-sequence and overwrite the closed loop's
        # own, more current result.
        async with self._lock:
            mode = await self._get_sound_mode()
            if mode:
                self._attr_current_option = mode

    async def _press_sound_mode_button(self) -> None:
        try:
            await self.hass.services.async_call(
                "remote",
                "send_command",
                {
                    "entity_id": HARMONY_REMOTE_ENTITY_ID,
                    "device": HARMONY_DEVICE,
                    "command": HARMONY_SOUND_MODE_COMMAND,
                },
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001 - surfaced as a HA error below
            raise HomeAssistantError(
                f"Failed to send Harmony Sound Mode command via "
                f"{HARMONY_REMOTE_ENTITY_ID}: {err}"
            ) from err

    async def _wait_for_mode_change(self, previous: str | None) -> str | None:
        elapsed = 0.0
        while elapsed < SOUND_MODE_STEP_TIMEOUT:
            await asyncio.sleep(SOUND_MODE_POLL_INTERVAL)
            elapsed += SOUND_MODE_POLL_INTERVAL
            mode = await self._get_sound_mode()
            if mode and mode != previous:
                return mode
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in SOUND_MODE_LIST:
            raise HomeAssistantError(f"Unknown sound mode: {option}")

        async with self._lock:
            _LOGGER.debug("Sound mode requested: %s", option)

            current = await self._get_sound_mode()
            if current is None:
                raise HomeAssistantError(
                    "Could not read current sound mode from the soundbar "
                    "(GetSoundMode failed) - not sending any Harmony command"
                )
            _LOGGER.debug("Current sound mode: %s", current)

            if current == option:
                self._attr_current_option = current
                self.async_write_ha_state()
                return

            for _ in range(SOUND_MODE_MAX_PRESSES):
                _LOGGER.debug("Sending Harmony SoundMode command")
                await self._press_sound_mode_button()

                new_mode = await self._wait_for_mode_change(current)
                if new_mode is None:
                    # No change observed within the step timeout - may have
                    # been a wasted "wake" press, or a dropped IR signal.
                    # Try again rather than assuming failure.
                    continue

                _LOGGER.debug("Sound mode changed: %s -> %s", current, new_mode)
                current = new_mode
                self._attr_current_option = current
                self.async_write_ha_state()

                if current == option:
                    _LOGGER.debug("Sound mode target reached: %s", option)
                    return

            raise HomeAssistantError(
                f"Could not reach sound mode '{option}' after "
                f"{SOUND_MODE_MAX_PRESSES} Harmony presses; soundbar is "
                f"actually on '{current}'"
            )
