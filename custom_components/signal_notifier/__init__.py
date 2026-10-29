"""The Signal Notifier integration."""
from __future__ import annotations

import copy
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.util.yaml import load_yaml_dict

from .const import DOMAIN, CONF_URL, CONF_SENDER, CONF_USERNAME, CONF_PASSWORD
from .client import (
    async_fetch_signal_contacts,
    async_fetch_signal_groups,
    async_send_signal_message,
)
from .attachments import async_resolve_attachments

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NOTIFY]

SERVICE_SEND_MESSAGE = "send_message"

# Fréquence de rafraîchissement des groupes et contacts proposés dans l'UI
REFRESH_INTERVAL = timedelta(minutes=15)


def build_recipient_list(
    groups: list[str] | str | None,
    contacts: list[str] | str | None,
    recipients: list[str] | str | None,
) -> list[str]:
    """Merge groups, contacts and free phone numbers into a single list."""
    result: list[str] = []
    for value in (groups, contacts, recipients):
        if not value:
            continue
        items = value.split(";") if isinstance(value, str) else value
        for item in items:
            item = str(item).strip()
            if item and item not in result:
                result.append(item)
    return result


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Signal Notifier from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    url = entry.data[CONF_URL]
    sender = entry.data[CONF_SENDER]
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)

    async def handle_send_message(call: ServiceCall) -> None:
        """Handle the service call."""
        message = call.data.get("message")
        recipients = build_recipient_list(
            call.data.get("groups"),
            call.data.get("contacts"),
            call.data.get("recipients"),
        )
        notify_self = call.data.get("notify_self", True)
        text_mode = call.data.get("text_mode", "styled")
        attachment_entity_id = call.data.get("attachment_entity_id") or []

        base64_attachments = await async_resolve_attachments(hass, attachment_entity_id)

        await async_send_signal_message(
            url=url,
            phone_number=sender,
            message=message,
            recipients=recipients,
            username=username,
            password=password,
            notify_self=notify_self,
            text_mode=text_mode,
            base64_attachments=base64_attachments,
        )

    hass.services.async_register(DOMAIN, SERVICE_SEND_MESSAGE, handle_send_message)

    services_yaml = await hass.async_add_executor_job(
        load_yaml_dict, str(Path(__file__).parent / "services.yaml")
    )

    async def async_refresh_service_schema(*_: Any) -> None:
        """Inject the Signal groups and contacts in the service UI selectors."""
        try:
            groups = await async_fetch_signal_groups(url, sender, username, password)
            contacts = await async_fetch_signal_contacts(
                url, sender, username, password
            )
        except Exception as ex:  # noqa: BLE001
            _LOGGER.warning("Unable to fetch Signal groups/contacts: %s", ex)
            return

        schema = copy.deepcopy(services_yaml[SERVICE_SEND_MESSAGE])
        schema["fields"]["groups"]["selector"]["select"]["options"] = groups
        schema["fields"]["contacts"]["selector"]["select"]["options"] = contacts
        async_set_service_schema(hass, DOMAIN, SERVICE_SEND_MESSAGE, schema)

    await async_refresh_service_schema()
    entry.async_on_unload(
        async_track_time_interval(hass, async_refresh_service_schema, REFRESH_INTERVAL)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
