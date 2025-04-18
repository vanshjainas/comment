import logging
import random
import time
from instagrapi import Client
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# Telegram Bot Token
BOT_TOKEN = "7938933320:AAH0BGREq3pIeSmNO3dwt8cie1t27cQUetk"

# Instagram account credentials (add more if needed)
accounts = [
    {"username": "vansh_jain_17", "password": "DREAMS@123456"},
     {"username": "creep_sen", "password": "INSTABOTTEST"},
    {"username": "bca_batch", "password": "INSTA360BOT"},
    {"username": "man_kind_0001", "password": "kpfans03"},
]

# Emoji list for comments
emojis = ["❤️", "🍀", "🔥", "💯", "🌟", "🙌", "🎯", "😎", "🚀", "🎉"]

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation states
URL, COMMENT, COUNT = range(3)
user_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Welcome! Please send the Instagram post URL:")
    return URL

# Step 1: Get post URL
async def get_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_user.id] = {"url": update.message.text}
    await update.message.reply_text("✅ Got the URL. Now send your base comment:")
    return COMMENT

# Step 2: Get comment
async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data[update.effective_user.id]["comment"] = update.message.text
    await update.message.reply_text("💬 How many comments should each account post?")
    return COUNT

# Step 3: Get count
async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    try:
        user_data[user_id]["count"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return COUNT

    await update.message.reply_text("⏳ Starting the commenting process...")
    await run_commenting(update, context)
    return ConversationHandler.END

# Core logic: comment using multiple accounts
async def run_commenting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = user_data[user_id]["url"]
    base_comment = user_data[user_id]["comment"]
    comments_per_account = user_data[user_id]["count"]

    if not accounts:
        await update.message.reply_text("⚠️ No Instagram accounts are configured.")
        return

    # Login with first account to get media_id
    try:
        cl_first = Client()
        cl_first.login(accounts[0]["username"], accounts[0]["password"])
        media_id = cl_first.media_id(cl_first.media_pk_from_url(url))
    except Exception as e:
        await update.message.reply_text(f"❌ Could not fetch media ID: {e}")
        return

    # Loop through each account and comment
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
                await update.message.reply_text(
                    f"✅ {acc['username']} commented ({i+1}/{comments_per_account}): {comment}"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error commenting: {e}")
            time.sleep(7)  # Delay to prevent spam

        cl.logout()
        time.sleep(10)  # Cooldown before switching accounts

    await update.message.reply_text("🎉 All comments have been posted!")

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# Main setup
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
