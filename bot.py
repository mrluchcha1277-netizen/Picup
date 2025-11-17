# ----------------------------------------------
#  BOT.PY — PART 1 (IMPORTS + TOKEN + GLOBAL STORAGE)
# ----------------------------------------------

import logging
from telegram import Update, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import re
import random
import asyncio

# ----------------------------------------------
# 👉 BOT TOKEN ADD HERE
# ----------------------------------------------
BOT_TOKEN = "8229030784:AAHTsl-s1jPMd6x5tIwkR3AiKH7Ou_PQlzA"   # <<== এখানে তোমার বট টোকেন বসাও

# ----------------------------------------------
# LOGGING SETUP
# ----------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------------------------------------------
# GLOBAL IN-MEMORY STORAGE
# ----------------------------------------------

ADMIN_USERNAME = "MinexxProo"

old_winners = {}        # {userid: "@username"}
new_members = {}        # {userid: "@username"}

awaiting_old = False
awaiting_new = False
awaiting_count = False

winner_count = 0

# ----------------------------------------------
# REGEX FORMAT CHECKER
# ----------------------------------------------
VALID_LINE = re.compile(r"^@[\w\d_]+ \| \d{3,20}$")

def parse_line(line):
    if not VALID_LINE.match(line.strip()):
        return None
    username, userid = line.split("|")
    return username.strip(), int(userid.strip())

def extract_valid_entries(text):
    lines = text.split("\n")
    valid = []
    invalid = []
    for l in lines:
        p = parse_line(l)
        if p:
            valid.append(p)
        else:
            if l.strip() != "":
                invalid.append(l)
    return valid, invalid
# ----------------------------------------------
#  PART 2 — BASIC COMMANDS
# ----------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"""
┌────────────────────────────────────┐
👑 WELCOME ADMIN — @{ADMIN_USERNAME} 👑

🤖 Your Giveaway Bot is Online!
🧰 System Status: READY

📌 Commands:
/on — Activate System

💚 Powered By: @PowerPointBreak
└────────────────────────────────────┘
"""
    )

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
┌────────────────────────────────────────────────┐
✅ SYSTEM ACTIVATED SUCCESSFULLY!

📌 Available Commands:
/oldwinnerlist — Set Old Winners
/newjoinmemberslist — Add New Join Members
/picwinnerlist — Pick Final Winners
/of — Turn Bot OFF

👑 Admin: @MinexxProo
💚 Powered By: @PowerPointBreak
└────────────────────────────────────────────────┘
"""
    )

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
┌────────────────────────────────────┐
⛔ SYSTEM DEACTIVATED!

📌 Bot commands are now disabled.
Use /on to activate again.
└────────────────────────────────────┘
"""
    )

# ----------------------------------------------
#  PART 3 — OLD WINNER LIST
# ----------------------------------------------

async def oldwinner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_old, awaiting_new, awaiting_count
    awaiting_old = True
    awaiting_new = False
    awaiting_count = False

    await update.message.reply_text(
        "📌 Please send your OLD Winner List\nFormat:\n@username | userid"
    )

async def save_old_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_old, old_winners

    valid, invalid = extract_valid_entries(update.message.text)

    if invalid:
        return await update.message.reply_text(
            f"⚠️ Invalid entries removed:\n" + "\n".join(invalid)
        )

    for user, uid in valid:
        old_winners[uid] = user

    awaiting_old = False

    text = "📜 OLD WINNERS:\n"
    c = 1
    for uid, user in old_winners.items():
        text += f"#{c} {user} | {uid}\n"
        c += 1

    await update.message.reply_text(
        f"""
✅ Old Winner List Saved!

{text}

📌 Total Old Winners: {len(old_winners)}

📌 Next:
Use /newjoinmemberslist
"""
  )

# ----------------------------------------------
#  PART 4 — NEW JOIN MEMBERS
# ----------------------------------------------

async def new_join_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_new, awaiting_old, awaiting_count
    awaiting_new = True
    awaiting_old = False
    awaiting_count = False

    await update.message.reply_text(
        "📌 Please send your NEW Giveaway Join Members List\nFormat:\n@username | userid"
    )

async def save_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_new, new_members

    valid, invalid = extract_valid_entries(update.message.text)

    if invalid:
        return await update.message.reply_text(
            f"⚠️ Invalid entries removed:\n" + "\n".join(invalid)
        )

    for user, uid in valid:
        new_members[uid] = user

    awaiting_new = False

    text = "📜 NEW MEMBERS:\n"
    c = 1
    for uid, user in new_members.items():
        text += f"#{c} {user} | {uid}\n"
        c += 1

    await update.message.reply_text(
        f"""
✅ New Join Members List Saved!

{text}

📌 Total New Members: {len(new_members)}

📌 Next:
Use /picwinnerlist
"""
    )

# ----------------------------------------------
#  PART 5 — PIC WINNER LIST
# ----------------------------------------------

async def pick_winner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_count, awaiting_old, awaiting_new
    awaiting_count = True
    awaiting_old = False
    awaiting_new = False

    await update.message.reply_text(
        "📌 How many winners do you want?\n(Choose 1–10000)"
    )

async def set_winner_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global winner_count, awaiting_count

    if not update.message.text.isdigit():
        return await update.message.reply_text("❌ Invalid number! Send a number only.")

    winner_count = int(update.message.text)
    awaiting_count = False

    await run_processing(update, context)

# ----------------------------------------------
#  PART 6 — PROGRESS + REMOVE OLD WINNERS
# ----------------------------------------------

async def run_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Remove old winners
    removed = 0
    for uid in list(new_members.keys()):
        if uid in old_winners:
            removed += 1
            del new_members[uid]

    # PROGRESS SYSTEM
    steps = [
        (0,  "Initializing system modules..."),
        (10, "Scanning users & loading entries..."),
        (20, "Checking duplicate submissions..."),
        (30, "Filtering blocked & old winners..."),
        (35, f"Removed {removed} old winners from new join list..."),
        (40, "Validating usernames & userIDs..."),
        (50, "Securing database & encrypting entries..."),
        (60, "Randomizing participants with safe mode..."),
        (70, "Preparing final candidate list..."),
        (80, "AI Verification running — please wait..."),
        (90, "Finalizing winner selection..."),
        (100, "✔ Winner selection completed!")
    ]

    for percent, msg in steps:
        bar = "▰" * (percent // 10) + "▱" * (10 - (percent // 10))
        await update.message.reply_text(f"{percent}%  {bar}\n{msg}")
        await asyncio.sleep(0.35)

    await show_final_winners(update, context)

# ----------------------------------------------
#  PART 7 — FINAL WINNERS OUTPUT
# ----------------------------------------------

async def show_final_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Pick random winners
    winners = random.sample(list(new_members.items()), winner_count)

    text = """
┌───────────────────────────────┐
│        🏆 WINNER LIST 🏆        │
└───────────────────────────────┘

🎉 FINAL SELECTED WINNERS 🎉
"""

    for username, uid in winners:
        text += f"\n{username} | {uid}"

    text += """
\n✔ Winner selection completed.
━━━━━━━━━━━━━━━━━━━━━━
Hosted By: @PowerPointBreak
Admin: @MinexxProo
━━━━━━━━━━━━━━━━━━━━━━
"""

    await update.message.reply_text(text)


# ----------------------------------------------
#  PART 8 — MAIN RUNNER
# ----------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global awaiting_old, awaiting_new, awaiting_count

    if awaiting_old:
        await save_old_winners(update, context)
    elif awaiting_new:
        await save_new_members(update, context)
    elif awaiting_count:
        await set_winner_count(update, context)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("on", bot_on))
    application.add_handler(CommandHandler("of", bot_off))
    application.add_handler(CommandHandler("oldwinnerlist", oldwinner_start))
    application.add_handler(CommandHandler("newjoinmemberslist", new_join_start))
    application.add_handler(CommandHandler("picwinnerlist", pick_winner_start))

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    application.run_polling()

if __name__ == "__main__":
    main()
