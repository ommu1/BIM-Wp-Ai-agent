# app/services/sheets.py
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


# ── LOG BIM TRAINING LEAD (Architecture & Structure) ─────────────────────────
def log_training_lead(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("BIM Training Leads")
        row = [
            now_str(),
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("address", "") or data.get("city", ""),
            data.get("profession", ""),
            data.get("college", "") or data.get("college/company", ""),
            data.get("experience", ""),
            data.get("course_interest", "Architecture & Structure"),
            "New Lead",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"BIM Training lead logged | phone={data.get('phone')} name={data.get('name')}")
        return True
    except Exception as e:
        logger.error(f"Failed to log BIM training lead | {e}")
        return False


# ── LOG MEPF LEAD ─────────────────────────────────────────────────────────────
def log_mepf_lead(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("MEPF Leads")
        row = [
            now_str(),
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("address", "") or data.get("city", ""),
            data.get("profession", ""),
            data.get("college", "") or data.get("college/company", ""),
            data.get("experience", ""),
            "MEPF BIM Training",
            "New Lead",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"MEPF lead logged | phone={data.get('phone')}")
        return True
    except Exception as e:
        logger.error(f"Failed to log MEPF lead | {e}")
        return False


# ── LOG WORKSHOP LEAD ─────────────────────────────────────────────────────────
def log_workshop_lead(data: Dict[str, Any]) -> bool:
    try:
        ws = _get_sheet("WORKSHOP Leads")
        row = [
            now_str(),
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("address", "") or data.get("city", ""),
            data.get("profession", ""),
            data.get("college", "") or data.get("college/company", ""),
            data.get("experience", ""),
            "BIM Workshop",
            "New Registration",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"Workshop lead logged | phone={data.get('phone')}")
        return True
    except Exception as e:
        logger.error(f"Failed to log workshop lead | {e}")
        return False


# ── ENROLL STUDENT ────────────────────────────────────────────────────────────
def enroll_student(data: Dict[str, Any]) -> Optional[str]:
    try:
        ws = _get_sheet("Existing students")
        student_id = generate_student_id()
        row = [
            student_id,
            data.get("name", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("address", "") or data.get("city", ""),
            data.get("college", ""),
            data.get("profession", ""),
            data.get("experience", ""),
            data.get("course", ""),
            data.get("batch_date", ""),
            "Payment Pending",
            now_str(),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"Student enrolled | id={student_id} phone={data.get('phone')}")
        return student_id
    except Exception as e:
        logger.error(f"Failed to enroll student | {e}")
        return None


# ── VERIFY STUDENT BY ID ──────────────────────────────────────────────────────
def verify_student(student_id: str) -> Dict[str, Any]:
    try:
        ws = _get_sheet("Existing students")
        rows = ws.get_all_values()
        for row in rows[1:]:
            if row and row[0] == student_id:
                return {
                    "found":       True,
                    "student_id":  row[0],
                    "name":        row[1],
                    "phone":       row[2],
                    "email":       row[3],
                    "course":      row[8] if len(row) > 8  else "",
                    "batch_date":  row[9] if len(row) > 9  else "",
                    "status":      row[10] if len(row) > 10 else "",
                }
        return {"found": False}
    except Exception as e:
        logger.error(f"Failed to verify student | {e}")
        return {"found": False}


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
    try:
        ws = _get_sheet("Existing students")
        rows = ws.get_all_values()
        pending = []
        today = datetime.now()
        for row in rows[1:]:
            if len(row) < 12:
                continue
            status = row[10] if len(row) > 10 else ""
            if "pending" in status.lower():
                pending.append({
                    "student_id": row[0],
                    "name":       row[1],
                    "phone":      row[2],
                    "email":      row[3],
                    "course":     row[8] if len(row) > 8 else "",
                })
        return pending
    except Exception as e:
        logger.error(f"Failed to get pending installments | {e}")
        return []


# ── GET ENROLLED STUDENTS ─────────────────────────────────────────────────────
def get_enrolled_students() -> List[Dict]:
    try:
        ws = _get_sheet("Existing students")
        rows = ws.get_all_values()
        active_statuses = {"Active", "Payment Confirmed"}
        students = []
        for row in rows[1:]:
            if len(row) > 10 and row[10] in active_statuses:
                students.append({
                    "student_id": row[0],
                    "name":       row[1],
                    "phone":      row[2],
                    "email":      row[3],
                    "course":     row[8] if len(row) > 8 else "",
                })
        return students
    except Exception as e:
        logger.error(f"Failed to get enrolled students | {e}")
        return []