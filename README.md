# Simple Slurry Order Bot 🍬

A Telegram bot that walks customers through a step-by-step order form and emails the completed order summary.

---

## What it collects

- Customer name
- Company name
- License number
- Container size (3.5 Gallon / 5 Gallon Bucket / 55 Gallon Drum)
- Flavor (free text)
- Quantity
- Delivery address
- Contact phone/email
- Notes / special instructions

---

## Setup

### 1. Create your Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **API token** you receive

---

### 2. Set up Gmail for SMTP

You need a Gmail **App Password** (not your regular password):

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification → enable it
3. Security → App passwords → create one for "Mail"
4. Copy the 16-character password

---

### 3. Deploy to Railway (Recommended — free tier, always-on)

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Go to **Variables** tab and add:

| Variable | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | your bot token from BotFather |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your Gmail address |
| `SMTP_PASSWORD` | your Gmail App Password |
| `ORDER_EMAIL_TO` | email where orders should land |

5. Railway auto-detects the `Procfile` and starts the bot as a worker.
6. Done — the bot runs 24/7.

---

### 4. Run locally (optional)

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env with your values
export $(cat .env | xargs)
python bot.py
```

---

## Usage

Customers open your bot in Telegram and type `/start`. The bot guides them through each field one at a time, shows a full order preview, and sends the order to your email on confirmation.

---

## Customization

- **Add products/SKUs**: Edit the `CONTAINER_OPTIONS` list in `bot.py`
- **Change email format**: Edit the `order_summary()` function
- **Add more fields**: Add a new state constant and handler following the same pattern
