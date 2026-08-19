"""Signal API client."""
from __future__ import annotations

import logging
import aiohttp
from typing import Any

_LOGGER = logging.getLogger(__name__)

async def async_send_signal_message(
    url: str,
    phone_number: str,
    message: str,
    recipients: list[str] | str | None = None,
    username: str | None = None,
    password: str | None = None,
    notify_self: bool = True,
    text_mode: str = "styled",
    base64_attachments: list[str] | None = None,
) -> bool:
    """Send a message via Signal API."""
    url = url.rstrip("/")
    endpoint = f"{url}/v2/send"
    
    # Gestion des destinataires
    if isinstance(recipients, str):
        # Séparés par des points-virgules
        recipient_list = [r.strip() for r in recipients.split(";") if r.strip()]
    elif isinstance(recipients, list):
        recipient_list = recipients
    else:
        recipient_list = [phone_number]

    if not recipient_list:
        recipient_list = [phone_number]

    payload = {
        "message": message,
        "number": phone_number,
        "recipients": recipient_list,
        "notify_self": notify_self,
        "text_mode": text_mode,
    }

    if base64_attachments:
        payload["base64_attachments"] = base64_attachments

    auth = None
    if username and password:
        auth = aiohttp.BasicAuth(username, password)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json=payload, auth=auth) as response:
                if response.status >= 400:
                    text = await response.text()
                    _LOGGER.error(
                        "Error sending Signal message: %s - %s",
                        response.status,
                        text,
                    )
                    return False
                _LOGGER.debug("Signal message sent successfully")
                return True
        except Exception as ex:
            _LOGGER.error("Exception while sending Signal message: %s", ex)
            return False
