# app/flows/message_handler.py
# Central router — every incoming WhatsApp message passes through here

import asyncio
from app.services import whatsapp as wa
from app.services import ai as ai_svc
from app.config import messages as M
from app.config.settings import get_settings
from app.utils.session_store import session_store
from app.utils.logger import logger

from app.flows.welcome_flow  import handle_welcome, route_from_main_menu
from app.flows.training_flow import (
    start_training_flow, handle_course_selection,
    handle_details_collection, handle_post_details,
    start_enrollment, handle_utr_submission, send_brochure,
)
from app.flows.projects_flow import (
    start_projects_flow, handle_project_selection,
    handle_project_details, handle_post_project,
)
from app.flows.student_flow import (
    start_student_flow, handle_student_id_input,
    handle_student_menu, handle_claim_certificate,
    handle_student_freetext,
)


async def handle_incoming_message(
    phone: str,
    msg_type: str,
    text: str | None,
    button_id: str | None,
    list_id: str | None,
    media_id: str | None,
):
    logger.info(f"MSG | phone={phone} type={msg_type} text={str(text)[:60]} btn={button_id} list={list_id}")

    s   = get_settings()
    session = session_store.get_or_create(phone)

    # ── ADMIN COMMANDS from your phone ────────────────────────────────────────
    if phone == s.admin_phone and text and text.startswith("ADMIN:"):
        return await handle_admin_command(phone, text)

    # ── HUMAN MODE: bot is paused for this contact ─────────────────────────
    if session.human_mode:
        logger.info(f"Human mode active — silent | phone={phone}")
        return

    lower = (text or "").lower().strip()

    # ── GLOBAL KEYWORDS ────────────────────────────────────────────────────
    if lower in ("hi", "hello", "start", "menu",  "hey", ""):
        return await handle_welcome(phone)

    if session.stage == "start":
        if lower in ("hi", "hello", "start", "menu", "bim", "hey", ""):
            return await handle_welcome(phone)
        if any(w in lower for w in ["train", "course", "revit", "mepf", "learn"]):
            return await start_training_flow(phone)
        if any(w in lower for w in ["project", "architecture", "interior", "design"]):
            from app.flows.projects_flow import start_projects_flow
            return await start_projects_flow(phone)
        if any(w in lower for w in ["student", "existing", "portal"]):
            from app.flows.student_flow import start_student_flow
            return await start_student_flow(phone)
        # Random text from new user
        return await wa.send_text(
            phone,
            "To get started please type:\n\n"
           "• *Hi* or *Menu* — Main menu\n"
            "• *BIM* — Course information\n"
            "• *Projects* — Project enquiries\n"
            "• *Student* — Existing student portal\n"
            "• *Help* — Talk to our team"
        )

    if lower in ("hi", "hello", "start", "menu", "bim", "hey", ""):
        return await handle_welcome(phone)
    
        

    if lower in ("restart", "reset", "main menu", "back to menu"):
        session_store.reset(phone)
        return await handle_welcome(phone)

    if lower == "install":
        return await wa.send_text(phone, M.INSTALL_GUIDE)

    if lower in ("help", "support", "?"):
        return await wa.send_text(phone,
            f"🆘 *Need help?*\n\n"
            f"Our team is here to assist you! You can reach us at:\n\n"
            f"📧 *askus@bimtrainingandprojects.com*\n"
            f"🌐 *{s.website_url}*\n\n"
            "_Type *MENU* to go back to the main menu._"
        )

    if lower in (
        "human", "agent", "call me", "talk to someone",
        "i want to talk to someone", "need help",
        "contact", "speak to someone", "talk to human"
    ):
        user_name   = session.data.get("name", "Not collected yet")
        user_course = session.data.get("course_interest", "Not specified")
        await wa.send_text(
            phone,
            "✅ *Noted! Our team has been notified.*\n\n"
            "Someone from BIM Training & Projects will contact you "
            "on this number personally.\n\n"
            
        )
        await wa.send_text(
            s.admin_phone,
            f"🔔 *HELP REQUESTED*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {user_name}\n"
            f"📱 Number: +{phone}\n"
            f"💬 Said: \"{text}\"\n"
            f"🎓 Course: {user_course}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"If busy, reply: *ADMIN: BUSY +{phone}*"
        )
        session_store.update(phone, stage="human_requested")
        return

    # ── STAGE ROUTER ───────────────────────────────────────────────────────
    stage = session.stage

    if stage == "main_menu":
        return await route_from_main_menu(phone, button_id or list_id or "", text or "")
    
    if stage == "other_enquiry":
        import re
        name = ""
        phone_num = ""
        email = ""
        address = ""
        description = ""

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text or "")
        if email_match:
            email = email_match.group(0)
            text_clean = (text or "").replace(email_match.group(0), "")
        else:
            text_clean = text or ""

        phone_match = re.search(r'\b\d{10,11}\b', text_clean)
        if phone_match:
            phone_num = phone_match.group(0)
            text_clean = text_clean.replace(phone_match.group(0), "")

        parts = [p.strip() for p in text_clean.split(",") if p.strip()]
        if len(parts) >= 1:
            name = parts[0]
        if len(parts) >= 2:
            address = parts[1]
        if len(parts) > 2:
            description = ", ".join(parts[2:])
        else:
            description = ""

        from app.services import sheets
        await asyncio.to_thread(sheets.log_other_enquiry, {
            "phone":       phone,
            "name":        name,
            "email":       email,
            "address":     address,
            "description": description,
        })

    

        await wa.send_text(
            phone,
            f"*Thank you{', ' + name if name else ''}!* ✅\n\n"
            "Your details have been noted. Our team will call you back.\n\n"
            "📧 *askus@bimtrainingandprojects.com*"
        )
        session_store.update(phone, stage="main_menu")
        return

    # Training
    if stage == "training_check":
        if button_id == "existing_yes" or "yes" in lower:
            from app.flows.student_flow import start_student_flow
            return await start_student_flow(phone)
        else:
            from app.flows.training_flow import start_training_flow
            await wa.send_list(
                phone,
                M.TRAINING_MENU_BODY,
                "📚 View Courses",
                M.TRAINING_MENU_SECTIONS,
                footer_text="bimtrainingandprojects.com",
            )
            session_store.update(phone, stage="training_menu", flow="training")
            return

    if stage == "training_menu":
        return await handle_course_selection(phone, list_id or button_id or "", text or "")

    if stage == "collecting_details":
        return await handle_details_collection(phone, text or "")
    if stage == "post_details":
        return await handle_post_details(phone, button_id or "", text or "")
    if stage == "enrollment_qr":
        return await start_enrollment(phone)
    if stage == "awaiting_utr":
        return await handle_utr_submission(phone, text or "")
    if stage == "payment_submitted":
        return await wa.send_text(phone,
            "⏳ *Payment verification in progress.*\n\n"
            "You'll receive your Student ID once confirmed.\n\n"
            "Questions?  Reply *HELP* or contact us at:\n\n"
        )

    # Projects
    if stage == "projects_menu":
        return await handle_project_selection(phone, button_id or list_id or "", text or "")
    if stage == "collecting_project_details":
        return await handle_project_details(phone, text or "")
    if stage == "post_project_details":
        return await handle_post_project(phone, button_id or "", text or "")

    # Student Portal
    if stage == "awaiting_student_id":
        return await handle_student_id_input(phone, text or "")
    if stage == "student_portal":
        return await handle_student_menu(phone, list_id or button_id or "", text or "")
    if stage == "student_freetext":
        return await handle_student_freetext(phone, text or "")

    # Human requested
    if stage == "human_requested":
        return await wa.send_text(phone,
            "_Our team has been notified and will reach out._ \n\nUrgent: *+*"
        )

    # ── CROSS-FLOW BUTTON IDs ──────────────────────────────────────────────
    return await handle_cross_flow(phone, button_id or list_id or "", text or "", session)


async def handle_cross_flow(phone: str, btn: str, text: str, session):
    lower = text.lower()

    btn_map = {
        "enroll_now":       lambda: start_enrollment(phone),
        "brochure":         lambda: send_brochure(phone),
        "back_main":        lambda: handle_welcome(phone),
        "claim_cert":       lambda: handle_claim_certificate(phone),
        "try_again":        lambda: start_student_flow(phone),
        "review_google":    lambda: wa.send_text(phone, "⭐ *Leave a Google Review:*\nhttps://g.page/r/YOUR_LINK\n\nThank you!"),
        "review_linkedin":  lambda: wa.send_text(phone, "💼 *Connect on LinkedIn:*\nhttps://linkedin.com/company/bim-training-and-projects\n\nThank you!"),
        "review_skip":      lambda: wa.send_text(phone, "No problem! Feel free to reach out anytime.") ,
        "paid_utr":         lambda: handle_utr_submission(phone, text),
        "contact_us":       lambda: wa.send_text(phone, f" *Contact Us*\n\n+\naskus@bimtrainingandprojects.com"),
        "ask_human":        None,  # handled below
    }

    if btn in btn_map and btn_map[btn]:
        return await btn_map[btn]()

    if btn == "ask_human" or any(w in lower for w in ["human", "trainer", "call", "speak"]):
        await wa.send_text(phone, M.human_handoff())
        session_store.update(phone, stage="human_requested", human_mode=True)
        return

    if any(w in lower for w in ["enroll", "enrol"]):
        return await start_enrollment(phone)
    if "brochure" in lower:
        return await send_brochure(phone)

    # AI intent classification
    lower = text.lower()
    if any(w in lower for w in ["train", "course", "bim", "revit", "mepf", "learn"]):
        return await start_training_flow(phone)
    if any(w in lower for w in ["project", "architecture", "interior", "design"]):
        return await start_projects_flow(phone)
    if any(w in lower for w in ["student", "existing", "portal", "my id"]):
        return await start_student_flow(phone)
    if any(w in lower for w in ["hi", "hello", "hey", "start"]):
        return await handle_welcome(phone)
       
# Instead of calling ai_svc, we send a helpful default message
    
    await wa.send_text(
        phone,
        "*Not sure what you mean!*\n\n"
        "Please type one of these to get started:\n\n"
        "• *Hi* — Main menu\n"
        "• *BIM* — Course information\n"
        "• *Projects* — Project enquiries\n"
        "• *Student* — Existing student portal\n"
        "• *Help* — Talk to our team"
    )

# ── ADMIN COMMANDS ─────────────────────────────────────────────────────────
async def handle_admin_command(phone: str, text: str):
    import re
    cmd = text.replace("ADMIN:", "").strip()
    logger.info(f"Admin command | cmd={cmd}")

    pause_match = re.match(r"PAUSE\s+(\+?\d+)", cmd, re.IGNORECASE)
    resume_match = re.match(r"RESUME\s+(\+?\d+)", cmd, re.IGNORECASE)

    if pause_match:
        target = pause_match.group(1).replace("+", "")
        session_store.update(target, human_mode=True)
        await wa.send_text(phone, f"✅ Bot paused for {target}")

    elif resume_match:
        target = resume_match.group(1).replace("+", "")
        session_store.update(target, human_mode=False)
        await wa.send_text(phone, f"✅ Bot resumed for {target}")

    elif cmd.upper() == "STATUS":
        count = session_store.count()
        from datetime import datetime
        await wa.send_text(phone,
            f"📊 *Bot Status*\nActive sessions: {count}\nServer: Running ✅\n"
            f"Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}"
        )

    elif cmd.upper() == "SESSIONS":
        all_s = session_store.all_active()
        lines = [f"{s['phone']}: {s['stage']} ({s['flow']})" for s in all_s[:10]]
        await wa.send_text(phone, "📋 *Active Sessions:*\n" + ("\n".join(lines) or "None"))

    elif cmd.upper().startswith("CLEANUP"):
        removed = session_store.cleanup_expired()
        await wa.send_text(phone, f"🧹 Cleaned {removed} expired sessions")

    else:
        await wa.send_text(phone,
            "❓ Admin commands:\n"
            "• ADMIN: STATUS\n"
            "• ADMIN: SESSIONS\n"
            "• ADMIN: CLEANUP\n"
            "• ADMIN: PAUSE +91XXXXXXXXXX\n"
            "• ADMIN: RESUME +91XXXXXXXXXX"
        )
