# app/services/ai.py
# OpenAI GPT-4o — intent classification, AI replies, detail extraction

import re
import json
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from app.config.settings import get_settings
from app.utils.logger import logger

def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)

SYSTEM_PROMPT = """You are BIMA — the official AI assistant for BIM Training & Projects (www.bimtrainingandprojects.com).

ABOUT THE COMPANY:
- Architecture, Interior Design, and BIM Training provider
- 9+ years expertise, 100+ projects, 5000+ hours of training
- Services: BIM Training (Architecture/Structure/ID + MEPF), Architecture & Interior Design Projects, BIM Consultancy
- Contact: askus@bimtrainingandprojects.com | +91 72178 22883

YOUR ROLE: Warm, professional, concise. Help leads and students with enquiries, enrollment, and support.

FORMATTING: Use WhatsApp formatting (*bold*, _italic_). Keep responses under 300 words. Use emojis naturally. Always end with a next step.

DISCOUNT POLICY: Acknowledge requests warmly. Say "I'll check with our trainer and share the best offer." Never quote a specific discount.

SOFTWARE HELP: Guide users through Revit installation on Windows (autodesk.com/education).

IF UNSURE: Offer to connect to a human expert. Never make up fees, dates, or details."""


async def get_ai_reply(history: List[Dict], user_message: str) -> str:
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history[-12:],
            {"role": "user", "content": user_message},
        ]
        res = await _client().chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=350,
            temperature=0.65,
        )
        reply = res.choices[0].message.content
        logger.debug(f"AI reply | tokens={res.usage.total_tokens}")
        return reply
    except Exception as e:
        logger.error(f"OpenAI error | {e}")
        return "I apologize, I'm having a brief technical issue. Please try again in a moment, or contact us at *askus@bimtrainingandprojects.com* 🙏"


async def classify_intent(message: str) -> str:
    """Returns: training | projects | student | workshop | human | greeting | other"""
    try:
        res = await _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    f"Classify this WhatsApp message into ONE word.\n"
                    f"Categories: training | projects | student | workshop | human | greeting | other\n"
                    f"Message: \"{message}\"\n"
                    f"Reply with ONLY the category word."
                )
            }],
            max_tokens=10,
            temperature=0,
        )
        intent = res.choices[0].message.content.strip().lower()
        logger.debug(f"Intent: {intent} | msg={message[:50]}")
        return intent
    except Exception as e:
        logger.error(f"Intent classification failed | {e}")
        return "other"


async def extract_contact_details(message: str) -> Dict[str, Any]:
    """Extract structured contact info from free text"""
    try:
        res = await _client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    f"Extract contact details from this message. Return ONLY valid JSON, no explanation.\n"
                    f"Fields: name, email, city, country, profession, experience, college, description\n"
                    f"Use null for missing fields.\n"
                    f"Message: \"{message}\""
                )
            }],
            max_tokens=200,
            temperature=0,
        )
        raw = res.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception:
        return {}


def extract_utr(message: str) -> Optional[str]:
    """Extract UTR/transaction number from message"""
    patterns = [
        r'\b(?:UTR|utr|REF|ref|TXN|txn)[:\s#]*([A-Z0-9]{10,22})\b',
        r'\b([0-9]{12,22})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return None
