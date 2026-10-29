"""Signal API client."""
from __future__ import annotations

import logging
import aiohttp
from typing import Any

_LOGGER = logging.getLogger(__name__)

def _build_auth(
    username: str | None, password: str | None
) -> aiohttp.BasicAuth | None:
    """Build the Basic Auth object if credentials are provided."""
    if username and password:
        return aiohttp.BasicAuth(username, password)
    return None


async def _async_get_json(
    url: str, username: str | None, password: str | None
) -> list[dict[str, Any]]:
    """GET a JSON list from the Signal API."""
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, auth=_build_auth(username, password)) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
            return data if isinstance(data, list) else []


async def async_fetch_signal_groups(
    url: str,
    phone_number: str,
    username: str | None = None,
    password: str | None = None,
) -> list[dict[str, str]]:
    """Fetch the groups of the account, as select options (value = group id)."""
    groups = await _async_get_json(
        f"{url.rstrip('/')}/v1/groups/{phone_number}", username, password
    )
    options = [
        {"value": group["id"], "label": group.get("name") or group["id"]}
        for group in groups
        if group.get("id") and not group.get("blocked")
    ]
    return sorted(options, key=lambda option: option["label"].lower())


async def async_fetch_signal_contacts(
    url: str,
    phone_number: str,
    username: str | None = None,
    password: str | None = None,
) -> list[dict[str, str]]:
    """Fetch the contacts of the account, as select options (value = number or uuid)."""
    contacts = await _async_get_json(
        f"{url.rstrip('/')}/v1/contacts/{phone_number}", username, password
    )
    options = []
    for contact in contacts:
        if contact.get("blocked"):
            continue
        value = contact.get("number") or contact.get("uuid")
        if not value:
            continue
        name = (
            contact.get("name")
            or contact.get("profile_name")
            or contact.get("given_name")
            or contact.get("username")
        )
        label = f"{name} ({contact['number']})" if name and contact.get("number") else name or value
        options.append({"value": value, "label": label})
    return sorted(options, key=lambda option: option["label"].lower())


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

    # L'API refuse de mélanger groupes et numéros dans une même requête
    groups = [r for r in recipient_list if r.startswith("group.")]
    numbers = [r for r in recipient_list if not r.startswith("group.")]
    batches = [batch for batch in (groups, numbers) if batch]

    success = True
    async with aiohttp.ClientSession() as session:
        for batch in batches:
            payload = {
                "message": message,
                "number": phone_number,
                "recipients": batch,
                "notify_self": notify_self,
                "text_mode": text_mode,
            }

            if base64_attachments:
                payload["base64_attachments"] = base64_attachments

            try:
                async with session.post(
                    endpoint, json=payload, auth=_build_auth(username, password)
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        _LOGGER.error(
                            "Error sending Signal message: %s - %s",
                            response.status,
                            text,
                        )
                        success = False
                        continue
                    _LOGGER.debug("Signal message sent successfully")
            except Exception as ex:
                _LOGGER.error("Exception while sending Signal message: %s", ex)
                success = False

    return success
