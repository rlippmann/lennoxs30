"""Tests for Lennox mDNS discovery and migration."""

from ipaddress import IPv4Address
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_ZEROCONF
from homeassistant.data_entry_flow import FlowResultType
from custom_components.lennoxs30.config_flow import Lennoxs30ConfigFlow
from custom_components.lennoxs30.discovery import (
    ZEROCONF_SERVICE,
    advertised_identity,
    discovered_host,
    discovered_port,
    runtime_target,
)


def service_info(**kwargs):
    values = {
        "type": ZEROCONF_SERVICE,
        "hostname": "Lennox-S40-BT23M54549.local.",
        "name": "Lennox-S40-BT23M54549._icomfort4._res._lii._http._tcp.local.",
        "host": "192.168.1.40",
        "ip_address": IPv4Address("192.168.1.40"),
        "ip_addresses": [IPv4Address("192.168.1.40")],
        "port": 443,
        "properties": {"serialNumber": "BT23M54549"},
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_discovery_preserves_hostname_port_and_identity():
    info = service_info()
    assert discovered_host(info) == "lennox-s40-bt23m54549.local"
    assert discovered_port(info) == 443
    assert runtime_target(info) == "192.168.1.40:443"
    assert advertised_identity(info) == "BT23M54549"


def test_discovery_defaults_port_and_handles_missing_txt():
    info = service_info(port=None, properties={})
    assert discovered_port(info) == 443
    assert advertised_identity(info) is None


def test_discovery_extracts_identity_from_service_instance_name():
    info = service_info(properties={}, name="_BT23M54601_1._icomfort4._res._lii._http._tcp.local.")
    assert advertised_identity(info) == "BT23M54601"


@pytest.mark.asyncio
async def test_zeroconf_existing_ip_entry_migrates_without_duplicate(hass):
    entry = MagicMock()
    entry.unique_id = "existing-entry"
    entry.data = {"cloud_connection": False, "host": "192.168.1.40", "create_sensors": True}
    hass.data["lennoxs30"] = {}
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", return_value=[entry]), patch.object(
        hass.config_entries, "async_update_entry"
    ) as update_entry:
        result = await flow.async_step_zeroconf(service_info())

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    updated = update_entry.call_args.kwargs["data"]
    assert updated["host"] == "lennox-s40-bt23m54549.local"
    assert updated["mdns_port"] == 443
    assert updated["create_sensors"] is True


@pytest.mark.asyncio
async def test_zeroconf_does_not_match_cloud_entry(hass):
    entry = MagicMock()
    entry.unique_id = "cloud-entry"
    entry.data = {"cloud_connection": True, "email": "user@example.com"}
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", return_value=[entry]), patch.object(flow, "async_set_unique_id"), patch.object(
        flow, "_abort_if_unique_id_configured"
    ):
        result = await flow.async_step_zeroconf(service_info(properties={"id": "thermostat-1"}))

    assert result["type"] == "form"
    assert result["step_id"] == "advanced"
    assert flow.config_input["host"] == "lennox-s40-bt23m54549.local"
    assert flow.config_input["thermostat_id"] == "thermostat-1"


@pytest.mark.asyncio
async def test_zeroconf_full_home_assistant_flow(hass):
    with patch("custom_components.lennoxs30.async_setup_entry", new=AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_init(
            "lennoxs30", context={"source": SOURCE_ZEROCONF}, data=service_info(properties={"id": "thermostat-1"})
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "advanced"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "scan_interval": 1,
                "fast_scan_interval": 0.75,
                "fast_scan_count": 10,
                "init_wait_time": 30,
                "timeout": 30,
                "pii_in_message_logs": False,
                "message_debug_logging": True,
                "log_messages_to_file": False,
                "message_debug_file": "",
            },
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "lennox-s40-bt23m54549.local"
    assert result["data"]["mdns_port"] == 443


@pytest.mark.asyncio
async def test_zeroconf_new_ip_uses_api_identity_to_migrate(hass):
    entry = MagicMock()
    entry.unique_id = "existing-entry"
    entry.data = {"cloud_connection": False, "host": "192.168.1.40", "thermostat_id": "thermostat-1", "keep": "me"}
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", return_value=[entry]), patch.object(
        flow, "_probe_discovered_identity", return_value="thermostat-1"
    ) as probe, patch.object(hass.config_entries, "async_update_entry") as update_entry:
        result = await flow.async_step_zeroconf(service_info(host="192.168.1.61", properties={}))

    assert result["reason"] == "already_configured"
    probe.assert_awaited_once()
    updated = update_entry.call_args.kwargs["data"]
    assert updated["host"] == "lennox-s40-bt23m54549.local"
    assert updated["thermostat_id"] == "thermostat-1"
    assert updated["keep"] == "me"


@pytest.mark.asyncio
async def test_zeroconf_probe_failure_keeps_discovery_available(hass):
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", return_value=[]), patch.object(
        flow, "_probe_discovered_identity", return_value=None
    ) as probe, patch.object(flow, "async_set_unique_id"), patch.object(flow, "_abort_if_unique_id_configured"):
        result = await flow.async_step_zeroconf(service_info(properties={}))

    assert result["type"] == "form"
    assert result["step_id"] == "advanced"
    assert flow.config_input["host"] == "lennox-s40-bt23m54549.local"
    assert "thermostat_id" not in flow.config_input
    probe.assert_awaited_once()


@pytest.mark.asyncio
async def test_zeroconf_rediscovery_updates_loaded_manager(hass):
    entry = MagicMock()
    entry.unique_id = "existing-entry"
    entry.data = {"cloud_connection": False, "host": "lennox-s40.local", "thermostat_id": "thermostat-1"}
    manager = MagicMock()
    hass.data["lennoxs30"] = {"existing-entry": {"manager": manager}}
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", return_value=[entry]), patch.object(hass.config_entries, "async_update_entry"):
        result = await flow.async_step_zeroconf(
            service_info(host="192.168.1.61", hostname="Lennox-S40.local.", properties={"id": "thermostat-1"})
        )

    assert result["reason"] == "already_configured"
    manager.async_update_connection_target.assert_called_once_with("lennox-s40.local", "192.168.1.61", 443)


@pytest.mark.asyncio
async def test_zeroconf_matches_existing_device_registry_identity(hass):
    entry = MagicMock()
    entry.entry_id = "existing-entry-id"
    entry.unique_id = "lennoxs30_192.168.1.250"
    entry.data = {"cloud_connection": False, "host": "192.168.1.250"}
    hass.data["lennoxs30"] = {}
    registry = SimpleNamespace(
        devices={
            "device": SimpleNamespace(
                config_entries={entry.entry_id},
                identifiers={("lennoxs30", "BT23M54601")},
            )
        }
    )
    assert (
        advertised_identity(
            service_info(
                name="_BT23M54601_1._icomfort4._res._lii._http._tcp.local.",
                properties={},
            )
        )
        == "BT23M54601"
    )
    flow = Lennoxs30ConfigFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", return_value=[entry]), patch.object(
        hass.config_entries, "async_update_entry"
    ) as update_entry, patch("custom_components.lennoxs30.config_flow.dr.async_get", return_value=registry):
        result = await flow.async_step_zeroconf(
            service_info(
                host="192.168.1.198",
                hostname="Lennox-S40-BT23M54601.local.",
                name="_BT23M54601_1._icomfort4._res._lii._http._tcp.local.",
                properties={},
            )
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert update_entry.call_args.kwargs["data"]["host"] == "lennox-s40-bt23m54601.local"


def test_manager_target_update_replaces_stale_runtime_ip(manager):
    manager.api.isLANConnection = True
    manager.async_update_connection_target("lennox-s40-bt23m54601.local", "192.168.1.61", 443)
    assert manager._ip_address == "lennox-s40-bt23m54601.local:443"
    assert manager._resolved_ip == "192.168.1.61"
    assert manager.api.ip == "192.168.1.61:443"
    assert manager._reinitialize is True


def test_manager_target_update_does_not_change_cloud_manager(manager):
    manager.api.isLANConnection = False
    manager.api.ip = None
    manager.async_update_connection_target("lennox-s40.local", "192.168.1.10", 443)
    assert manager.api.ip is None
