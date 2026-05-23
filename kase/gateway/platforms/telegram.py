"""Telegram platform adapter."""

import logging

logger = logging.getLogger(__name__)


def run_telegram_bot(token: str, handler_fn):
    """Run a Telegram bot using python-telegram-bot."""
    try:
        from telegram.ext import Application, MessageHandler, filters
        
        app = Application.builder().token(token).build()
        
        async def handle_message(update, context):
            if not update.message or not update.message.text:
                return
            text = update.message.text
            chat_id = str(update.effective_chat.id)
            user_id = str(update.effective_user.id) if update.effective_user else ""
            response = handler_fn("telegram", chat_id, user_id, text)
            await update.message.reply_text(response)
        
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Telegram bot starting...")
        app.run_polling()
    except ImportError:
        logger.error("python-telegram-bot not installed. Install with: pip install kase[messaging]")
    except Exception as e:
        logger.error("Telegram bot error: %s", e)
