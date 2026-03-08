# app/main.py
# ═══════════════════════════════════════════════════════════════════════════════
#  BIM Training & Projects — WhatsApp AI Agent
#  Python 3.11+ | FastAPI | Meta Cloud API v20.0 | GPT-4o
#  Deploy: Railway.app or Render.com
# ═══════════════════════════════════════════════════════════════════════════════

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from app.config.settings import get_settings
from app.utils.logger import logger
from app.services import mailer, whatsapp as wa
from app.flows.message_handler import handle_incoming_message
from app.jobs.reminders import start_scheduler, schedule_session_reminder, send_seat_filling_alert


# ── App startup / shutdown ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 BIM WhatsApp AI Agent starting up...")
    await mailer.test_smtp()   # Verify Gmail SMTP
    start_scheduler()           # Start cron jobs
    logger.info("✅ All systems ready")
    yield
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="BIM Training WhatsApp AI Agent",
    description="Meta Cloud API v20.0 + GPT-4o",
    version="2.0.0",
    lifespan=lifespan,
)


# ── API Key dependency for admin endpoints ────────────────────────────────────
def require_api_key(x_api_key: str = Query(None, alias="key"),
                    x_api_key_header: Optional[str] = None):
    s = get_settings()
    # Accept via query param or header
    return True  # Simplified — add real auth if needed


# ═══════════════════════════════════════════════════════════════════════════════
#  WEBHOOK VERIFICATION — Meta calls this once to verify your URL
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    s = get_settings()
    if mode == "subscribe" and token == s.verify_token:
        logger.info("✅ Webhook verified by Meta")
        return PlainTextResponse(challenge)

    logger.warning(f"Webhook verification failed | mode={mode} token={token}")
    raise HTTPException(status_code=403, detail="Forbidden")


# ═══════════════════════════════════════════════════════════════════════════════
#  WEBHOOK RECEIVER — All incoming WhatsApp messages arrive here
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/webhook")
async def receive_webhook(request: Request):
    # Always return 200 immediately — Meta retries on failure
    body = await request.json()

    if body.get("object") != "whatsapp_business_account":
        return JSONResponse({"status": "ignored"})

    try:
        entry   = (body.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value   = changes.get("value", {})

        # Ignore status updates (delivery receipts etc.)
        if value.get("statuses"):
            return JSONResponse({"status": "ok"})

        messages = value.get("messages", [])
        for message in messages:
            await process_message(message)

    except Exception as e:
        logger.error(f"Webhook processing error | {e}", exc_info=True)

    return JSONResponse({"status": "ok"})


async def process_message(message: dict):
    phone    = message.get("from", "")
    msg_type = message.get("type", "")
    msg_id   = message.get("id", "")

    # Mark as read (blue ticks)
    await wa.mark_read(msg_id)

    text      = None
    button_id = None
    list_id   = None
    media_id  = None

    if msg_type == "text":
        text = message.get("text", {}).get("body", "").strip()

    elif msg_type == "interactive":
        interactive = message.get("interactive", {})
        itype       = interactive.get("type")

        if itype == "button_reply":
            button_id = interactive["button_reply"]["id"]
            text      = interactive["button_reply"]["title"]

        elif itype == "list_reply":
            list_id = interactive["list_reply"]["id"]
            text    = interactive["list_reply"]["title"]

    elif msg_type == "image":
        media_id = message.get("image", {}).get("id")
        text     = "[IMAGE_RECEIVED]"   # payment screenshot

    elif msg_type == "document":
        media_id = message.get("document", {}).get("id")
        text     = "[DOCUMENT_RECEIVED]"

    elif msg_type == "audio":
        await wa.send_text(phone,
            "🎙️ I received your voice message! I work best with text.\n\n"
            "Please type your question and I'll be happy to help 😊"
        )
        return

    else:
        logger.debug(f"Unhandled message type | type={msg_type} phone={phone}")
        return

    if not any([text, button_id, list_id]):
        return

    await handle_incoming_message(phone, msg_type, text, button_id, list_id, media_id)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN REST API ENDPOINTS
#  (Called from Google Apps Script after payment / certificate events)
# ═══════════════════════════════════════════════════════════════════════════════

class ConfirmPaymentRequest(BaseModel):
    phone: str
    name: str
    email: str = ""
    course: str
    student_id: str
    batch_date: str

@app.post("/api/confirm-payment")
async def confirm_payment(data: ConfirmPaymentRequest):
    """
    Called by Google Apps Script when you change status to "Payment Confirmed" in Sheet.
    Sends Student ID + welcome message to the student.
    """
    from app.config.messages import student_id_welcome
    try:
        phone = data.phone.replace("+", "").replace(" ", "")
        await wa.send_text(phone, student_id_welcome(
            data.name, data.student_id, data.course, data.batch_date
        ))
        if data.email:
            await mailer.send_enrollment_email(
                data.email, data.name, data.course, data.student_id, data.batch_date
            )
        logger.info(f"Payment confirmed + Student ID sent | id={data.student_id}")
        return {"success": True, "student_id": data.student_id}
    except Exception as e:
        logger.error(f"confirm-payment error | {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CertificateRequest(BaseModel):
    phone: str
    name: str
    email: str = ""
    course: str
    student_id: str

@app.post("/api/send-certificate")
async def send_certificate(data: CertificateRequest):
    """
    Called by Google Apps Script when you change status to "Completed" in Sheet.
    Sends certificate congratulations on WhatsApp + emails the certificate.
    """
    from app.config.messages import certificate_ready, REVIEW_BUTTONS
    try:
        phone = data.phone.replace("+", "").replace(" ", "")
        await wa.send_buttons(phone, certificate_ready(data.name, data.course), REVIEW_BUTTONS)
        if data.email:
            await mailer.send_certificate_email(data.email, data.name, data.course, data.student_id)
        logger.info(f"Certificate sent | id={data.student_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"send-certificate error | {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SessionReminderRequest(BaseModel):
    session_datetime: str   # ISO format: "2026-03-15T10:00:00+05:30"
    zoom_link: str
    course_name: str

@app.post("/api/schedule-reminder")
async def schedule_reminder(data: SessionReminderRequest):
    """Schedule a session reminder 30 minutes before class"""
    try:
        dt = datetime.fromisoformat(data.session_datetime)
        ok = schedule_session_reminder(dt, data.zoom_link, data.course_name)
        return {"success": ok, "scheduled_for": data.session_datetime}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BroadcastRequest(BaseModel):
    phones: list[str]
    course: str
    seats_left: int
    last_date: str

@app.post("/api/broadcast-seats")
async def broadcast_seats(data: BroadcastRequest):
    """Send seat-filling alert to a list of phone numbers"""
    await send_seat_filling_alert(data.phones, data.course, data.seats_left, data.last_date)
    return {"success": True, "sent": len(data.phones)}


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    from app.utils.session_store import session_store
    return {
        "status":          "ok",
        "service":         "BIM Training WhatsApp AI Agent",
        "active_sessions": session_store.count(),
        "timestamp":       datetime.now().isoformat(),
    }
