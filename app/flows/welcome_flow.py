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
    """Route user to the correct flow based on their selection"""
    lower = (text or "").lower()

    if button_id == "training" or any(w in lower for w in ["training", "course", "bim", "revit", "mepf", "workshop", "learn"]):
        from app.flows.training_flow import start_training_flow
        return await start_training_flow(phone)

    if button_id == "projects" or any(w in lower for w in ["project", "architecture", "interior", "design", "outsource"]):
        from app.flows.projects_flow import start_projects_flow
        return await start_projects_flow(phone)

    if button_id == "student" or any(w in lower for w in ["student", "enrolled", "existing", "portal", "my id"]):
        from app.flows.student_flow import start_student_flow
        return await start_student_flow(phone)
    
    if button_id == "other" or any(w in lower for w in ["other", "enquiry", "callback", "general"]):
        await wa.send_text(
            phone,
            "Please share your details and our team will call you back:\n\n"
             "*Format:*\n"
            "_Name, Phone, Email, City/Country, Description_\n\n"
            "*Example:*\n"
            "_Rahul Sharma, 9876543210, rahul@gmail.com, Mumbai India, I want to know about your services_\n\n"
            
            "_Type *Menu* anytime to go back to main menu._"
        )
        session_store.update(phone, stage="other_enquiry")
        return

    if any(w in lower for w in ["human", "call me", "talk to", "speak", "person", "agent"]):
        await wa.send_text(phone, M.human_handoff())
        session_store.update(phone, stage="human_requested", human_mode=True)
        return
    
    # fallback
    await wa.send_text(phone,
        "⚠️ Please select one of the options above.\n\n"
        "Type *Menu* to see the main menu again."
    )

    # Default — show welcome again
    await handle_welcome(phone)
