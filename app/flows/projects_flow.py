# app/flows/projects_flow.py
import asyncio
from app.services import whatsapp as wa
from app.services import sheets, ai as ai_svc
from app.config import messages as M
from app.utils.session_store import session_store


async def start_projects_flow(phone: str):
    await wa.send_buttons(
        phone,
        M.PROJECT_MENU_BODY,
        M.PROJECT_MENU_BUTTONS,
    )
    session_store.update(phone, stage="projects_menu", flow="projects")

async def handle_project_selection(phone: str, button_id: str, text: str):
    lower = (text or "").lower()

    if button_id == "arch_project" or any(w in lower for w in ["architect", "interior", "design"]):
        await wa.send_text(phone, M.PROJECT_ARCH_DETAILS)
        session_store.update(phone, stage="collecting_project_details", sub_flow="Design Projects")

    elif button_id == "bim_project" or any(w in lower for w in ["bim", "modelling", "clash", "coordination"]):
        await wa.send_text(phone, M.PROJECT_BIM_DETAILS)
        session_store.update(phone, stage="collecting_project_details", sub_flow="BIM Projects")

    else:
        await start_projects_flow(phone)


async def handle_project_details(phone: str, text: str):
    import re
    session = session_store.get_or_create(phone)
    new_data = dict(session.data)

    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text or "")
    if email_match:
        new_data["email"] = email_match.group(0)
        text_clean = (text or "").replace(email_match.group(0), "")
    else:
        text_clean = text or ""

    # Extract phone
    phone_match = re.search(r'\b\d{10}\b', text_clean)
    if phone_match:
        new_data["user_phone"] = phone_match.group(0)
        text_clean = text_clean.replace(phone_match.group(0), "")

    # Split by comma — positional assignment
    parts = [p.strip() for p in text_clean.split(",") if p.strip()]

    if len(parts) >= 1 and not new_data.get("name"):
        new_data["name"] = parts[0]
    if len(parts) >= 2 and not new_data.get("address"):
        new_data["address"] = parts[1]
    if len(parts) > 2:
        new_data["description"] = ", ".join(parts[2:])
    elif len(text or "") > 20 and not new_data.get("description"):
        new_data["description"] = text

    session_store.update(phone, data=new_data)

    has_name    = bool(new_data.get("name"))
    has_email   = bool(new_data.get("email"))
    has_address = bool(new_data.get("address"))

    if has_name and (has_email or has_address):
        await asyncio.to_thread(sheets.log_project_lead, {
            "phone":       phone,
            "name":        new_data.get("name", ""),
            "email":       new_data.get("email", ""),
            "address":     new_data.get("address", ""),
            "description": new_data.get("description", ""),
            "project_type": session.sub_flow or "General",
        })
        await wa.send_buttons(
            phone,
            M.project_received(new_data["name"]),
            [
                {"id": "send_files", "label": "Share Project Files"},
                {"id": "view_work",  "label": "View Our Work"},
                {"id": "back_main",  "label": "Main Menu"},
            ],
        )
        session_store.update(phone, stage="post_project_details")
    else:
        await wa.send_text(
            phone,
            "Please share your details in this format:\n\n"
            "_Name, Phone, Email, City/Country, Project Description_\n\n"
            "*Example:*\n"
            "_Rahul Sharma, 9876543210, rahul@gmail.com, Mumbai India, I want to learn Interior Design_"
        )


async def handle_post_project(phone: str, button_id: str, text: str):
    from app.config.settings import get_settings
    lower = (text or "").lower()
    s = get_settings()

    if button_id == "send_files" or any(w in lower for w in ["file", "drawing", "attach"]):
        await wa.send_text(phone,
            f"📎 *Share Project Files*\n\nEmail your drawings to:\n📧 *askus@bimtrainingandprojects.com*\n\n"
            "_Mention your name and project type in the subject._ 🙏"
        )
    elif button_id == "view_work" or any(w in lower for w in ["portfolio", "sample", "work"]):
        await wa.send_text(phone, f"🌐 *Our Portfolio*\n\n{s.website_url}\n\n_100+ projects delivered_ 🏗️")
    elif button_id == "back_main":
        from app.flows.welcome_flow import handle_welcome
        await handle_welcome(phone)
    else:
        await wa.send_text(
            phone,
            "Thank you for reaching out! 🙏\n\n"
            "Our team will contact you within *few hours*.\n\n"
            "📞 *+91 72178 22883*\n"
            "📧 *askus@bimtrainingandprojects.com*"
        )