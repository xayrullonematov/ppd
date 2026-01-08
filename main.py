"""
PDD Test Bot - Main entry point
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import config
from handlers.user import start, test_command
from handlers.admin import admin_command, handle_admin_message
from handlers.test import start_test, handle_answer
from utils.keyboards import get_category_keyboard

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Callback query router
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route callback queries to appropriate handlers"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("start_"):
        # Start test with selected category
        category = data.replace("start_", "")
        await start_test(update, context, category)
    
    elif data.startswith("answer_"):
        # Handle answer selection
        answer_index = int(data.split("_")[1])
        await handle_answer(update, context, answer_index)
    
    elif data == "back_to_categories":
        # Show category menu again
        await query.answer()
        keyboard = get_category_keyboard()
        await query.edit_message_text(
            "📚 Qaysi bo'limdan test topshirmoqchisiz?",
            reply_markup=keyboard
        )
    
    elif data == "home":
        # Go back to home
        await query.answer()
        await query.message.reply_text(
            "🏠 Bosh sahifa\\n\\n/test - Yangi test boshlash"
        )

def main():
    """Start the bot"""
    
    # Create application
    application = Application.builder().token(config.TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Admin message handler (for adding questions)
    application.add_handler(MessageHandler(
        (filters.PHOTO | filters.TEXT) & ~filters.COMMAND,
        handle_admin_message
    ))
    
    # Start polling
    logger.info("✅ Bot ishga tushdi!")
    logger.info(f"📊 Admin ID: {config.ADMIN_ID}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

