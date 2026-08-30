"""Lennox mDNS discovery helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import CONF_THERMOSTAT_ID

ZEROCONF_SERVICE = "_icomfort4._res._lii._http._tcp.local."
DEFAULT_PORT = 443
_ID_KEYS = ("id", "uuid", "device_id", "deviceId", "thermostat_id", "thermostatId", "sysId", "serial", "serialNumber")


def normalize_hostname(hostname: str) -> str:
    """Normalize a Zeroconf hostname for comparison and storage."""
    return hostname.rstrip(".").lower()


def discovered_host(info: ZeroconfServiceInfo) -> str:
    """Return the durable hostname from a discovery result."""
    return normalize_hostname(info.hostname or info.name.split(".", 1)[0])


def discovered_port(info: ZeroconfServiceInfo) -> int:
    """Return the advertised port, defaulting to Lennox's HTTPS port."""
    return info.port or DEFAULT_PORT


def runtime_target(info: ZeroconfServiceInfo) -> str:
    """Return the address used by the legacy API client for this result."""
    return f"{info.host}:{discovered_port(info)}"


def advertised_identity(info: ZeroconfServiceInfo) -> str | None:
    """Extract a stable thermostat identity from mDNS TXT properties."""
    properties: Mapping[str, Any] = info.properties
    for key in _ID_KEYS:
        value = properties.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def entry_identity(data: Mapping[str, Any]) -> str | None:
    """Return the stable identity stored for a discovered entry."""
    value = data.get(CONF_THERMOSTAT_ID)
    return str(value) if value else None
