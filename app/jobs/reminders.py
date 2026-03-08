# app/jobs/reminders.py
# APScheduler jobs for automated reminders

import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services import whatsapp as wa, sheets
from app.config import messages as M
from app.utils.logger import logger

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


# ── JOB 1: Installment reminders — daily at 9 AM IST ─────────────────────────
async def installment_reminder_job():
    logger.info("[CRON] Running installment reminder job")
    try:
        pending = await asyncio.to_thread(sheets.get_students_with_pending_installments)
        for s in pending:
            try:
                # Send QR first
                from app.config.settings import get_settings
                cfg = get_settings()
                await wa.send_image(s["phone"], cfg.upi_qr_image_url,
                                    f"Payment QR — ₹{s['amount']} due {s['due_date']}")

                # Send reminder with buttons
                await wa.send_buttons(
                    s["phone"],
                    M.installment_reminder(s["name"], s["amount"], s["due_date"], s["days_left"]),
                    [
                        {"id": "paid_utr",   "label": "✅ I've Paid"},
                        {"id": "need_help",  "label": "📞 Need Help"},
                        {"id": "ask_human",  "label": "📅 Request Extension"},
                    ],
                )
                logger.info(f"[CRON] Installment reminder sent | phone={s['phone']}")
                await asyncio.sleep(1)  # Rate limit
            except Exception as e:
                logger.error(f"[CRON] Reminder failed | phone={s['phone']} | {e}")

        logger.info(f"[CRON] Installment job done | sent={len(pending)}")
    except Exception as e:
        logger.error(f"[CRON] Installment job error | {e}")


# ── JOB 2: Session reminder — scheduled dynamically ──────────────────────────
async def send_session_reminders(zoom_link: str, course_name: str):
    """Called 30 minutes before a session"""
    logger.info(f"[CRON] Sending session reminders | course={course_name}")
    try:
        students = await asyncio.to_thread(sheets.get_enrolled_students)
        cfg_data = await asyncio.to_thread(sheets.get_admin_config)
        now_str  = datetime.now().strftime("%d %b %Y, %I:%M %p")

        for s in students:
            try:
                await wa.send_text(
                    s["phone"],
                    M.session_reminder(s["name"], course_name, now_str, zoom_link)
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"[CRON] Session reminder failed | phone={s['phone']} | {e}")

        logger.info(f"[CRON] Session reminders done | count={len(students)}")
    except Exception as e:
        logger.error(f"[CRON] Session reminder error | {e}")


def schedule_session_reminder(session_datetime: datetime, zoom_link: str, course_name: str):
    """Schedule a one-off session reminder 30 minutes before"""
    from datetime import timedelta
    remind_at = session_datetime - timedelta(minutes=30)
    now       = datetime.now(remind_at.tzinfo)

    if remind_at <= now:
        logger.warning(f"[CRON] Reminder time already passed | {session_datetime}")
        return False

    job_id = f"session_{session_datetime.strftime('%Y%m%d_%H%M')}"
    scheduler.add_job(
        send_session_reminders,
        "date",
        run_date=remind_at,
        args=[zoom_link, course_name],
        id=job_id,
        replace_existing=True,
    )
    logger.info(f"[CRON] Session reminder scheduled | at={remind_at} id={job_id}")
    return True


# ── JOB 3: Seat-filling broadcast ─────────────────────────────────────────────
async def send_seat_filling_alert(
    phones: list[str], course: str, seats_left: int, last_date: str
):
    logger.info(f"[BROADCAST] Seat alert starting | count={len(phones)}")
    for phone in phones:
        try:
            await wa.send_buttons(
                phone,
                M.seat_filling_alert(course, seats_left, last_date),
                [
                    {"id": "enroll_now", "label": "✅ Enroll Now"},
                    {"id": "brochure",   "label": "📄 Get Brochure"},
                ],
            )
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"[BROADCAST] Failed | phone={phone} | {e}")
    logger.info("[BROADCAST] Seat alert complete")


def start_scheduler():
    scheduler.add_job(
        installment_reminder_job,
        CronTrigger(hour=9, minute=0),
        id="installment_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[CRON] APScheduler started — installment reminders daily at 9 AM IST")
