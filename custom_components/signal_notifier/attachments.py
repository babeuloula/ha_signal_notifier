"""Attachment resolution for Signal Notifier."""
from __future__ import annotations

import base64
import logging
import mimetypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

SUPPORTED_DOMAINS = ("camera", "image")


def _build_data_uri(entity_id: str, content: bytes, content_type: str) -> str:
    """Build a signal-cli-rest-api compatible data URI for an attachment."""
    extension = mimetypes.guess_extension(content_type) or ".jpg"
    filename = f"{entity_id.replace('.', '_')}{extension}"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};filename={filename};base64,{encoded}"


async def async_resolve_attachments(
    hass: HomeAssistant, entity_ids: list[str]
) -> list[str]:
    """Resolve camera/image entity_ids into Signal-ready data URIs.

    Best-effort: an entity that fails to resolve (unknown entity, timeout,
    unsupported domain...) is logged and skipped. This function never raises.
    """
    from homeassistant.components import camera, image

    attachments: list[str] = []
    for entity_id in entity_ids:
        domain = entity_id.split(".", 1)[0]
        if domain not in SUPPORTED_DOMAINS:
            _LOGGER.warning(
                "Unsupported attachment entity domain for %s: expected camera or image",
                entity_id,
            )
            continue

        try:
            if domain == "camera":
                fetched = await camera.async_get_image(hass, entity_id)
            else:
                fetched = await image.async_get_image(hass, entity_id)
        except Exception as err:  # noqa: BLE001 - best-effort, any failure is skipped
            _LOGGER.warning("Could not fetch attachment from %s: %s", entity_id, err)
            continue

        attachments.append(
            _build_data_uri(entity_id, fetched.content, fetched.content_type)
        )

    return attachments
