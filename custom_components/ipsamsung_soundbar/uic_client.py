from __future__ import annotations

from urllib.parse import quote
import xml.etree.ElementTree as ET

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class UicClient:
    """Minimal client for the Samsung UIC HTTP API (port 56001)."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        self._hass = hass
        self._host = host
        self._port = port

    def _url(self, xml_payload: str) -> str:
        # "/" must stay unescaped in closing tags - the HW-Q960A returns
        # unrelated data when "/" is percent-encoded (e.g. GetFunc misrouted
        # to a VolumeLevel response).
        return f"http://{self._host}:{self._port}/UIC?cmd={quote(xml_payload, safe='/')}"

    async def request(self, xml_payload: str) -> ET.Element | None:
        session = async_get_clientsession(self._hass)
        try:
            async with session.get(self._url(xml_payload), timeout=4) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
                return ET.fromstring(text)
        except (TimeoutError, ClientError, ET.ParseError):
            return None

    async def send(self, xml_payload: str) -> bool:
        root = await self.request(xml_payload)
        if root is None:
            return False
        response = root.find(".//response")
        return response is not None and response.attrib.get("result") == "ok"
