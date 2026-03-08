# BIM Training & Projects — WhatsApp AI Agent (Python / FastAPI)

**Meta Cloud API v20.0 | FastAPI | GPT-4o | Google Sheets | APScheduler**

## Project Structure

```
bim-fastapi-agent/
├── app/
│   ├── main.py                     ← FastAPI app, webhook endpoints, API routes
│   ├── config/
│   │   ├── settings.py             ← All environment variables (pydantic-settings)
│   │   └── messages.py             ← All bot message templates (edit here!)
│   ├── flows/
│   │   ├── message_handler.py      ← Central router for all incoming messages
│   │   ├── welcome_flow.py         ← Greeting + main menu
│   │   ├── training_flow.py        ← BIM training enquiry → enrollment → payment
│   │   ├── projects_flow.py        ← Architecture/BIM project enquiries
│   │   └── student_flow.py         ← Existing student portal
│   ├── services/
│   │   ├── whatsapp.py             ← Meta Cloud API (text, buttons, lists, images)
│   │   ├── sheets.py               ← Google Sheets CRUD (gspread)
│   │   ├── ai.py                   ← GPT-4o replies, intent detection, NER
│   │   └── mailer.py               ← Gmail SMTP certificates & enrollment emails
│   ├── jobs/
│   │   └── reminders.py            ← APScheduler: installment reminders, broadcasts
│   └── utils/
│       ├── session_store.py        ← Per-user conversation state (in-memory)
│       └── logger.py               ← Python logging to console + file
├── scripts/
│   ├── google_apps_script.js       ← Paste in script.google.com
│   └── test_bot.py                 ← Local test without real WhatsApp
├── Procfile                        ← Railway.app start command
├── railway.json                    ← Railway deployment config
├── requirements.txt
└── .env.example
```

## Quick Start

### 1. Install dependencies
```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in all values in .env
```

### 3. Run locally
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Test locally (no WhatsApp needed)
```bash
python scripts/test_bot.py
```

### 5. Deploy to Railway
```bash
git init && git add . && git commit -m "BIM FastAPI Agent"
# Push to GitHub → connect Railway → add env vars → deploy
```

## Google Sheets Tab Setup
Create these tabs (exact names):
- `Training Leads`
- `Project Leads`  
- `Students`
- `Payments`
- `IG Leads`
- `AdminConfig` — key/value pairs the bot reads live

## AdminConfig Keys
| Key | Example Value |
|-----|--------------|
| `arch_fee` | 18000 |
| `mepf_fee` | 15000 |
| `arch_batch` | 15 March 2026 |
| `zoom_default` | https://zoom.us/j/YOUR_ID |
| `next_class_time` | Saturday 10:00 AM IST |
| `class_schedule` | Every Sat & Sun, 10 AM–12 PM IST |
| `brochure_url` | https://your-site.com/brochure.pdf |

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/webhook` | Meta webhook verification |
| POST | `/webhook` | Receive all WhatsApp messages |
| GET | `/health` | Health check + session count |
| POST | `/api/confirm-payment` | Send Student ID (from Apps Script) |
| POST | `/api/send-certificate` | Send certificate (from Apps Script) |
| POST | `/api/schedule-reminder` | Schedule a session reminder |
| POST | `/api/broadcast-seats` | Send seat-filling alert |

## Admin WhatsApp Commands
Send from your registered admin phone:
```
ADMIN: STATUS          → Bot status + session count
ADMIN: SESSIONS        → List active sessions
ADMIN: CLEANUP         → Remove expired sessions
ADMIN: PAUSE +91XXXX   → Pause bot for that number
ADMIN: RESUME +91XXXX  → Resume bot for that number
```

## Monthly Cost
| Service | Cost |
|---------|------|
| Meta Cloud API (≤1000 conversations) | ₹0 |
| Railway.app | ₹0 free / ~₹400 paid |
| OpenAI GPT-4o | ~₹800–₹2,000 |
| Google Sheets + Gmail | ₹0 |
| **Total** | **~₹800–₹2,400/month** |
