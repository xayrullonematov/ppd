"""
PDD Test Bot - Main entry point with Exam Mode
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
from handlers.user import start, test_command, stats_command, review_command
from handlers.admin import admin_command, handle_admin_message
from handlers.test import start_test, handle_answer, user_sessions
from handlers.admin_tools import (
    admin_tools_command,
    list_questions,
    show_question_detail,
    delete_question,
    edit_question_menu,
    start_edit_field,
    handle_admin_edit,
    search_questions,
    handle_search,
    detailed_stats,
    export_questions,
    admin_state
)
from handlers.exam_mode import (
    exam_command,
    start_exam,
    handle_exam_answer,
    cancel_exam,
    has_active_exam,
    exam_sessions
)
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
    user_id = update.effective_user.id
    
    # Exam mode callbacks
    if data == "exam_start":
        await start_exam(update, context)
        return
    
    elif data == "exam_cancel":
        await cancel_exam(update, context)
        return
    
    # Check if user is in exam mode - priority handling
    if has_active_exam(user_id):
        if data.startswith("answer_"):
            answer_index = int(data.split("_")[1])
            await handle_exam_answer(update, context, answer_index)
            return
    
    # Regular test callbacks
    if data.startswith("start_"):
        category = data.replace("start_", "")
        await start_test(update, context, category)
    
    elif data.startswith("answer_"):
        answer_index = int(data.split("_")[1])
        await handle_answer(update, context, answer_index)
    
    elif data == "back_to_categories":
        await query.answer()
        keyboard = get_category_keyboard()
        await query.edit_message_text(
            "📚 Qaysi bo'limdan test topshirmoqchisiz?",
            reply_markup=keyboard
        )
    
    elif data == "home":
        await query.answer()
        await query.message.reply_text(
            "🏠 Bosh sahifa\n\n"
            "/test - Mashq test\n"
            "/exam - Haqiqiy imtihon"
        )
    
    # Admin tools callbacks
    elif data == "admin_tools":
        await admin_tools_command(update, context)
    
    elif data == "admin_list":
        await list_questions(update, context, page=0)
    
    elif data.startswith("admin_list_page_"):
        page = int(data.split("_")[-1])
        await list_questions(update, context, page=page)
    
    elif data.startswith("admin_edit_") and not data.startswith("admin_edit_start_"):
        question_id = int(data.split("_")[2])
        await show_question_detail(update, context, question_id)
    
    elif data.startswith("admin_edit_start_"):
        question_id = int(data.split("_")[3])
        await edit_question_menu(update, context, question_id)
    
    elif data.startswith("admin_edit_question_"):
        question_id = int(data.split("_")[3])
        await start_edit_field(update, context, question_id, 'question')
    
    elif data.startswith("admin_edit_explanation_"):
        question_id = int(data.split("_")[3])
        await start_edit_field(update, context, question_id, 'explanation')
    
    elif data.startswith("admin_edit_correct_"):
        question_id = int(data.split("_")[3])
        await start_edit_field(update, context, question_id, 'correct')
    
    elif data.startswith("admin_edit_category_"):
        question_id = int(data.split("_")[3])
        await start_edit_field(update, context, question_id, 'category')
    
    elif data.startswith("admin_delete_confirm_"):
        question_id = int(data.split("_")[3])
        await delete_question(update, context, question_id, confirmed=False)
    
    elif data.startswith("admin_delete_yes_"):
        question_id = int(data.split("_")[3])
        await delete_question(update, context, question_id, confirmed=True)
    
    elif data == "admin_search":
        await search_questions(update, context)
    
    elif data == "admin_detailed_stats":
        await detailed_stats(update, context)
    
    elif data == "admin_export":
        await export_questions(update, context)
    
    elif data == "admin_back":
        await admin_command(update, context)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (for admin edits and searches)"""
    user_id = update.effective_user.id
    
    # Check if admin is in edit/search mode
    if user_id in admin_state:
        state = admin_state[user_id]
        
        if state['action'] == 'edit_field':
            await handle_admin_edit(update, context)
            return
        elif state['action'] == 'search':
            await handle_search(update, context)
            return
    
    # Otherwise, handle as normal admin message (adding questions)
    await handle_admin_message(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current admin operation"""
    user_id = update.effective_user.id
    
    if user_id in admin_state:
        del admin_state[user_id]
        await update.message.reply_text("✅ Amal bekor qilindi.")
    else:
        await update.message.reply_text("Hech qanday amal bajarilmayapti.")

def main():
    """Start the bot"""
    
    # Create application
    application = Application.builder().token(config.TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("exam", exam_command))  # NEW!
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("review", review_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("tools", admin_tools_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(
        filters.PHOTO & ~filters.COMMAND,
        handle_admin_message
    ))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_messages
    ))
    
    # Start polling
    logger.info("✅ Bot ishga tushdi!")
    logger.info(f"📊 Admin ID: {config.ADMIN_ID}")
    logger.info("🔧 Admin tools yoqilgan!")
    logger.info("🎓 Exam mode yoqilgan!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
