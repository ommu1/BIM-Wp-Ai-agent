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


async def start_training_flow(phone: str):
    """Start the training flow"""
    await wa.send_text(phone, "Training flow started")
    session_store.update(phone, stage="training")


async def start_projects_flow(phone: str):
    """Start the projects flow"""
    await wa.send_text(phone, "Projects flow started")
    session_store.update(phone, stage="projects")


async def route_from_main_menu(phone: str, button_id: str, text: str):
    lower = (text or "").lower()

    if button_id == "training" or any(w in lower for w in ["training", "course", "bim", "workshop"]):
        session_store.reset(phone)
        return await start_training_flow(phone)

    if button_id == "projects" or any(w in lower for w in ["project", "architecture", "design"]):
        session_store.reset(phone)
        return await start_projects_flow(phone)

    if button_id == "other" or any(w in lower for w in ["other", "enquiry", "callback", "general"]):
        session_store.reset(phone)
        await wa.send_text(
            phone,
            "Please share your details and our team will call you back:\n\n"
            "_Name, Phone, Email, City/Country, Description_\n\n"
            "*Example:*\n"
            "_Rahul Sharma, 9876543210, rahul@gmail.com, Mumbai India, I want to know about your services_\n\n"
            "_Type *Menu* anytime to go back to main menu._"
        )
        session_store.update(phone, stage="other_enquiry")
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
