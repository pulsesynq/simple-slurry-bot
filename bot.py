"""
Simple Slurry Order Bot
Step-by-step order intake form via Telegram. Emails completed orders.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Conversation states ──────────────────────────────────────────────────────
(
    NAME,
    COMPANY,
    LICENSE,
    CONTAINER_SIZE,
    QUANTITY,
    FLAVOR,
    ADDRESS,
    CONTACT_PHONE,
    CONTACT_EMAIL,
    NOTES,
    CONFIRM,
) = range(11)

# ── Config ───────────────────────────────────────────────────────────────────
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.environ["SMTP_USER"]
SMTP_PASSWORD  = os.environ["SMTP_PASSWORD"]
ORDER_EMAIL_TO = os.environ["ORDER_EMAIL_TO"]

CONTAINER_OPTIONS = ["3.5 Gallon", "5 Gallon", "55 Gallon Drum"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def order_summary(data: dict) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"🛒  SIMPLE SLURRY ORDER\n"
        f"{'─'*36}\n"
        f"📅  Submitted:        {ts}\n"
        f"👤  Full Name:        {data['name']}\n"
        f"🏢  Company:          {data['company']}\n"
        f"🪪  License #:        {data['license']}\n"
        f"📦  Container Size:   {data['container_size']}\n"
        f"⚖️   Quantity:         {data['quantity']}\n"
        f"🍬  Flavor:           {data['flavor']}\n"
        f"🚚  Ship To:          {data['address']}\n"
        f"📞  Phone:            {data['phone']}\n"
        f"📧  Email:            {data['email']}\n"
        f"📝  Notes:            {data.get('notes', 'None')}\n"
        f"{'─'*36}"
    )


def send_order_email(data: dict) -> bool:
    subject = (
        f"New Slurry Order — {data['company']} | "
        f"{data['quantity']} x {data['container_size']} | {data['flavor']}"
    )
    body = order_summary(data)

    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = ORDER_EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, ORDER_EMAIL_TO, msg.as_string())
        return True
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False


# ── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    await update.message.reply_text(
        "👋 Welcome to the *Simple Slurry Order Form!*\n\n"
        "I'll guide you through each step. Type /cancel at any time to start over.\n\n"
        "*What is your full name?*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "🏢 *What is your company name?*",
        parse_mode="Markdown",
    )
    return COMPANY


async def get_company(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["company"] = update.message.text.strip()
    await update.message.reply_text(
        "🪪 *What is your license number?*\n_(Type N/A if not applicable)_",
        parse_mode="Markdown",
    )
    return LICENSE


async def get_license(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["license"] = update.message.text.strip()
    keyboard = [[opt] for opt in CONTAINER_OPTIONS]
    await update.message.reply_text(
        "📦 *Select your container size:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CONTAINER_SIZE


async def get_container_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    if choice not in CONTAINER_OPTIONS:
        keyboard = [[opt] for opt in CONTAINER_OPTIONS]
        await update.message.reply_text(
            "Please choose one of the options below:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return CONTAINER_SIZE
    ctx.user_data["container_size"] = choice
    await update.message.reply_text(
        f"⚖️ *How many {choice}s would you like to order?*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return QUANTITY


async def get_quantity(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["quantity"] = update.message.text.strip()
    await update.message.reply_text(
        "🍬 *What flavor would you like?*\n_(e.g. Watermelon, Blue Raspberry, Mango)_",
        parse_mode="Markdown",
    )
    return FLAVOR


async def get_flavor(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["flavor"] = update.message.text.strip()
    await update.message.reply_text(
        "🚚 *What is the shipping address?*\n_(Full address including city, state, and zip)_",
        parse_mode="Markdown",
    )
    return ADDRESS


async def get_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["address"] = update.message.text.strip()
    await update.message.reply_text(
        "📞 *What is your contact phone number?*",
        parse_mode="Markdown",
    )
    return CONTACT_PHONE


async def get_contact_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(
        "📧 *What is your contact email address?*",
        parse_mode="Markdown",
    )
    return CONTACT_EMAIL


async def get_contact_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["email"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 *Any special instructions or notes?*\n_(Type 'none' to skip)_",
        parse_mode="Markdown",
    )
    return NOTES


async def get_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    ctx.user_data["notes"] = "None" if raw.lower() == "none" else raw

    summary = order_summary(ctx.user_data)
    keyboard = [["✅ Confirm & Submit", "❌ Cancel"]]
    await update.message.reply_text(
        f"*Please review your order:*\n\n`{summary}`\n\nReady to submit?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CONFIRM


async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()

    if choice == "✅ Confirm & Submit":
        await update.message.reply_text(
            "⏳ Submitting your order...",
            reply_markup=ReplyKeyboardRemove(),
        )
        success = send_order_email(ctx.user_data)
        if success:
            await update.message.reply_text(
                "✅ *Order submitted!*\n\n"
                "We've received your order and will be in touch shortly. "
                "Thank you for ordering Simple Slurry! 🍬",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "⚠️ Your order was recorded but we had trouble sending the email confirmation. "
                "Please contact us directly to confirm.",
            )
    else:
        await update.message.reply_text(
            "❌ Order cancelled. Type /start to begin a new order.",
            reply_markup=ReplyKeyboardRemove(),
        )

    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    await update.message.reply_text(
        "Order cancelled. Type /start whenever you're ready.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:           [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            COMPANY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company)],
            LICENSE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_license)],
            CONTAINER_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_container_size)],
            QUANTITY:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            FLAVOR:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flavor)],
            ADDRESS:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            CONTACT_PHONE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact_phone)],
            CONTACT_EMAIL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact_email)],
            NOTES:          [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)],
            CONFIRM:        [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
