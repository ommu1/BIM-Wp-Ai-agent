# app/flows/welcome_flow.py
from app.services import whatsapp as wa
from app.config import messages as M
from app.utils.session_store import session_store
from app.utils.logger import logger


async def handle_welcome(phone: str):
    """Send greeting with 3 quick-reply buttons"""
    await wa.send_buttons(
        phone,
        M.GREETING,
        M.GREETING_BUTTONS,
    )
    session_store.update(phone, stage="main_menu")
    logger.info(f"Welcome sent | phone={phone}")


async def route_from_main_menu(phone: str, button_id: str, text: str):
    lower = (text or "").lower()

    if button_id == "training" or any(w in lower for w in ["training", "course", "bim", "workshop", "learn"]):
        from app.flows.training_flow import start_training_flow
        return await start_training_flow(phone)

    if button_id == "projects" or any(w in lower for w in ["project", "architecture", "design", "interior"]):
        from app.flows.projects_flow import start_projects_flow
        return await start_projects_flow(phone)

    if button_id == "student" or any(w in lower for w in ["student", "enrolled", "existing", "portal", "my id"]):
        from app.flows.student_flow import start_student_flow
        return await start_student_flow(phone)

    if button_id == "other" or any(w in lower for w in ["other", "enquiry", "callback", "general"]):
        from app.config.settings import get_settings
        import uuid
        s = get_settings()
        session_store.reset(phone)
        await wa.send_text(
            phone,
            "Please share your details and our team will call you back.\n\n"
            "_Type *Menu* anytime to go back to main menu._"
        )
        await wa.send_flow(
            phone,
            flow_id=s.flow_id_enquiry,
            flow_token=str(uuid.uuid4()),
            body_text="Tap below to fill in your details:"
        )
        session_store.update(phone, stage="other_enquiry", sub_flow="other_enquiry")
        return

    if any(w in lower for w in ["human", "call me", "talk to", "speak", "person", "agent", "help"]):
        await wa.send_text(phone, M.human_handoff())
        session_store.update(phone, stage="human_requested", human_mode=True)
        return

    # Fallback for anything else
    await wa.send_text(
        phone,
        "⚠️ Please select one of the options above.\n\n"
        "Type *Menu* to see the main menu again.\n"
        "Type *Help* to talk to our team."
    )
