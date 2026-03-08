# app/services/mailer.py
# Gmail SMTP via aiosmtplib — certificate dispatch & enrollment emails

import ssl
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import get_settings
from app.utils.logger import logger


def _build_envelope(to: str, subject: str, html_body: str) -> MIMEMultipart:
    s = get_settings()
    msg = MIMEMultipart("alternative")
    msg["From"]    = f'"{s.business_name}" <{s.gmail_user}>'
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    return msg


async def _send(to: str, subject: str, html_body: str):
    s = get_settings()
    msg = _build_envelope(to, subject, html_body)
    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=465,
            use_tls=True,
            username=s.gmail_user,
            password=s.gmail_app_password,
        )
        logger.info(f"Email sent | to={to} subject={subject[:40]}")
    except Exception as e:
        logger.error(f"Email failed | to={to} | {e}")


async def send_enrollment_email(
    to: str, name: str, course: str, student_id: str, batch_date: str
):
    s = get_settings()
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;border:1px solid #e0e0e0;border-radius:8px;">
      <div style="background:#075E54;padding:20px;border-radius:6px 6px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:20px;">{s.business_name}</h1>
        <p style="color:rgba(255,255,255,0.8);margin:4px 0 0;">Enrollment Confirmed 🎓</p>
      </div>
      <div style="padding:24px;">
        <p>Dear <strong>{name}</strong>,</p>
        <p>Welcome to <strong>{s.business_name}!</strong> Your enrollment has been confirmed.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr><td style="padding:8px;background:#f5f5f5;"><strong>Student ID</strong></td><td style="padding:8px;">{student_id}</td></tr>
          <tr><td style="padding:8px;background:#f5f5f5;"><strong>Course</strong></td><td style="padding:8px;">{course}</td></tr>
          <tr><td style="padding:8px;background:#f5f5f5;"><strong>Batch Start</strong></td><td style="padding:8px;">{batch_date}</td></tr>
        </table>
        <p>Your trainer will connect with you via WhatsApp with session links and study material.</p>
        <p style="margin-top:24px;">Warm regards,<br/><strong>{s.business_name} Team</strong><br/>
        <a href="{s.website_url}">{s.website_url}</a></p>
      </div>
    </div>"""
    await _send(to, f"✅ Enrollment Confirmed — {course} | {s.business_name}", html)


async def send_certificate_email(
    to: str, name: str, course: str, student_id: str
):
    s = get_settings()
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;border:1px solid #e0e0e0;border-radius:8px;">
      <div style="background:linear-gradient(135deg,#075E54,#25D366);padding:24px;border-radius:6px 6px 0 0;text-align:center;">
        <h1 style="color:#fff;margin:0;">🏆 Congratulations!</h1>
        <p style="color:rgba(255,255,255,0.9);font-size:16px;">{name}</p>
      </div>
      <div style="padding:24px;">
        <p>Dear <strong>{name}</strong>,</p>
        <p>We are thrilled to certify that you have successfully completed:</p>
        <div style="background:#f0faf0;border-left:4px solid #25D366;padding:16px;margin:20px 0;border-radius:4px;">
          <h2 style="color:#075E54;margin:0;">{course}</h2>
          <p style="color:#666;margin:4px 0 0;">Certificate ID: {student_id}</p>
        </div>
        <p>🌟 Please share your experience:</p>
        <p>
          <a href="https://g.page/r/YOUR_GOOGLE_REVIEW" style="background:#4285F4;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;display:inline-block;margin:4px 4px 4px 0;">⭐ Google Review</a>
          <a href="https://www.linkedin.com/company/bim-training-and-projects" style="background:#0A66C2;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;display:inline-block;margin:4px;">💼 LinkedIn</a>
        </p>
        <p style="margin-top:24px;">With pride,<br/><strong>{s.business_name} Team</strong></p>
      </div>
    </div>"""
    await _send(to, f"🎓 Your Certificate — {course} | {s.business_name}", html)


async def test_smtp() -> bool:
    s = get_settings()
    try:
        async with aiosmtplib.SMTP(hostname="smtp.gmail.com", port=465, use_tls=True) as smtp:
            await smtp.login(s.gmail_user, s.gmail_app_password)
        logger.info("Gmail SMTP connection verified ✅")
        return True
    except Exception as e:
        logger.error(f"Gmail SMTP failed | {e}")
        return False
