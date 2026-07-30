# app/flows/student_flow.py
import re
import asyncio
from app.services import whatsapp as wa
from app.services import sheets, ai as ai_svc, mailer
from app.config import messages as M
from app.utils.session_store import session_store
from app.utils.logger import logger


async def start_student_flow(phone: str):
    await wa.send_text(phone, M.STUDENT_ID_PROMPT)
    session_store.update(phone, stage="awaiting_student_id", flow="student")


async def handle_student_id_input(phone: str, text: str):
    # Match pattern like #BIMP-2026-1234
    match = re.search(r"#?BIMP[-\s]?\d{4}[-\s]?\d{3,4}", text, re.IGNORECASE)
    student_id = None
    if match:
        student_id = match.group(0).upper().replace(" ", "-")
        if not student_id.startswith("#"):
            student_id = "#" + student_id

    if not student_id:
        if any(w in text.lower() for w in ["help", "forgot", "lost", "don't know"]):
            await wa.send_text(phone,
                "No problem! 😊\n\nShare the *phone number or email* you enrolled with "
                "and our team will find your Student ID.\n\nOr contact us at:\n📧 *askus@bimtrainingandprojects.com*"
            )
        else:
            await wa.send_text(phone,
                "⚠️ That doesn't look like a valid Student ID.\n\n"
                "It should look like: *#BIMP-2026-1234*\n\n"
                "_Reply *HELP* if you've forgotten your ID._"
            )
        return

    # Verify in Google Sheet
    result = await asyncio.to_thread(sheets.verify_student, student_id)

    if not result["found"]:
        await wa.send_buttons(phone,
            f"❌ Student ID *{student_id}* not found.\n\nPlease double-check the ID.",
            [
                {"id": "try_again",  "label": "🔄 Try Again"},
                {"id": "contact_us", "label": "📞 Contact Us"},
                {"id": "back_main",  "label": "↩ Main Menu"},
            ]
        )
        return

    config    = await asyncio.to_thread(sheets.get_admin_config)
    zoom_link = config.get(f"zoom_{result['course'].replace(' ','_')}", config.get("zoom_default", "Check your WhatsApp group"))

    session_store.update(phone,
        stage="student_portal",
        is_verified=True,
        student_id=student_id,
        student_data=result,
        zoom_link=zoom_link,
    )

    await wa.send_list(
        phone,
        M.student_menu_body(result["name"]),
        "📋 Student Menu",
        M.STUDENT_MENU_SECTIONS,
        footer_text=f"Student ID: {student_id}",
    )


async def handle_student_menu(phone: str, list_id: str, text: str):
    session = session_store.get_or_create(phone)
    student = session.student_data or {}
    lower   = (text or "").lower()

    if list_id == "zoom_link" or any(w in lower for w in ["zoom", "link", "join"]):
        await _send_zoom(phone, session, student)

    elif list_id == "next_class" or any(w in lower for w in ["next", "schedule", "when", "date"]):
        config = await asyncio.to_thread(sheets.get_admin_config)
        schedule = config.get("class_schedule", "Check your WhatsApp group for the latest schedule.")
        await wa.send_text(phone,
            f"📅 *Upcoming Class Schedule*\n\n{schedule}\n\n"
            "_Zoom link sent 30 minutes before session._"
        )

    elif list_id == "install" or any(w in lower for w in ["install", "revit", "software", "download"]):
        await wa.send_text(phone, M.INSTALL_GUIDE)

    elif list_id == "submit_proj" or any(w in lower for w in ["submit", "project", "assignment"]):
        config = await asyncio.to_thread(sheets.get_admin_config)
        link   = config.get("project_submit_link")
        if link:
            await wa.send_text(phone,
                f"📤 *Submit Your Project*\n\n🔗 {link}\n\n"
                f"_Or email to askus@bimtrainingandprojects.com with subject: Project — {session.student_id}_"
            )
        else:
            await wa.send_text(phone,
                f"📤 *Submit Your Project*\n\nEmail your files to:\n📧 *askus@bimtrainingandprojects.com*\n\n"
                f"Subject: *Project Submission — {session.student_id}*"
            )

    elif list_id == "attendance" or "attendance" in lower:
        att    = student.get("attendance", "Not yet recorded")
        pct    = float(att.replace("%","")) if att and att not in ("","Not yet recorded") else 0
        status = "✅ Eligible for certificate" if pct >= 75 else "⚠️ Below 75% — please attend more sessions"
        await wa.send_text(phone,
            f"📊 *Attendance Record*\n\n"
            f"Student: *{student.get('name')}*\n"
            f"Course: *{student.get('course')}*\n"
            f"Attendance: *{att}*\n{status}\n\n"
            "_Minimum 75% required for certificate._"
        )

    elif list_id == "cert_status" or "certificate" in lower:
        await _handle_cert_status(phone, student)

    elif list_id == "other_help":
        await wa.send_text(phone,
            "Sure! Type your question and I'll help.\n\n"
            "For urgent issues: *askus@bimtrainingandprojects.com*"
        )
        session_store.update(phone, stage="student_freetext")

    else:
        # AI freetext
        reply = await ai_svc.get_ai_reply(session.history, text)
        session.add_history("user", text)
        session.add_history("assistant", reply)
        await wa.send_text(phone, reply)


async def handle_claim_certificate(phone: str):
    session = session_store.get_or_create(phone)
    student = session.student_data or {}

    await wa.send_text(phone,
        f"🎓 *Processing your certificate...*\n\n"
        f"_Sending to: {student.get('email','your registered email')}_\n\n"
        "Check your inbox in a few minutes. 📧"
    )
    if student.get("email"):
        await mailer.send_certificate_email(
            student["email"], student["name"],
            student["course"], student["student_id"]
        )
    await wa.send_buttons(
        phone,
        M.certificate_ready(student.get("name",""), student.get("course","")),
        M.REVIEW_BUTTONS,
    )
    logger.info(f"Certificate dispatched | id={student.get('student_id')} phone={phone}")


async def handle_student_freetext(phone: str, text: str):
    lower = text.lower()
    if any(w in lower for w in ["install", "revit", "software"]):
        return await wa.send_text(phone, M.INSTALL_GUIDE)
    if any(w in lower for w in ["zoom", "link", "join"]):
        session = session_store.get_or_create(phone)
        return await _send_zoom(phone, session, session.student_data or {})
    if "certificate" in lower:
        session = session_store.get_or_create(phone)
        return await _handle_cert_status(phone, session.student_data or {})

    session = session_store.get_or_create(phone)
    reply   = await ai_svc.get_ai_reply(session.history, text)
    session.add_history("user", text)
    session.add_history("assistant", reply)
    await wa.send_text(phone, reply)


async def _send_zoom(phone: str, session, student: dict):
    config    = await asyncio.to_thread(sheets.get_admin_config)
    zoom_link = session.zoom_link or config.get("zoom_default", "Check your WhatsApp group")
    next_time = config.get("next_class_time", "See your WhatsApp group")
    await wa.send_text(phone, M.zoom_link_msg(zoom_link, student.get("course","BIM Training"), next_time))


async def _handle_cert_status(phone: str, student: dict):
    att         = float((student.get("attendance") or "0").replace("%","") or 0)
    project_done = student.get("project_done","").upper() in ("Y","YES","TRUE")
    eligible    = att >= 75 and project_done

    if eligible:
        await wa.send_buttons(phone,
            f"🎓 *Certificate Status*\n\n✅ Attendance: {student.get('attendance')}%\n✅ Project: Submitted\n\n"
            "*You are eligible for your certificate!* 🏆",
            [
                {"id": "claim_cert", "label": "🎓 Claim Certificate"},
                {"id": "back_main",  "label": "↩ Back to Menu"},
            ]
        )
    else:
        issues = []
        if att < 75:      issues.append(f"• Attendance: {student.get('attendance','0%')} (need 75%)")
        if not project_done: issues.append("• Project: Not yet submitted")
        await wa.send_text(phone,
            f"📋 *Certificate Status*\n\nNot yet eligible:\n" + "\n".join(issues) +
            "\n\n_Complete the above requirements to receive your certificate._ "
        )
