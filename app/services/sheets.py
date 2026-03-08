# app/services/sheets.py
# Google Sheets integration via gspread

import json
import random
from datetime import datetime
from typing import Optional, Dict, List, Any
import gspread
from google.oauth2.service_account import Credentials
from app.config.settings import get_settings
from app.utils.logger import logger

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _get_client() -> gspread.Client:
    s = get_settings()
    creds_dict = json.loads(s.google_service_account_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def _get_sheet(tab_name: str):
    s = get_settings()
    client = _get_client()
    spreadsheet = client.open_by_key(s.google_sheets_spreadsheet_id)
    return spreadsheet.worksheet(tab_name)

def generate_student_id() -> str:
    year = datetime.now().year
    num  = random.randint(1000, 9999)
    return f"#BIMP-{year}-{num}"

def now_str() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


# ── LOG TRAINING LEAD ─────────────────────────────────────────────────────────
def log_training_lead(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("Training Leads")
        row = [
            now_str(),
            data.get("phone", ""),
            data.get("name", ""),
            data.get("email", ""),
            data.get("city", ""),
            data.get("country", "India"),
            data.get("profession", ""),
            data.get("experience", ""),
            data.get("college", ""),
            data.get("course_interest", ""),
            data.get("source", "WhatsApp Bot"),
            "New Lead",
            "",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"Training lead logged | phone={data.get('phone')} name={data.get('name')}")
        return True
    except Exception as e:
        logger.error(f"Failed to log training lead | {e}")
        return False


# ── LOG PROJECT LEAD ──────────────────────────────────────────────────────────
def log_project_lead(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("Project Leads")
        row = [
            now_str(),
            data.get("phone", ""),
            data.get("name", ""),
            data.get("email", ""),
            data.get("country", ""),
            data.get("city", ""),
            data.get("project_type", ""),
            data.get("description", ""),
            data.get("source", "WhatsApp Bot"),
            "New Lead",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"Project lead logged | phone={data.get('phone')}")
        return True
    except Exception as e:
        logger.error(f"Failed to log project lead | {e}")
        return False


# ── LOG INSTAGRAM LEAD ────────────────────────────────────────────────────────
def log_ig_lead(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("IG Leads")
        row = [
            now_str(),
            data.get("ig_username", ""),
            data.get("name", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("interest", ""),
            "Instagram",
            "New Lead",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        logger.error(f"Failed to log IG lead | {e}")
        return False


# ── ENROLL STUDENT ────────────────────────────────────────────────────────────
def enroll_student(data: Dict[str, Any]) -> Optional[str]:
    try:
        ws = _get_sheet("Students")
        student_id = generate_student_id()
        row = [
            student_id,
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("address", ""),
            data.get("city", ""),
            data.get("college", ""),
            data.get("profession", ""),
            data.get("experience", ""),
            data.get("course", ""),
            data.get("batch_date", ""),
            "Payment Pending",
            "", "", "",  # Inst1 Amount, Paid, Date
            "", "", "",  # Inst2 Amount, Paid, DueDate
            "", "",      # Attendance, ProjectSubmitted
            now_str(),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"Student enrolled | id={student_id} phone={data.get('phone')}")
        return student_id
    except Exception as e:
        logger.error(f"Failed to enroll student | {e}")
        return None


# ── LOG PAYMENT ───────────────────────────────────────────────────────────────
def log_payment(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("Payments")
        row = [
            now_str(),
            data.get("student_id", ""),
            data.get("phone", ""),
            data.get("name", ""),
            data.get("amount", ""),
            data.get("utr", ""),
            data.get("installment", "1"),
            "Pending Verification",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"Payment logged | phone={data.get('phone')} utr={data.get('utr')}")
        return True
    except Exception as e:
        logger.error(f"Failed to log payment | {e}")
        return False


# ── VERIFY STUDENT BY ID ──────────────────────────────────────────────────────
def verify_student(student_id: str) -> Dict[str, Any]:
    try:
        ws = _get_sheet("Students")
        rows = ws.get_all_values()
        for row in rows[1:]:  # skip header
            if row and row[0] == student_id:
                return {
                    "found": True,
                    "student_id":  row[0],
                    "name":        row[1],
                    "phone":       row[2],
                    "email":       row[3],
                    "course":      row[9] if len(row) > 9  else "",
                    "batch_date":  row[10] if len(row) > 10 else "",
                    "status":      row[11] if len(row) > 11 else "",
                    "attendance":  row[18] if len(row) > 18 else "",
                    "project_done":row[19] if len(row) > 19 else "",
                }
        return {"found": False}
    except Exception as e:
        logger.error(f"Failed to verify student | {e}")
        return {"found": False}


# ── GET ADMIN CONFIG ──────────────────────────────────────────────────────────
def get_admin_config() -> Dict[str, str]:
    try:
        ws = _get_sheet("AdminConfig")
        rows = ws.get_all_values()
        config = {}
        for row in rows:
            if row and row[0]:
                config[row[0].strip()] = row[1].strip() if len(row) > 1 else ""
        return config
    except Exception as e:
        logger.error(f"Failed to get admin config | {e}")
        return {}


# ── GET STUDENTS WITH PENDING INSTALLMENTS ────────────────────────────────────
def get_students_with_pending_installments() -> List[Dict]:
    from datetime import timedelta
    try:
        ws = _get_sheet("Students")
        rows = ws.get_all_values()
        pending = []
        today = datetime.now()
        for row in rows[1:]:
            if len(row) < 18:
                continue
            inst2_due   = row[17]  # Inst2DueDate
            inst2_paid  = row[16]  # Inst2Paid
            if inst2_due and inst2_paid != "Y":
                try:
                    due_date = datetime.strptime(inst2_due, "%d-%m-%Y")
                    days_left = (due_date - today).days
                    if 0 <= days_left <= 3:
                        pending.append({
                            "student_id": row[0],
                            "name":       row[1],
                            "phone":      row[2],
                            "email":      row[3],
                            "course":     row[9],
                            "amount":     row[15],
                            "due_date":   inst2_due,
                            "days_left":  days_left,
                        })
                except ValueError:
                    pass
        return pending
    except Exception as e:
        logger.error(f"Failed to get pending installments | {e}")
        return []


# ── GET ENROLLED STUDENTS ─────────────────────────────────────────────────────
def get_enrolled_students() -> List[Dict]:
    try:
        ws = _get_sheet("Students")
        rows = ws.get_all_values()
        active_statuses = {"Active", "Payment Confirmed"}
        students = []
        for row in rows[1:]:
            if len(row) > 11 and row[11] in active_statuses:
                students.append({
                    "student_id": row[0],
                    "name":       row[1],
                    "phone":      row[2],
                    "email":      row[3],
                    "course":     row[9] if len(row) > 9 else "",
                })
        return students
    except Exception as e:
        logger.error(f"Failed to get enrolled students | {e}")
        return []
