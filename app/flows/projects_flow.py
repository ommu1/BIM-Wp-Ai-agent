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
        session_store.update(phone, stage="collecting_project_details", sub_flow="architecture")

    elif button_id == "bim_project" or any(w in lower for w in ["bim", "modelling", "clash", "coordination"]):
        await wa.send_text(phone, M.PROJECT_BIM_DETAILS)
        session_store.update(phone, stage="collecting_project_details", sub_flow="bim")

    elif button_id == "discuss" or any(w in lower for w in ["discuss", "call", "quote"]):
        await wa.send_text(phone,
            "📞 Sure! Please share:\n\n📝 *Name*\n🌐 *Country & City*\n📧 *Email*\n\n"
            "Our expert will call/WhatsApp you within 4–8 hours 🙏"
        )
        session_store.update(phone, stage="collecting_project_details", sub_flow="discuss")
    else:
        await start_projects_flow(phone)


async def handle_project_details(phone: str, text: str):
    session  = session_store.get_or_create(phone)
    extracted = await ai_svc.extract_contact_details(text)
    new_data  = dict(session.data)

    for field in ["name", "email", "city", "country", "description"]:
        if extracted.get(field):
            new_data[field] = extracted[field]
    if not new_data.get("description") and len(text) > 20:
        new_data["description"] = text

    session_store.update(phone, data=new_data)

    if new_data.get("name") and (new_data.get("email") or new_data.get("city")):
        await asyncio.to_thread(sheets.log_project_lead, {
            "phone": phone, **new_data,
            "project_type": session.sub_flow or "General",
            "source": "WhatsApp Bot",
        })
        await wa.send_buttons(
            phone,
            M.project_received(new_data["name"]),
            [
                {"id": "send_files", "label": "📎 Share Project Files"},
                {"id": "view_work",  "label": "🌐 View Our Work"},
                {"id": "back_main",  "label": "↩ Main Menu"},
            ],
        )
        session_store.update(phone, stage="post_project_details")
    else:
        missing = []
        if not new_data.get("name"):  missing.append("*Name*")
        if not new_data.get("email"): missing.append("*Email*")
        if not new_data.get("city"):  missing.append("*City & Country*")
        await wa.send_text(phone, f"Almost there! Could you share your {', '.join(missing)} as well? 😊")


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
        session = session_store.get_or_create(phone)
        reply = await ai_svc.get_ai_reply(session.history, text)
        session.add_history("user", text)
        session.add_history("assistant", reply)
        await wa.send_text(phone, reply)
