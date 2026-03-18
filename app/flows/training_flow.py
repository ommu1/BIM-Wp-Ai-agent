# app/flows/training_flow.py
# Full BIM training enquiry → course selection → detail collection → enrollment → payment

import asyncio
from app.services import whatsapp as wa
from app.services import sheets, ai as ai_svc
from app.config import messages as M
from app.utils.session_store import session_store
from app.utils.logger import logger


# ── STEP 1: Show course list ──────────────────────────────────────────────────
async def start_training_flow(phone: str):
    await wa.send_list(
        phone,
        M.TRAINING_MENU_BODY,
        "📚 View Courses",
        M.TRAINING_MENU_SECTIONS,
        footer_text="bimtrainingandprojects.com",
    )
    session_store.update(phone, stage="training_menu", flow="training")


# ── STEP 2: Handle course selection ──────────────────────────────────────────
async def handle_course_selection(phone: str, list_id: str, text: str):
    lower = (text or "").lower()

    if list_id == "arch_bim" or any(w in lower for w in ["architect", "structure", "interior", "id bim"]):
        await wa.send_buttons(
            phone,
            M.COURSE_ARCH,
            [
                {"id": "brochure",   "label": "Download Brochure"},
                {"id": "enroll_now", "label": "Enroll Now"},
                {"id": "back_main",  "label": "Back to Menu"},
            ]
        )
        session_store.update(phone, stage="collecting_details", sub_flow="arch_bim")

    elif list_id == "mepf_bim" or any(w in lower for w in ["mepf", "mep", "mechanical", "electrical", "plumbing"]):
        await wa.send_text(phone, M.COURSE_MEPF)
        session_store.update(phone, stage="collecting_details", sub_flow="mepf_bim")

    elif list_id == "workshop" or any(w in lower for w in ["workshop", "free", "event"]):
        await wa.send_text(phone, M.COURSE_WORKSHOP)
        session_store.update(phone, stage="collecting_details", sub_flow="workshop")

    elif list_id == "brochure" or any(w in lower for w in ["brochure", "pdf", "download"]):
        await send_brochure(phone)

    elif list_id == "back_main":
        from app.flows.welcome_flow import handle_welcome
        await handle_welcome(phone)

    else:
        await wa.send_text(
            phone,
            "🙏 Please select a course from the list above.\n\n"
            "Or type *Menu* to go back to the main menu."
        )


# ── STEP 3: Collect lead details ─────────────────────────────────────────────
async def handle_details_collection(phone: str, text: str):
    session = session_store.get_or_create(phone)

    # Handle button taps first before extracting details
    lower_text = (text or "").lower()
    if text == "Download Brochure" or "brochure" in lower_text:
        return await send_brochure(phone)
    if text == "Enroll Now" or "enroll" in lower_text:
        return await start_enrollment(phone)
    if text == "Back to Menu" or "back" in lower_text:
        from app.flows.welcome_flow import handle_welcome
        session_store.reset(phone)
        return await handle_welcome(phone)

    
    import re
    new_data = dict(session.data)

    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        new_data["email"] = email_match.group(0)
        text_no_email = text.replace(email_match.group(0), "")
    else:
        text_no_email = text

    # Split by comma or newline to get other fields
    parts = [p.strip() for p in re.split(r'[,\n]', text_no_email) if p.strip()]

    if parts and not new_data.get("name"):
        new_data["name"] = parts[0]
    if len(parts) > 1 and not new_data.get("city"):
        new_data["city"] = parts[1]
    if len(parts) > 2 and not new_data.get("profession"):
        new_data["profession"] = parts[2]
    if len(parts) > 3 and not new_data.get("experience"):
        new_data["experience"] = parts[3]

    # Save full text as backup
    new_data["description"] = text

    has_name  = bool(new_data.get("name"))
    has_email = bool(new_data.get("email"))
    has_city  = bool(new_data.get("city"))

    if has_name and (has_email or has_city):
        # Enough info — log to sheet
        if session.sub_flow == "workshop":
            await asyncio.to_thread(sheets.log_workshop_lead, {
                "phone": phone, **new_data,
            })
        elif session.sub_flow == "mepf_bim":
            await asyncio.to_thread(sheets.log_mepf_lead, {
                "phone": phone, **new_data,
            })
        else:
            await asyncio.to_thread(sheets.log_training_lead, {
                "phone": phone, **new_data,
                "course_interest": "Architecture & Structure",
            })
        await wa.send_buttons(
            phone,
            M.confirm_details_received(new_data["name"]),
            [
                {"id": "enroll_now", "label": "✅ Enroll Now"},
                {"id": "brochure",   "label": "📄 Get Brochure"},
                {"id": "ask_human",  "label": "📞 Talk to Trainer"},
            ],
        )
        session_store.update(phone, stage="post_details")
    else:
        missing = []
        if not has_name:  missing.append("*Name*")
        if not has_email: missing.append("*Email Address*")
        if not has_city:  missing.append("*City & Country*")
        await wa.send_text(phone, f"Almost there! Could you share your {', '.join(missing)} as well? 😊")


# ── STEP 4: Post-details button handling ─────────────────────────────────────
async def handle_post_details(phone: str, button_id: str, text: str):
    lower = (text or "").lower()
    session = session_store.get_or_create(phone)

    if button_id == "enroll_now" or any(w in lower for w in ["enroll", "enrol", "join", "pay", "register"]):
        return await start_enrollment(phone)

    if button_id == "brochure" or "brochure" in lower:
        return await send_brochure(phone)

    if button_id == "ask_human" or any(w in lower for w in ["human", "trainer", "call", "talk"]):
        await wa.send_text(phone, M.human_handoff())
        session_store.update(phone, stage="human_requested", human_mode=True)
        return

    if any(w in lower for w in ["discount", "offer", "price", "reduce", "less"]):
        await wa.send_text(phone,
            "I understand! 😊 I'll pass your request to our trainer.\n\n"
            "_They'll share the best available offer when they call you._ 🙏"
        )
        return

    await wa.send_text(
        phone,
        "Thank you for your message! 🙏\n\n"
        "Our team will get back to you within *2-4 hours*.\n\n"
        "📞 *+91 72178 22883*\n"
        "📧 *askus@bimtrainingandprojects.com*"
    )

# ── ENROLLMENT: Show fee + send QR ───────────────────────────────────────────
async def start_enrollment(phone: str):
    session = session_store.get_or_create(phone)
    config  = await asyncio.to_thread(sheets.get_admin_config)

    course_map = {
        "arch_bim": {
            "name":  "Architecture, Structure & ID BIM",
            "fee":   config.get("arch_fee", "18000"),
            "batch": config.get("arch_batch", "Contact us for next batch"),
        },
        "mepf_bim": {
            "name":  "MEPF BIM Training",
            "fee":   config.get("mepf_fee", "15000"),
            "batch": config.get("mepf_batch", "Contact us for next batch"),
        },
        "workshop": {
            "name":  "BIM Workshop (Free)",
            "fee":   "0",
            "batch": config.get("workshop_date", "Coming soon"),
        },
    }

    course = course_map.get(session.sub_flow or "arch_bim", course_map["arch_bim"])
    name   = session.data.get("name", "there")

    session_store.update(phone, stage="enrollment_qr", enroll_course=course)

    if course["fee"] == "0":
        await wa.send_text(phone,
            f"🎉 *{name}, you're registered for the FREE BIM Workshop!*\n\n"
            f"📅 *Date:* {course['batch']}\n\n"
            "_We'll send the Zoom link to this number before the event._\n\n"
            "You're all set! See you there 🎓"
        )
        await asyncio.to_thread(sheets.log_workshop_lead, {
            "phone": phone, **session.data,
        })
        session_store.update(phone, stage="post_enrollment")
        return

    # Paid course — send details + QR
    await wa.send_text(phone, M.enrollment_confirm(name, course["name"], course["fee"], course["batch"]))
    await wa.send_image(phone, session_store.get_or_create(phone).__class__.__module__ and __import__('app.config.settings', fromlist=['get_settings']).get_settings().upi_qr_image_url, M.qr_caption())
    session_store.update(phone, stage="awaiting_utr", awaiting_utr=True)


# ── UTR Submission ────────────────────────────────────────────────────────────
async def handle_utr_submission(phone: str, text: str):
    session = session_store.get_or_create(phone)
    utr  = ai_svc.extract_utr(text)
    name = session.data.get("name", "Student")

    await asyncio.to_thread(sheets.log_payment, {
        "phone": phone,
        "name":  name,
        "email": session.data.get("email", ""),
        "utr":   utr or "Screenshot/Pending",
        "amount": (session.enroll_course or {}).get("fee", ""),
        "installment": "1",
    })

    if utr:
        await wa.send_text(phone, M.utr_received(name, utr))
    else:
        await wa.send_text(phone,
            "Thank you! 📸 Our team will verify your payment within *2 hours* and send your Student ID.\n\n"
            "_For queries: +91 72178 22883_ 🙏"
        )
    session_store.update(phone, stage="payment_submitted", awaiting_utr=False)


# ── Send Brochure ─────────────────────────────────────────────────────────────
async def send_brochure(phone: str):
    from app.config.settings import get_settings
    s = get_settings()
    pdf_url = s.brochure_pdf_url

    if pdf_url:
        await wa.send_document(
            phone,
            pdf_url,
            "BIM_Training_Brochure.pdf",
            "BIM Training & Projects — Course Brochure\n\nReply ENROLL to register!"
        )
    else:
        config = await asyncio.to_thread(sheets.get_admin_config)
        url = config.get("brochure_url", "https://www.bimtrainingandprojects.com/bimtraining")
        await wa.send_text(phone, f"Course Brochure:\n\n{url}\n\nReply ENROLL to start enrollment")

    session_store.update(phone, stage="post_brochure")