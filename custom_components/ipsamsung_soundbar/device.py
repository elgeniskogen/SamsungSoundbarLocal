from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def soundbar_device_info(host: str, port: int, name: str) -> DeviceInfo:
    """Shared device info so all entities for one soundbar group under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{host}_{port}")},
        name=name,
        manufacturer="Samsung",
        model="HW-Q960A",
    )
