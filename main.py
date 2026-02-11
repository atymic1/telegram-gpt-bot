import os, orjson
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from openai import OpenAI

# Load API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Memory storage
MEMORY_FILE = "memory.json"
MAX_MESSAGES = 20
SYSTEM_PROMPT = "You are a helpful, friendly Telegram assistant."

# ---------- MEMORY FUNCTIONS ----------
def load_memory():
    try:
        with open(MEMORY_FILE, "rb") as f:
            return orjson.loads(f.read())
    except:
        return {}

def save_memory(memory):
    with open(MEMORY_FILE, "wb") as f:
        f.write(orjson.dumps(memory))

user_memory = load_memory()

def get_user_memory(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = [{"role":"system","content":SYSTEM_PROMPT}]
    return user_memory[user_id]

# ---------- COMMANDS ----------
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_memory[user_id] = [{"role":"system","content":SYSTEM_PROMPT}]
    save_memory(user_memory)
    await update.message.reply_text("Memory cleared 🧠")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your ChatGPT bot 🤖")

# ---------- MAIN CHAT ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    msg = update.message.text

    memory = get_user_memory(user_id)
    memory.append({"role":"user","content":msg})

    # keep memory short to reduce cost
    user_memory[user_id] = memory[-MAX_MESSAGES:]

    response = client.chat.completions.create(
        model="gpt-5",   # ⭐ premium model
        messages=user_memory[user_id]
    )

    reply = response.choices[0].message.content
    user_memory[user_id].append({"role":"assistant","content":reply})
    save_memory(user_memory)

    await update.message.reply_text(reply)

# ---------- START BOT ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot running with MEMORY 🧠")
app.run_polling()
