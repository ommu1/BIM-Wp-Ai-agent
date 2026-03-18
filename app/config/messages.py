# app/config/messages.py
# All bot message templates — edit here to change what the bot says

import os
from app.config.settings import get_settings

def cfg():
    return get_settings()

# ── WELCOME ──────────────────────────────────────────────────────────────────
GREETING = """ *Namaste! Welcome to BIM Training & Projects!* 

We specialize in:
- BIM Training 
- Projects
- Others 

Please visit our website for more information:
www.bimtrainingandprojects.com


*How can I help you today?*"""

GREETING_BUTTONS = [
    {"id": "training",  "label": "🎓 BIM Training / Workshop"},
    {"id": "projects",  "label": "🏗️ Architecture / BIM Project"},
    {"id": "student",   "label": "📋 Existing Student"},
]

# ── TRAINING ──────────────────────────────────────────────────────────────────
TRAINING_MENU_BODY = "🎓 *BIM Training — Our Courses*\n\nPlease select a course to know more:"

TRAINING_MENU_SECTIONS = [
    {
        "title": "BIM Courses",
        "rows": [
            {"id": "arch_bim",  "title": "🏛️ Arch, Structure & ID",  "description": "Revit · Navisworks · ACC · DYANMO"},
            {"id": "mepf_bim",  "title": "⚙️ MEPF BIM Training",              "description": "Revit MEP · Navisworks · ACC "},
            {"id": "workshop",  "title": "⚡ BIM Workshop",             "description": "Upcoming batch — register now"},
            {"id": "back_main", "title": "↩ Back to Main Menu",               "description": ""},
        ]
    }
]

COURSE_ARCH = """🏛️ *BIM Training for Architecture, Structure & Interior Design *

✅ Live online sessions with expert trainer
✅ Revit + Navisworks + ACC + DYANMO
✅ Real project-based learning
✅ WhatsApp group support throughout
✅ Certificate of Completion

*To get fee details & batch dates, Please reply with your details in this exact format:*
  Your *Name*
  *Phone NUmber*
  *Email Address*
  *address*
  *Profession* (Student / Working Professional)
  *Company or College
  *Years of Experience*"""

COURSE_MEPF = """⚙️ *MEPF BIM Training*

For BIM MEP Trainings (For MEP Engineers) visit our MEP Training Partner Website :
https://bimsavvyacademy.com/courses

*Please share your details in exact format:*
 Name, , Phone number , Email , Address , Profession , Company/College & Years of Experience to get fee details.*"""

COURSE_WORKSHOP = """⚡ *BIM Workshops — Upcoming !*

   Intensive, focused sessions on specific BIM topics
   *Fee:* 
   *Mode:* Online 

*To register, please share in exact format:*
📝 *Name, Phone, Email , Address , Profession , Company/College , Experience *"""

def confirm_details_received(name: str) -> str:
    return f"""✅ Thank you, *{name}!*

Your enquiry has been noted. Our expert trainer will call or WhatsApp you within *2–4 hours* with complete fee and batch details.

📋 Download our course brochure in the meantime!

_Reply *ENROLL* anytime to start the enrollment process._"""

def enrollment_confirm(name: str, course: str, fee: str, batch_date: str) -> str:
    s = get_settings()
    return f"""🎉 *Excellent, {name}!*

Here are your enrollment details:

📚 *Course:* {course}
📅 *Batch Start:* {batch_date}
💰 *Course Fee:* ₹{fee}

*Payment Options:*
💳 Full Payment: ₹{fee}
📆 Installments available (ask us)

_After payment, reply with your *UTR number* or send a *payment screenshot*._
_We'll confirm within 2 hours._

⚠️ By enrolling, you agree to our:
📄 Privacy Policy: {s.privacy_policy_url}
📄 Terms: {s.terms_url}"""

def qr_caption() -> str:
    s = get_settings()
    return f"""📲 *Scan to pay via UPI*

🏦 UPI ID: {s.upi_id}
👤 Account: {s.upi_name}

_Works with GPay, PhonePe, Paytm, any UPI app_

✉️ After payment, reply with your *UTR number* or send screenshot."""

def utr_received(name: str, utr: str) -> str:
    return f"""✅ *Payment received, {name}!*

UTR: *{utr}*

Our team will verify and confirm within *2 hours*.
You'll receive your *Student ID* and welcome details once verified.

_If you don't hear within 2 hours, call: *+91 72178 22883*_"""

def student_id_welcome(name: str, student_id: str, course: str, batch_date: str) -> str:
    return f"""🎊 *Welcome aboard, {name}!* 🏆

Your enrollment is *CONFIRMED!*

🆔 *Student ID:* {student_id}
📚 *Course:* {course}
📅 *First Session:* {batch_date}

*Important:*
📌 Save your Student ID for all future queries
💬 You'll be added to the WhatsApp study group shortly
🔗 Zoom link will be sent 30 mins before first class

_Need software installation help? Reply *INSTALL*_
_Questions? Reply *HELP*_ 🙏"""

# ── STUDENT PORTAL ────────────────────────────────────────────────────────────
STUDENT_ID_PROMPT = """📋 *Existing Student Portal*

Please enter your *Student ID* to continue.

Example: *#BIMP-2026-1234*

_Don't know your ID? Reply *HELP* and we'll look it up._"""

def student_menu_body(name: str) -> str:
    return f"✅ *Verified! Hello {name}* 👋\n\nWhat do you need help with today?"

STUDENT_MENU_SECTIONS = [
    {
        "title": "Student Support",
        "rows": [
            {"id": "zoom_link",   "title": "🔗 Get Today's Zoom Link",      "description": "Join the current or next session"},
            {"id": "next_class",  "title": "📅 Next Class Schedule",         "description": "Date and time of upcoming sessions"},
            {"id": "install",     "title": "💻 Software Installation Help",  "description": "Revit, Navisworks, BIM 360 setup"},
            {"id": "submit_proj", "title": "📤 Submit My Project",           "description": "Upload link for project submission"},
            {"id": "attendance",  "title": "📊 Check My Attendance",         "description": "View your attendance percentage"},
            {"id": "cert_status", "title": "🎓 Certificate Status",          "description": "Check if certificate is ready"},
            {"id": "other_help",  "title": "❓ Other Help",                   "description": "Ask any other question"},
        ]
    }
]

def zoom_link_msg(link: str, course: str, date_time: str) -> str:
    return f"""🔗 *Session Zoom Link*

📚 Course: {course}
📅 Date & Time: {date_time}

*Zoom Link:* {link}

_Join 5 minutes early. Keep mic muted on entry._ 🎧"""

INSTALL_GUIDE = """💻 *Revit Installation Guide*

*System Requirements:*
• OS: Windows 10 or 11 (64-bit)
• RAM: 8 GB minimum (16 GB recommended)
• Disk: 3 GB free space

*Steps:*
1️⃣ Go to *autodesk.com/education*
2️⃣ Create a free Autodesk Education account
3️⃣ Search for "Revit" → Get Product
4️⃣ Download the installer (.exe)
5️⃣ Right-click → *Run as Administrator*
6️⃣ Follow installer steps, restart when prompted
7️⃣ Launch Revit → Sign in with Autodesk account

_Facing issues? Send a screenshot and our team will help!_ 📸"""

# ── PROJECTS ──────────────────────────────────────────────────────────────────
PROJECT_MENU_BODY = "🏗️ *BIM & Design Projects*\n\nWe deliver world-class BIM and design services. What are you looking for?"

PROJECT_MENU_BUTTONS = [
    {"id": "arch_project", "label": "🏛️ Architecture / Interior"},
    {"id": "bim_project",  "label": "📐 BIM Projects"},
    {"id": "discuss",      "label": "📞 Discuss My Project"},
]

PROJECT_ARCH_DETAILS = """🏛️ *Architecture & Interior Design Projects*

✅ Architectural Design & Drawings
✅ Interior Design & 3D Visualization
✅ Landscape Design
✅ Construction Documentation
✅ Rendering & Walkthroughs

*To get a quote, please share:*
📝 *Name, Country & City, Email*
📋 *Project Description* (building type, area, requirements)"""

PROJECT_BIM_DETAILS = """📐 *BIM Projects — Coordination & Modelling*

✅ BIM Modelling (Architectural, Structural, MEP)
✅ Clash Detection (Navisworks)
✅ BIM 360 Cloud Collaboration
✅ As-Built Documentation
✅ LOD 100–400 modelling

*Please share:*
📝 *Name, Company/Firm, Country & City, Email*
📋 *Project Description*"""

def project_received(name: str) -> str:
    return f"""✅ *Thank you, {name}!*

Your project enquiry has been noted. Our BIM expert will review your requirements and reach out within *4–8 business hours*.

_Want to share project files?_
📧 *askus@bimtrainingandprojects.com*"""

# ── REMINDERS ─────────────────────────────────────────────────────────────────
def installment_reminder(name: str, amount: str, due_date: str, days_left: int) -> str:
    day_str = f"{days_left} day{'s' if days_left > 1 else ''}"
    return f"""⏰ *Payment Reminder — BIM Training & Projects*

Hi *{name}*,

Your *2nd installment of ₹{amount}* is due in *{day_str}* ({due_date}).

_Scan the QR code to pay via UPI._

After payment, reply with your *UTR number* 🙏"""

def session_reminder(name: str, course: str, date_time: str, zoom_link: str) -> str:
    return f"""🔔 *Class Reminder — Starting Soon!*

Hi {name}!

📚 *{course}*
🕐 *Today at {date_time}*
🔗 *Join:* {zoom_link}

_Join 5 minutes early. See you there!_ 🎓"""

def seat_filling_alert(course: str, seats_left: int, last_date: str) -> str:
    return f"""🚨 *BIM Training — Limited Seats!*

📚 *{course}*

⚠️ Only *{seats_left} seats remaining!*
📅 *Registration closes:* {last_date}

Don't miss out on India's most practical BIM training!

Reply *ENROLL* to secure your seat now 👇"""

# ── CERTIFICATE ───────────────────────────────────────────────────────────────
def certificate_ready(name: str, course: str) -> str:
    return f"""🎓 *Congratulations, {name}!* 🏆

You have successfully completed:
📚 *{course}*

Your certificate has been sent to your registered email.
_Please check your inbox (and spam folder)._

🌟 *Please share your experience:*
⭐ Google Review: https://g.page/r/YOUR_LINK
💼 LinkedIn: https://linkedin.com/company/bim-training-and-projects

Your review helps other professionals find quality BIM training 🙏"""

REVIEW_BUTTONS = [
    {"id": "review_google",   "label": "⭐ Google Review"},
    {"id": "review_linkedin", "label": "💼 LinkedIn"},
    {"id": "review_skip",     "label": "⏩ Skip"},
]

# ── HUMAN HANDOFF ─────────────────────────────────────────────────────────────
def human_handoff() -> str:
    s = get_settings()
    return f"""I understand! Let me connect you with our expert trainer. 🙏

They will reach out within *2–4 hours* (Mon–Sat, 9AM–7PM IST).

For urgent queries:
📞 *+91 72178 22883*
📧 *askus@bimtrainingandprojects.com*
🌐 *{s.website_url}*"""
