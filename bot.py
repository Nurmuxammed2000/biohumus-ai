"""
BioHumus AI Telegram Bot
AI-powered soil / biohumus photo analysis bot.

Bot receives a soil photo from the user, sends it to Claude (vision model)
for analysis, and returns soil quality insights + biohumus recommendations.
"""

import os
import base64
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ANALYSIS_PROMPT = """You are a soil and biohumus (vermicompost) analysis expert.
Look at this soil photo and provide:
1. Soil texture and moisture assessment
2. Visible organic matter / biohumus quality signs
3. Any concerns (compaction, dryness, pests, poor structure)
4. 2-3 concrete recommendations to improve soil/biohumus quality

Keep the answer concise (under 150 words), practical, and farmer-friendly."""


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salem! Men BioHumus AI botpan.\n\n"
        "Maǵan topıraq súwretin jiberiń — men onı AI járdeminde analiz etip, "
        "sapası hám biohumus boyınsha usınıslar beremen. 🌱"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("🔍 Súwret analiz etilmekte...")

    try:
        # Get the highest-resolution version of the photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        image_b64 = base64.standard_b64encode(bytes(photo_bytes)).decode("utf-8")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": ANALYSIS_PROMPT},
                    ],
                }
            ],
        )

        analysis_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        await processing_msg.edit_text(f"🌱 *Analiz nátiyjesi:*\n\n{analysis_text}", parse_mode="Markdown")

    except Exception as e:
        logger.exception("Photo analysis failed")
        await processing_msg.edit_text(
            "❌ Ókinishke oray, súwretti analiz etiwde qátelik shıqtı. "
            "Basqa súwret penen qayta urınıp kóriń."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 Maǵan topıraq súwretin jiberiń — men onı analiz etemen."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("BioHumus AI bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
