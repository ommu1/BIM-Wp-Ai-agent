# app/main.py
# ═══════════════════════════════════════════════════════════════════════════════
#  BIM Training & Projects — WhatsApp AI Agent
#  Python 3.11+ | FastAPI | Meta Cloud API v20.0 | GPT-4o
#  Deploy: Railway.app or Render.com
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
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
from app.jobs.reminders import start_scheduler, schedule_session_reminder


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

        elif itype == "nfm_reply":
            import json
            nfm_reply = interactive.get("nfm_reply", {})
            response_json_str = nfm_reply.get("response_json", "{}")
            try:
                flow_data = json.loads(response_json_str) if isinstance(response_json_str, str) else response_json_str
            except Exception:
                flow_data = {}

            logger.info(f"Flow submission received | phone={phone} | data={flow_data}")

            # Extract fields — matches your Flow JSON field names
            name       = flow_data.get("full_name", "") or flow_data.get("name", "")
            phone_num  = flow_data.get("phone_number", "") or flow_data.get("phone", "")
            email      = flow_data.get("email", "")
            city       = flow_data.get("city", "")
            profession = flow_data.get("profession", "")
            college    = flow_data.get("college", "")

            # Get session to know which flow/course
            from app.utils.session_store import session_store
            session = session_store.get_or_create(phone)
            sub_flow = session.sub_flow or ""

            try:
                from app.services import sheets

                if sub_flow == "workshop":
                    await asyncio.to_thread(sheets.log_workshop_lead, {
                        "phone": phone,
                        "name": name,
                        "user_phone": phone_num,
                        "email": email,
                        "address": city,
                        "profession": profession,
                        "college": college,
                    })
                elif sub_flow == "mepf_bim":
                    await asyncio.to_thread(sheets.log_mepf_lead, {
                        "phone": phone,
                        "name": name,
                        "user_phone": phone_num,
                        "email": email,
                        "address": city,
                        "profession": profession,
                        "college": college,
                    })

                elif sub_flow == "other_enquiry":
                    await asyncio.to_thread(sheets.log_other_enquiry, {
                "phone": phone,
                "name": name,
                "email": email,
                "address": city,
                "profession": profession,
                "college": college,
            })
                        
                elif sub_flow in ("Design Projects", "BIM Projects"):  
                    await asyncio.to_thread(sheets.log_project_lead, {
                        "phone": phone,
                        "name": name,
                        "email": email,
                        "address": city,
                        "description": f"Profession: {profession} | College: {college}",
                        "project_type": sub_flow,
                    })
                else:
                    # Default — Architecture & Structure
                    await asyncio.to_thread(sheets.log_training_lead, {
                        "phone": phone,
                        "name": name,
                        "user_phone": phone_num,
                        "email": email,
                        "address": city,
                        "profession": profession,
                        "college": college,
                        "course_interest": "Architecture & Structure",
                    })

                logger.info(f"Flow submission saved | phone={phone} sub_flow={sub_flow}")

            except Exception as e:
                logger.error(f"Flow submission sheet error | {e}")

            # Send thank you + action buttons
            from app.services import whatsapp as wa2
            from app.config import messages as M2
            session_store.update(phone,
                stage="post_details",
                data={"name": name, "email": email, "address": city}
            )
            await wa2.send_buttons(
                phone,
                M2.confirm_details_received(name),
                [
                    {"id": "ask_human",  "label": "📞 Talk to Trainer"},
                ],
            )
            return

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



# ── Health check ──────────────────────────────────────────────────────────────
@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    from app.utils.session_store import session_store
    return {
        "status":          "ok",
        "service":         "BIM Training WhatsApp AI Agent",
        "active_sessions": session_store.count(),
        "timestamp":       datetime.now().isoformat(),
    }
