<<<<<<< HEAD
# gob-agent
=======
# GOB 🤖 — Government Job Agent

> Monitors government exam websites and sends you Telegram alerts when a new notification drops. Powered by Firecrawl (scraping), Gemini AI (reasoning), and n8n (automation).

Built for Indian students tracking exams like **GATE, RBI Grade B, UPSC IES, SSC JE**.

---

## How It Works

```
Every day at 9AM
       ↓
Fetch list of sites from GOB backend
       ↓
Scrape each site with Firecrawl (clean Markdown)
       ↓
Gemini AI reads the content and decides: relevant or not?
       ↓
Relevant? → Send Telegram alert → Log it
Not relevant? → Skip quietly
```

---

## What You Need (Get These First)

### 1. Firecrawl API Key (Free)
- Go to: https://firecrawl.dev
- Sign Up → Dashboard → API Keys → Create Key
- Free plan: 500 credits/month (plenty for daily checks)

### 2. Gemini API Key (Free)
- Go to: https://aistudio.google.com
- Sign in with Google → Get API Key → Create API Key
- Free tier is very generous (enough for daily use)

### 3. Telegram Bot Token + Chat ID
**Step A: Create your bot**
1. Open Telegram
2. Search for `@BotFather`
3. Send: `/newbot`
4. Pick a name (e.g., `My GOB Bot`)
5. Pick a username (must end in `bot`, e.g., `mygobjob_bot`)
6. Copy the token it gives you → `TELEGRAM_BOT_TOKEN`

**Step B: Get your Chat ID**
1. Create a Telegram group (e.g., "GOB Alerts")
2. Add your bot to the group
3. Send any message in the group
4. Open this URL in your browser (replace YOUR_TOKEN):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
5. Find `"chat":{"id": -XXXXXXXXX}` — copy that number → `TELEGRAM_CHAT_ID`
   > Note: Group IDs are negative numbers (e.g., `-1001234567890`)

---

## Setup (One Time)

### Step 1: Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/gob.git
cd gob
```

### Step 2: Run the setup script
```bash
bash setup.sh
```

This will:
- Check Docker is running
- Create your `.env` file from the template
- Tell you what to fill in

### Step 3: Fill in your `.env` file
Open `.env` in VS Code and replace the placeholder values:
```bash
code .env
```

Fill in:
```
FIRECRAWL_API_KEY=fc-your-actual-key
GEMINI_API_KEY=AIza-your-actual-key
TELEGRAM_BOT_TOKEN=123456:ABC-your-actual-token
TELEGRAM_CHAT_ID=-1001234567890
```

### Step 4: Run setup again (starts everything)
```bash
bash setup.sh
```

You'll see:
```
✅ GOB is running!
  n8n UI:      http://localhost:5678
  Backend API: http://localhost:8000
  API Docs:    http://localhost:8000/docs
```

---

## Set Up n8n (One Time — 5 Minutes)

### Step 1: Open n8n
Go to http://localhost:5678 → Log in with:
- Username: `admin` (or whatever you set in `.env`)
- Password: `changeme123` (or whatever you set in `.env`)

### Step 2: Set your API keys as Variables
Go to **Settings (gear icon) → Variables → Add Variable** for each:

| Name | Value |
|------|-------|
| `FIRECRAWL_API_KEY` | your Firecrawl key |
| `GEMINI_API_KEY` | your Gemini key |
| `TELEGRAM_BOT_TOKEN` | your Telegram bot token |
| `TELEGRAM_CHAT_ID` | your group/chat ID |

### Step 3: Import the workflow
1. Click **+ New Workflow** → top right menu → **Import from file**
2. Select: `n8n-workflow/gob-workflow.json`
3. Click **Save**

### Step 4: Test it manually
1. In n8n, click **Execute Workflow** (the play button ▶️)
2. Watch the nodes light up green one by one
3. Check your Telegram group — you should get a message!

### Step 5: Activate it
Toggle the **Active** switch at the top right of the workflow.
GOB will now run automatically every day at 9AM IST.

---

## Manage Your Sites

Visit http://localhost:8000/docs for the full interactive API.

### Add a new site to monitor
```bash
curl -X POST http://localhost:8000/sites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "IBPS Notifications",
    "url": "https://www.ibps.in/crp-clerks/",
    "keywords": ["Clerk", "PO", "2026", "notification"],
    "description": "IBPS banking recruitment"
  }'
```

### See all sites being monitored
```bash
curl http://localhost:8000/sites
```

### See recent alerts
```bash
curl http://localhost:8000/alerts
```

### Pause a site (stop monitoring it)
```bash
curl -X DELETE http://localhost:8000/sites/2
```

### Default sites (pre-loaded automatically)
GOB comes pre-loaded with:
- RBI Opportunities page
- GATE 2026 official site
- UPSC active examinations
- SSC notifications

---

## Share With Friends

Your friend needs to:
1. Install Docker Desktop
2. Clone the same GitHub repo: `git clone https://github.com/YOUR_USERNAME/gob.git`
3. Create their own `.env` with their own API keys (Firecrawl + Gemini are free)
4. Run `bash setup.sh`
5. Import the workflow in n8n
6. Use their own Telegram bot (or you add them to your existing group)

Each person runs GOB locally on their own machine. No server needed.

---

## Project Structure

```
gob/
├── docker-compose.yml        ← Runs n8n + backend together
├── .env.example              ← Template for your API keys
├── .env                      ← Your actual keys (NEVER commit this!)
├── .gitignore                ← Keeps .env out of git
├── setup.sh                  ← One-click setup script
│
├── backend/                  ← FastAPI site manager
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py               ← All API routes + SQLite DB
│
└── n8n-workflow/
    └── gob-workflow.json     ← Import this into n8n
```

---

## Useful Commands

```bash
# Start GOB
docker compose up -d

# Stop GOB
docker compose down

# View live logs
docker compose logs -f

# Restart after changing backend code
docker compose restart backend

# Check status
docker compose ps
```

---

## Troubleshooting

**"Site couldn't be scraped"** alert in Telegram
→ The site might be down or blocked Firecrawl. Check the URL manually.

**Gemini says nothing relevant but you know there is something**
→ The site's content might be behind a login. Try a different URL (e.g., the PDF direct link page).

**n8n workflow not running**
→ Make sure the "Active" toggle is ON in n8n. Check that Variables are set correctly.

**Backend not starting**
→ Run `docker compose logs backend` and check for Python errors.

**Changing check frequency**
→ In n8n, click the "Daily 9AM Trigger" node → change the cron:
  - Every 6 hours: `0 */6 * * *`
  - Every morning + evening: `0 9,21 * * *`
  - Weekdays only at 9AM: `0 9 * * 1-5`

---

## Coming Later (WhatsApp)

Once everything is working on Telegram, you can switch to WhatsApp:
1. Go to developers.facebook.com → Create a WhatsApp Business App
2. Get a WhatsApp Phone Number ID + Access Token
3. In n8n, replace the "Send Telegram Alert" node with an HTTP Request to:
   `https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages`

---

*GOB — Built with ❤️ for Indian students who don't want to miss that one notification.*
>>>>>>> ebc9a57 (Initial commit: GOB Agent Core)
