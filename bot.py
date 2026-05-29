"""
Simple Slurry Order Bot
"""

import os
import logging
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NAME, COMPANY, LICENSE, CONTAINER_SIZE, FLAVOR, QUANTITY, ADDRESS, CONTACT, NOTES, CONFIRM = range(10)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
ORDER_EMAIL_TO = os.environ["ORDER_EMAIL_TO"]

CONTAINER_OPTIONS = {
    "container_3_5": "3.5 Gallon",
    "container_5": "5 Gallon Bucket",
    "container_55": "55 Gallon Drum",
}


def order_summary(data):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"🛒 SIMPLE SLURRY ORDER\n"
        f"────────────────────────────\n"
        f"📅 Submitted: {ts}\n"
        f"👤 Customer: {data['name']}\n"
        f"🏢 Company: {data['company']}\n"
        f"🪪 License #: {data['license']}\n"
        f"📦 Container: {data['container_size']}\n"
        f"🍬 Flavor: {data['flavor']}\n"
        f"⚖️ Quantity: {data['quantity']}\n"
        f"🚚 Ship To: {data['address']}\n"
        f"📞 Contact: {data['contact']}\n"
        f"📝 Notes: {data.get('notes', 'None')}\n"
        f"────────────────────────────"
    )



def send_order_email(data):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Simple Slurry <onboarding@resend.dev>",
                "to": [ORDER_EMAIL_TO],
                "subject": f"New Simple Slurry Order — {data['company']}",
                "text": order_summary(data),
            },
            timeout=30,
        )

        logger.info("Resend response: %s", response.text)

        return response.status_code in [200, 201]

    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "👋 Welcome to the Simple Slurry Order Form!\n\n"
        "I'll guide you through each step. Type /cancel at any time to start over.\n\n"
        "What is your full name?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("🏢 What is your company name?")
    return COMPANY


async def get_company(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["company"] = update.message.text.strip()
    await update.message.reply_text("🪪 What is your license number?\n(Type N/A if not applicable)")
    return LICENSE


async def get_license(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["license"] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("3.5 Gallon", callback_data="container_3_5")],
        [InlineKeyboardButton("5 Gallon Bucket", callback_data="container_5")],
        [InlineKeyboardButton("55 Gallon Drum", callback_data="container_55")],
    ]

    await update.message.reply_text(
        "📦 Select your container size:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONTAINER_SIZE


async def get_container_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ctx.user_data["container_size"] = CONTAINER_OPTIONS[query.data]

    await query.edit_message_text(
        f"📦 Container selected: {ctx.user_data['container_size']}"
    )

    await query.message.reply_text(
        "🍬 What flavor would you like?\n"
        "Example: Watermelon, Blue Raspberry, Mango"
    )
    return FLAVOR


async def get_flavor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["flavor"] = update.message.text.strip()
    await update.message.reply_text(
        "⚖️ How many units are you ordering?\nExample: 4 buckets, 1 drum, 10 x 3.5 gal"
    )
    return QUANTITY


async def get_quantity(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["quantity"] = update.message.text.strip()
    await update.message.reply_text(
        "🚚 What is the delivery address?\nFull street address including city, state, zip."
    )
    return ADDRESS


async def get_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["address"] = update.message.text.strip()
    await update.message.reply_text("📞 Your contact phone and/or email?")
    return CONTACT


async def get_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["contact"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 Any special instructions or notes?\nType none to skip."
    )
    return NOTES


async def get_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    notes = update.message.text.strip()
    ctx.user_data["notes"] = notes if notes.lower() != "none" else "None"

    summary = order_summary(ctx.user_data)

    keyboard = [
        [InlineKeyboardButton("SUBMIT", callback_data="submit_order")],
        [InlineKeyboardButton("CANCEL", callback_data="cancel_order")],
    ]

    await update.message.reply_text(
        f"Please review your order:\n\n{summary}\n\nTap SUBMIT to send this order.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONFIRM


async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "submit_order":
        await query.edit_message_text("⏳ Submitting your order...")

        success = send_order_email(ctx.user_data)

        if success:
            await query.message.reply_text(
                "✅ Order submitted!\n\n"
                "We received your order and will be in touch shortly. "
                "Thank you for ordering Simple Slurry! 🍬"
            )
        else:
            await query.message.reply_text(
                "⚠️ Order was recorded, but there was an issue sending the email notification."
            )

    else:
        await query.edit_message_text("❌ Order cancelled. Type /start to begin a new order.")

    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Order cancelled. Type /start whenever you're ready to place an order.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company)],
            LICENSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_license)],
            CONTAINER_SIZE: [CallbackQueryHandler(get_container_size, pattern="^container_")],
            FLAVOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_flavor)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)],
            CONFIRM: [CallbackQueryHandler(confirm, pattern="^(submit_order|cancel_order)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
