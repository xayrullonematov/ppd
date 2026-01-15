"""
PDD Test Bot - Main entry point (FIXED VERSION)
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
from handlers.user import start, test_command, stats_command, review_command, help_command
from handlers.admin import admin_command, handle_admin_message, broadcast_command
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

from handlers.leaderboard import (
    leaderboard_command,
    show_leaderboard,
    show_my_rank,
    share_rank_certificate
)
from handlers.badges import (
    badges_command,
    show_all_badges,
    show_my_badges
)
# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Track last message IDs for cleanup
user_last_messages = {}

async def cleanup_old_message(chat_id: int, message_id: int):
    """Delete old message if it exists"""
    try:
        from telegram import Bot
        bot = Bot(token=config.TOKEN)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass  # Message already deleted or doesn't exist

# Callback query router
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route callback queries to appropriate handlers"""
    from handlers.user import start  # Import here to avoid circular import
    
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    chat_id = query.message.chat_id

    # Exam mode callbacks
    if data == "exam_start":
        await start_exam(update, context)
        return
    # Leaderboard callbacks
    elif data == "menu_leaderboard" or data == "leaderboard_menu":
        await leaderboard_command(update, context)
        return

    elif data == "leaderboard_weekly":
        await show_leaderboard(update, context, 'weekly')
        return

    elif data == "leaderboard_monthly":
        await show_leaderboard(update, context, 'monthly')
        return

    elif data == "leaderboard_alltime":
        await show_leaderboard(update, context, 'alltime')
        return

    elif data == "share_rank_cert":
        await share_rank_certificate(update, context)
        return

    elif data == "leaderboard_myrank":
        await show_my_rank(update, context)
        return

    elif data == "menu_badges":
        await badges_command(update, context)
        return

    elif data == "badges_my":

        await show_my_badges(update, context)
        return

     # Badge callbacks


    elif data == "badges_all":
        await show_all_badges(update, context)
        return


    elif data == "exam_cancel":
        # Cancel and go back to main menu
        await query.answer()
        await query.message.delete()
        
        # Send fresh start menu directly
        class FakeUpdate:
            def __init__(self, user, chat):
                self.effective_user = user
                self.message = FakeMessage(chat, user)
        
        class FakeMessage:
            def __init__(self, chat, user):
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                return await self.chat.send_message(text=text, **kwargs)
        
        fake_update = FakeUpdate(query.from_user, query.message.chat)
        await start(fake_update, context)
        return

    # Check if user is in exam mode - priority handling
    if has_active_exam(user_id):
        if data.startswith("answer_"):
            answer_index = int(data.split("_")[1])
            await handle_exam_answer(update, context, answer_index)
            return

    # Menu navigation callbacks
    elif data == "menu_back":
        await query.answer()
        await query.message.delete()
        
        # Send fresh start menu
        class FakeUpdate:
            def __init__(self, user, chat):
                self.effective_user = user
                self.message = FakeMessage(chat, user)
        
        class FakeMessage:
            def __init__(self, chat, user):
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                return await self.chat.send_message(text=text, **kwargs)
        
        fake_update = FakeUpdate(query.from_user, query.message.chat)
        await start(fake_update, context)
        return
    
    elif data == "menu_test":
        await query.answer()
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = get_category_keyboard()
        # Convert to list and add back button
        keyboard_list = list(keyboard.inline_keyboard)
        keyboard_list.append([
            InlineKeyboardButton("◀️ Bosh menyu", callback_data="menu_back")
        ])
        new_keyboard = InlineKeyboardMarkup(keyboard_list)
        await query.edit_message_text(
            "📚 Qaysi bo'limdan test topshirmoqchisiz?",
            reply_markup=new_keyboard
        )
        return
    
    elif data == "menu_exam":
        await query.answer()
        await exam_command(update, context)
        return
    
    elif data == "menu_review":
        await query.answer()
        await review_command(update, context)
        return
    
    elif data == "menu_stats":
        await query.answer()
        await stats_command(update, context)
        return
    
    elif data == "menu_admin":
        await query.answer()
        await query.message.delete()
        
        class FakeUpdate:
            def __init__(self, user, chat):
                self.effective_user = user
                self.message = FakeMessage(chat, user)
        
        class FakeMessage:
            def __init__(self, chat, user):
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                return await self.chat.send_message(text=text, **kwargs)
        
        fake_update = FakeUpdate(query.from_user, query.message.chat)
        await admin_command(fake_update, context)
        return
    
    elif data == "menu_help":
        await query.answer()
        await help_command(update, context)
        return

    # Regular test callbacks
    if data.startswith("start_"):
        category = data.replace("start_", "")
        await start_test(update, context, category)

    elif data.startswith("answer_"):
        answer_index = int(data.split("_")[1])
        # Track message for cleanup
        if user_id in user_last_messages:
            await cleanup_old_message(chat_id, user_last_messages[user_id])
        await handle_answer(update, context, answer_index)

    elif data == "back_to_categories":
        await query.answer()
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = get_category_keyboard()
        keyboard_list = list(keyboard.inline_keyboard)
        keyboard_list.append([
            InlineKeyboardButton("◀️ Bosh menyu", callback_data="menu_back")
        ])
        new_keyboard = InlineKeyboardMarkup(keyboard_list)
        await query.edit_message_text(
            "📚 Qaysi bo'limdan test topshirmoqchisiz?",
            reply_markup=new_keyboard
        )

    elif data == "home":
        await query.answer()
        await query.message.delete()
        
        class FakeUpdate:
            def __init__(self, user, chat):
                self.effective_user = user
                self.message = FakeMessage(chat, user)
        
        class FakeMessage:
            def __init__(self, chat, user):
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                return await self.chat.send_message(text=text, **kwargs)
        
        fake_update = FakeUpdate(query.from_user, query.message.chat)
        await start(fake_update, context)

    # Admin tools callbacks
    elif data == "admin_tools":
        class FakeUpdate:
            def __init__(self, user, chat):
                self.effective_user = user
                self.message = FakeMessage(chat, user)
        
        class FakeMessage:
            def __init__(self, chat, user):
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                return await self.chat.send_message(text=text, **kwargs)
        
        fake_update = FakeUpdate(query.from_user, query.message.chat)
        await admin_tools_command(fake_update, context)

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
        await query.message.delete()
        
        class FakeUpdate:
            def __init__(self, user, chat):
                self.effective_user = user
                self.message = FakeMessage(chat, user)
        
        class FakeMessage:
            def __init__(self, chat, user):
                self.chat = chat
                self.from_user = user
                
            async def reply_text(self, text, **kwargs):
                return await self.chat.send_message(text=text, **kwargs)
        
        fake_update = FakeUpdate(query.from_user, query.message.chat)
        await admin_command(fake_update, context)

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
        elif state['action'] == 'broadcast':
            from handlers.admin import handle_broadcast_message
            await handle_broadcast_message(update, context)
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
    application.add_handler(CommandHandler("exam", exam_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("review", review_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("tools", admin_tools_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("badges", badges_command))

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
    logger.info("📢 Broadcast yoqilgan!")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
