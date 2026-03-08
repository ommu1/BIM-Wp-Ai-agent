#!/usr/bin/env python3
"""
scripts/test_bot.py
Run locally to simulate conversations without real WhatsApp.
Usage: python scripts/test_bot.py
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock WhatsApp sends so output goes to terminal
from app.services import whatsapp as wa

async def mock_send_text(to, text):
    print(f"\n🤖 BOT → {to}:\n{text}\n{'─'*60}")

async def mock_send_buttons(to, body, buttons, **kwargs):
    btns = " | ".join(b["label"] for b in buttons)
    print(f"\n🤖 BOT BUTTONS → {to}:\n{body}\n[{btns}]\n{'─'*60}")

async def mock_send_list(to, body, btn_label, sections, **kwargs):
    items = " | ".join(r["title"] for r in sections[0]["rows"])
    print(f"\n🤖 BOT LIST → {to}:\n{body}\nItems: {items}\n{'─'*60}")

async def mock_send_image(to, url, caption=""):
    print(f"\n🤖 BOT IMAGE → {to}:\n[QR Code: {url}]\n{caption}\n{'─'*60}")

async def mock_mark_read(msg_id): pass

wa.send_text    = mock_send_text
wa.send_buttons = mock_send_buttons
wa.send_list    = mock_send_list
wa.send_image   = mock_send_image
wa.mark_read    = mock_mark_read

from app.flows.message_handler import handle_incoming_message

TEST_PHONE = "919876543210"

STEPS = [
    ("text",        "Hi",                                    None,         None),
    ("interactive", "🎓 BIM Training / Workshop",            "training",   None),
    ("interactive", "🏛️ Architecture, Structure & ID",        None,         "arch_bim"),
    ("text",        "Rahul Sharma, Mumbai, rahul@gmail.com, 3 years, professional", None, None),
    ("interactive", "Enroll Now",                            "enroll_now", None),
    ("text",        "UTR 409283817264",                      None,         None),
]

async def run_simulation():
    print("\n" + "═"*60)
    print("  BIM WhatsApp AI Agent — Test Simulation")
    print("═"*60)

    for i, (msg_type, text, btn_id, list_id) in enumerate(STEPS, 1):
        print(f"\n👤 USER step {i}: {text}")
        await handle_incoming_message(TEST_PHONE, msg_type, text, btn_id, list_id, None)
        await asyncio.sleep(0.2)

    print("\n✅ Simulation complete!")

if __name__ == "__main__":
    asyncio.run(run_simulation())
