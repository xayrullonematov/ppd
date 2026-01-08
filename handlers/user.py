"""
User-facing commands and test logic
"""

from telegram import Update
from telegram.ext import ContextTypes
import config
from database import get_total_count, get_category_stats
from utils.keyboards import get_category_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    is_admin = (user_id == config.ADMIN_ID)
    
    stats = get_category_stats()
    total = get_total_count()
    
    text = (
        "🚗 Salom! PDD test botiga xush kelibsiz!\n\n"
        f"📊 Bazada {total} ta savol:\n"
    )
    
    for letter, cat_info in config.CATEGORIES.items():
        if cat_info['id'] != 'mixed':
            count = stats.get(cat_info['id'], 0)
            text += f"{cat_info['emoji']} {cat_info['name']}: {count} ta\n"
    
    text += "\n/test - Test boshlash"
    
    if is_admin:
        text += "\n\n🔐 Admin: /admin"
    
    await update.message.reply_text(text)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command - show category selection"""
    total = get_total_count()
    
    if total == 0:
        await update.message.reply_text("❌ Hozircha savollar yo'q.")
        return
    
    keyboard = get_category_keyboard()
    
    await update.message.reply_text(
        "📚 Qaysi bo'limdan test topshirmoqchisiz?",
        reply_markup=keyboard
    )
