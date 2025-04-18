import logging
import random
import time
import json
from instagrapi import Client
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# Load bot token from bot.json
with open("bot.json", "r") as f:
    BOT_TOKEN = json.load(f)["token"]

# Load accounts from accounts.json
def load_accounts():
    with open("accounts.json", "r") as f:
        return json.load(f)

# Emojis for comment decoration
emojis = ["❤️", "🍀", "🔥", "💯", "🌟", "🙌", "🎯", "😎", "🚀", "🎉"]

# Logging setup
logging.basicConfig(level=logging.INFO)

# Conversation states
URL, COMMENT, COUNT, MORE_COMMENTS = range(4)
user_data = {}

# --- Help & Start ---
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton("🚀 Start Bot")]]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("ℹ️ Choose an option:", reply_markup=markup)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "start bot" in update.message.text.lower():
        return await start(update, context)
    else:
        await update.message.reply_text("❓ I didn't understand that. Use /help to see options.")
        return ConversationHandler.END

# --- Comment Flow ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Send the Instagram post URL:", reply_markup=ReplyKeyboardRemove())
    return URL

async def get_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_user.id] = {"url": update.message.text}
    await update.message.reply_text("✅ Got the URL. Now send your base comment:")
    return COMMENT

async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_user.id]["comment"] = update.message.text
    await update.message.reply_text("💬 How many comments should each account post?")
    return COUNT

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    try:
        user_data[user_id]["count"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return COUNT

    await update.message.reply_text("⏳ Starting the commenting process...")
    return await run_commenting(update, context)

async def run_commenting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    url = user_data[user_id]["url"]
    base_comment = user_data[user_id]["comment"]
    comments_per_account = user_data[user_id]["count"]

    accounts = load_accounts()
    if not accounts:
        await update.message.reply_text("⚠️ No Instagram accounts are configured.")
        return ConversationHandler.END

    try:
        cl_first = Client()
        cl_first.login(accounts[0]["username"], accounts[0]["password"])
        media_id = cl_first.media_id(cl_first.media_pk_from_url(url))
    except Exception as e:
        await update.message.reply_text(f"❌ Could not fetch media ID: {e}")
        return ConversationHandler.END

    for acc in accounts:
        cl = Client()
        try:
            cl.login(acc["username"], acc["password"])
            await update.message.reply_text(f"🔐 Logged in as {acc['username']}")
        except Exception as e:
            await update.message.reply_text(f"❌ Login failed for {acc['username']}: {e}")
            continue

        for i in range(comments_per_account):
            emoji = random.choice(emojis)
            comment = f"{emoji} {base_comment}"
            try:
                cl.media_comment(media_id, comment)
                await update.message.reply_text(f"✅ {acc['username']} commented ({i+1}/{comments_per_account}): {comment}")
            except Exception as e:
                await update.message.reply_text(f"❌ Error commenting: {e}")
            time.sleep(7)

        cl.logout()
        time.sleep(10)

    await update.message.reply_text("🎉 All comments have been posted!\n\nDo you want to post more comments on the same post? (yes/no)")
    return MORE_COMMENTS

async def handle_more_comments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    if text in ["yes", "y"]:
        await update.message.reply_text("💬 Send your new base comment:")
        return COMMENT
    elif text in ["no", "n"]:
        await update.message.reply_text("👍 Done! You can use /help to start again.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❓ Please reply with 'yes' or 'no'.")
        return MORE_COMMENTS

# --- Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Main Bot Setup ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("help", help_menu))
    app.add_handler(MessageHandler(filters.Regex("^(🚀 Start Bot)$"), handle_menu))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
            MORE_COMMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_more_comments)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
