"""The Signal Notifier integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, CONF_URL, CONF_SENDER, CONF_USERNAME, CONF_PASSWORD
from .client import async_send_signal_message
from .attachments import async_resolve_attachments

PLATFORMS: list[Platform] = [Platform.NOTIFY]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Signal Notifier from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    async def handle_send_message(call: ServiceCall) -> None:
        """Handle the service call."""
        url = entry.data[CONF_URL]
        sender = entry.data[CONF_SENDER]
        username = entry.data.get(CONF_USERNAME)
        password = entry.data.get(CONF_PASSWORD)
        
        message = call.data.get("message")
        recipients = call.data.get("recipients")
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

    hass.services.async_register(DOMAIN, "send_message", handle_send_message)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
