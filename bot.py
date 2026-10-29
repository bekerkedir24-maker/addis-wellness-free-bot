import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = "8754561416:AAFPghCvpISb9x3Pzqn-0DAezxMz9MpC8ps"

user_data_store = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_data_store[user_id] = {}

  keyboard = [
      [
          InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am"),
          InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
      ]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text(
      "እንኳን ወደ አዲስ ጤና ማጣሪያ ቦት በደህና መጡ! / Welcome to Addis Wellness"
      " Assessment Bot!\nእባክዎ ቋንቋ ይምረጡ / Please choose your language:",
      reply_markup=reply_markup,
  )


async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  user_id = query.from_user.id
  user_data_store[user_id] = {}

  lang = "am" if query.data == "lang_am" else "en"
  user_data_store[user_id]["lang"] = lang

  if lang == "am":
    keyboard = [
        [
            InlineKeyboardButton("ወንድ (Male)", callback_data="gender_1"),
            InlineKeyboardButton("ሴት (Female)", callback_data="gender_0"),
        ]
    ]
    text = "እባክዎ ፆታዎን ይምረጡ:"
  else:
    keyboard = [
        [
            InlineKeyboardButton("Male", callback_data="gender_1"),
            InlineKeyboardButton("Female", callback_data="gender_0"),
        ]
    ]
    text = "Please select your gender:"

  reply_markup = InlineKeyboardMarkup(keyboard)
  await query.edit_message_text(text=text, reply_markup=reply_markup)


async def gender_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  user_id = query.from_user.id
  if user_id not in user_data_store:
    user_data_store[user_id] = {}

  gender = int(query.data.split("_")[1])
  user_data_store[user_id]["gender"] = gender
  user_data_store[user_id]["step"] = "waiting_age"

  await query.edit_message_text(
      text="እባክዎ ዕድሜዎን (በዓመት) ይጻፉ (ለምሳሌ: 47):"
  )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  text = update.message.text

  if user_id not in user_data_store or "step" not in user_data_store[user_id]:
    await update.message.reply_text("እባክዎ /start በመጫን ይጀምሩ።")
    return

  step = user_data_store[user_id]["step"]

  if step == "waiting_age":
    try:
      user_data_store[user_id]["age"] = float(text)
      user_data_store[user_id]["step"] = "waiting_height"
      await update.message.reply_text("እባክዎ ቁመትዎን (በሴንቲሜትር - cm) ይጻፉ:")
    except ValueError:
      await update.message.reply_text("እባክዎ ትክክለኛ ቁጥር ያስገቡ:")

  elif step == "waiting_height":
    try:
      user_data_store[user_id]["height"] = float(text)
      user_data_store[user_id]["step"] = "waiting_weight"
      await update.message.reply_text("እባክዎ ክብደትዎን (በኪሎግራም - kg) ይጻፉ:")
    except ValueError:
      await update.message.reply_text("እባክዎ ትክክለኛ ቁጥር ያስገቡ:")

  elif step == "waiting_weight":
    try:
      user_data_store[user_id]["weight"] = float(text)
      user_data_store[user_id]["step"] = "waiting_waist"
      await update.message.reply_text(
          "እባክዎ የወገብ ዙሪያዎን በሴንቲሜትር (cm) ይጻፉ (ለምሳሌ: 88):"
      )
    except ValueError:
      await update.message.reply_text("እባክዎ ትክክለኛ ቁጥር ያስገቡ:")

  elif step == "waiting_waist":
    try:
      user_data_store[user_id]["waist"] = float(text)
      data = user_data_store[user_id]

      age = data["age"]
      height = data["height"]
      weight = data["weight"]
      waist = data["waist"]

      h_m = height / 100
      bmi = weight / (h_m**2)
      whtr = waist / height

      if bmi < 18.5:
        bmi_status = "Underweight (ዝቅተኛ ክብደት)"
      elif 18.5 <= bmi < 25:
        bmi_status = "🟢 Healthy range (መደበኛ/ጤናማ ልክ)"
      elif 25 <= bmi < 30:
        bmi_status = "🟡 Overweight (ከመጠን በላይ ውፍረት)"
      else:
        bmi_status = "🔴 Obese (ውፍረት)"

      if whtr > 0.5:
        whtr_status = (
            "🔴 Higher central-fat risk (ከፍተኛ የወገብ ስብ እና የጤና ስጋት)"
        )
      else:
        whtr_status = "🟢 Low risk (መደበኛ እና ጤናማ)"

      assessment_report = (
          f"📋 **የአዲስ ጤና ማጣሪያ ውጤት (Health Assessment)**\n\n"
          f"👤 **የገቡት መረጃዎች:**\n"
          f"• ዕድሜ: `{int(age)}` | ቁመት: `{h_m:.2f} m`\n"
          f"• ክብደት: `{weight} kg` | ወገብ: `{waist} cm`\n\n"
          f"⚖️ **BMI ውጤት:**\n"
          f"• ነጥብ: `{bmi:.1f} kg/m²`\n"
          f"• ሁኔታ: {bmi_status}\n\n"
          f"📐 **የወገብና ቁመት ጥምርታ (WHtR):**\n"
          f"• ጥምርታ: `{whtr:.2f}` — {whtr_status}\n\n"
          f"⚠️ **የጤና ስጋት ትንተና:**\n"
          f"• የስኳር (Type 2) እና የልብ ስጋት: "
          f"{'ከፍተኛ 🔴' if whtr > 0.5 or bmi >= 25 else 'ዝቅተኛ 🟢'}\n\n"
          f"📌 **ማሳሰቢያ:**\n"
          f"ይህ የመጀመሪያ ደረጃ ማጣሪያ እንጂ የህክምና ትዕዛዝ አይደለም።"
      )

      user_data_store[user_id] = {}
      await update.message.reply_text(
          assessment_report, parse_mode="Markdown"
      )

    except ValueError:
      await update.message.reply_text("እባክዎ ትክክለኛ ቁጥር ያስገቡ:")


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(
      CallbackQueryHandler(language_handler, pattern="^lang_")
  )
  app.add_handler(CallbackQueryHandler(gender_handler, pattern="^gender_"))
  app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

  print("Addis Wellness Free Assessment Bot is running...")
  app.run_polling()


if __name__ == "__main__":
  main()
