"""Notification service for Signal Notifier."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import (
    ATTR_DATA,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_URL, CONF_SENDER, CONF_USERNAME, CONF_PASSWORD, DOMAIN
from .client import async_send_signal_message
from .attachments import async_resolve_attachments

_LOGGER = logging.getLogger(__name__)

async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> SignalNotificationService | None:
    """Get the Signal notification service."""
    if discovery_info is None:
        return None

    # On récupère les données de l'entrée de configuration
    config_entry = hass.config_entries.async_get_entry(discovery_info["entry_id"])
    if config_entry is None:
        return None

    url = config_entry.data[CONF_URL]
    sender = config_entry.data[CONF_SENDER]
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)

    return SignalNotificationService(hass, url, sender, username, password)

class SignalNotificationService(BaseNotificationService):
    """Implementation of a notification service for Signal."""

    def __init__(
        self,
        hass: HomeAssistant,
        url: str,
        sender: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize the service."""
        self._hass = hass
        self._url = url.rstrip("/")
        self._sender = sender
        self._username = username
        self._password = password

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""
        target = kwargs.get("target")
        data = kwargs.get(ATTR_DATA, {}) or {}
        
        # On utilise l'expéditeur global par défaut
        sender = data.get("sender", self._sender)
        notify_self = data.get("notify_self", True)
        text_mode = data.get("text_mode", "styled")

        attachment_entity_id = data.get("attachment_entity_id") or []
        base64_attachments = await async_resolve_attachments(
            self._hass, attachment_entity_id
        )

        await async_send_signal_message(
            url=self._url,
            phone_number=sender,
            message=message,
            recipients=target,
            username=self._username,
            password=self._password,
            notify_self=notify_self,
            text_mode=text_mode,
            base64_attachments=base64_attachments,
        )
