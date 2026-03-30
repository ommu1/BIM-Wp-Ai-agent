# app/services/whatsapp.py
# All WhatsApp Cloud API v20.0 message sending functions

import httpx
from typing import List, Dict, Optional
from app.config.settings import get_settings
from app.config.messages import MENU_HINT
from app.utils.logger import logger

def _get_base() -> tuple[str, dict]:
    s = get_settings()
    url = f"https://graph.facebook.com/v20.0/{s.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {s.whatsapp_token}",
        "Content-Type": "application/json",
    }
    return url, headers


async def _send(payload: dict) -> dict:
    url, headers = _get_base()
    payload["messaging_product"] = "whatsapp"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            logger.debug(f"WA sent | to={payload.get('to')} type={payload.get('type')}")
            return res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WA send failed | {e.response.status_code} | {e.response.text[:300]}")
            raise
        except Exception as e:
            logger.error(f"WA send error | {str(e)}")
            raise


def _ensure_menu_hint(text: str) -> str:
    if "Type *Menu* anytime" in text:
        return text
    return text.rstrip() + MENU_HINT


# ── 1. Plain text ─────────────────────────────────────────────────────────────
async def send_text(to: str, text: str) -> dict:
    return await _send({
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": _ensure_menu_hint(text)}
    })


# ── 2. Quick-Reply Buttons (max 3) ─────────────────────────────────────────────────────────────────────────────────────
# ── 2. Quick-Reply Buttons (max 3) ────────────────────────────────────────────
async def send_buttons(
    to: str,
    body_text: str,
    buttons: List[Dict],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> dict:
    body_text = _ensure_menu_hint(body_text)
    interactive = {
        "type": "button",
        "body": {"text": body_text},
        "action": {
            "buttons": [
                # FIX: Using "title" instead of "text" for Meta Cloud API v20.0
                {"type": "reply", "reply": {"id": b["id"], "title": b["label"][:20]}}
                for b in buttons[:3]
            ]
        }
    }
    
    # Add optional components if they exist
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive["footer"] = {"text": footer_text}

    return await _send({"to": to, "type": "interactive", "interactive": interactive})
    
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text}
    if footer_text:
        interactive["footer"] = {"text": footer_text}

    return await _send({"to": to, "type": "interactive", "interactive": interactive})


# ── 3. List Message — scrollable bottom sheet (max 10 items) ──────────────────
async def send_list(
    to: str,
    body_text: str,
    button_label: str,
    sections: List[Dict],
    footer_text: Optional[str] = None,
) -> dict:
    body_text = _ensure_menu_hint(body_text)
    interactive = {
        "type": "list",
        "body": {"text": body_text},
        "action": {
            "button": button_label[:20],
            "sections": [
                {
                    "title": sec.get("title", ""),
                    "rows": [
                        {
                            "id": row["id"],
                            "title": row["title"][:24],
                            "description": row.get("description", "")[:72],
                        }
                        for row in sec["rows"]
                    ]
                }
                for sec in sections
            ]
        }
    }
    if footer_text:
        interactive["footer"] = {"text": footer_text}

    return await _send({"to": to, "type": "interactive", "interactive": interactive})


# ── 4. Image (QR code, etc.) ──────────────────────────────────────────────────
async def send_image(to: str, image_url: str, caption: str = "") -> dict:
    return await _send({
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption}
    })


# ── 5. Document (PDF brochure, certificate) ───────────────────────────────────
async def send_document(to: str, doc_url: str, filename: str, caption: str = "") -> dict:
    return await _send({
        "to": to,
        "type": "document",
        "document": {"link": doc_url, "filename": filename, "caption": caption}
    })


# ── 6. Template Message (proactive / broadcast) ───────────────────────────────
async def send_template(
    to: str,
    template_name: str,
    language_code: str = "en",
    components: Optional[List] = None,
) -> dict:
    return await _send({
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": components or [],
        }
    })


# ── 7. Mark message as read (blue ticks) ─────────────────────────────────────
async def mark_read(message_id: str):
    url, headers = _get_base()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            }, headers=headers)
    except Exception:
        pass  # Non-critical
