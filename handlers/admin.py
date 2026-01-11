"""
Admin commands for adding questions (WITH BROADCAST)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import add_question, get_category_stats, get_total_count
from utils.parser import parse_question_caption

# Import broadcast functions
from handlers.broadcast import broadcast_command, handle_broadcast_message, broadcast_state

# Store pending questions waiting for answer + category
pending_admin_questions = {}

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    user_id = update.effective_user.id
    
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q")
        return
    
    stats = get_category_stats()
    total = get_total_count()
    
    stats_text = "\n".join([
        f"{cat_info['emoji']} {cat_info['name']}: {stats.get(cat_info['id'], 0)}"
        for cat_info in config.CATEGORIES.values()
        if cat_info['id'] != 'mixed'
    ])
    
    # Get user count for broadcast
    from user_stats import load_stats
    user_count = len(load_stats())
    
    # Admin tools buttons
    keyboard = [
        [InlineKeyboardButton("🔧 Admin asboblari", callback_data="admin_tools")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")]
    ]
    
    message_text = (
        f"🔐 <b>Admin panel</b>\n\n"
        f"📊 <b>Statistika:</b>\n{stats_text}\n\n"
        f"Jami savollar: {total}\n"
        f"👥 Foydalanuvchilar: {user_count}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>Savol qo'shish:</b>\n\n"
        f"Rasm yoki matn yuboring:\n"
        f"<code>"
        f"Savol matni?\n\n"
        f"A) Javob 1\n"
        f"B) Javob 2\n"
        f"C) Javob 3\n"
        f"D) Javob 4\n\n"
        f"---\n\n"
        f"Tushuntirish"
        f"</code>\n\n"
        f"Keyin bot so'raydi:\n"
        f"To'g'ri javob va kategoriya?\n\n"
        f"Siz javob berasiz:\n"
        f"<code>0 a</code> - Birinchi javob to'g'ri, Belgilar\n"
        f"<code>2 d</code> - Uchinchi javob to'g'ri, Aralash\n\n"
        f"<b>Kategoriyalar:</b>\n"
        f"a = 🚦 Belgilar\n"
        f"b = 🚗 Qoidalar\n"
        f"c = ⚡ Tezlik\n"
        f"d = 🧠 Aralash\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔧 /tools - Tahrirlash, o'chirish, qidirish\n"
        f"📢 /broadcast - Hammaga xabar yuborish"
    )
    
    # Check if this is from callback or message
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            message_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from admin"""
    user_id = update.effective_user.id
    
    if user_id != config.ADMIN_ID:
        return
    
    # Check if in broadcast mode
    if user_id in broadcast_state:
        await handle_broadcast_message(update, context)
        return
    
    # Check if replying with answer + category
    if user_id in pending_admin_questions:
        response = update.message.text.strip()
        
        # Parse "0 a" or "2 d" format
        parts = response.split()
        
        if len(parts) != 2:
            await update.message.reply_text(
                "❌ Format: <code>0 a</code> (javob_raqami kategoriya)\n"
                "Masalan: <code>0 a</code> yoki <code>2 d</code>",
                parse_mode='HTML'
            )
            return
        
        try:
            answer_index = int(parts[0])
            category_letter = parts[1].lower()
            
            if answer_index not in [0, 1, 2, 3]:
                await update.message.reply_text("❌ Javob raqami 0, 1, 2 yoki 3 bo'lishi kerak")
                return
            
            if category_letter not in config.CATEGORIES:
                await update.message.reply_text(
                    "❌ Kategoriya a, b, c yoki d bo'lishi kerak\n"
                    "a=Belgilar, b=Qoidalar, c=Tezlik, d=Aralash"
                )
                return
            
            # Get pending question
            pending_q = pending_admin_questions[user_id]
            pending_q['correct_index'] = answer_index
            pending_q['category'] = config.get_category_id(category_letter)
            
            # Save to database
            question_id = add_question(pending_q)
            
            # Show confirmation
            cat_name = config.get_category_name(category_letter)
            
            preview = (
                f"✅ <b>Savol #{question_id} qo'shildi!</b>\n\n"
                f"📚 {cat_name}\n\n"
                f"❓ {pending_q['question']}\n\n"
            )
            
            for i, opt in enumerate(pending_q['options']):
                prefix = "✅" if i == answer_index else "   "
                preview += f"{prefix} {chr(65+i)}) {opt}\n"
            
            preview += f"\n💡 {pending_q['explanation']}\n\n"
            preview += f"📊 Jami: {get_total_count()} ta savol"
            
            await update.message.reply_text(preview, parse_mode='HTML')
            
            # Clean up
            del pending_admin_questions[user_id]
            return
            
        except ValueError:
            await update.message.reply_text(
                "❌ Format: <code>0 a</code> (raqam harf)", 
                parse_mode='HTML'
            )
            return
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {str(e)}")
            return
    
    # Parse new question
    caption = ""
    file_id = None
    
    try:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            caption = update.message.caption or ""
        elif update.message.text:
            caption = update.message.text
        else:
            return
        
        if not caption:
            await update.message.reply_text("❌ Matn yoki caption yo'q")
            return
        
        # Parse question
        parsed, error = parse_question_caption(caption)
        
        if error:
            await update.message.reply_text(error)
            return
        
        parsed['file_id'] = file_id
        
        # Show preview and ask for answer + category
        preview = (
            f"✅ <b>Savol qabul qilindi!</b>\n\n"
            f"❓ {parsed['question']}\n\n"
        )
        
        for i, opt in enumerate(parsed['options']):
            preview += f"{i}) {opt}\n"
        
        preview += (
            f"\n💡 {parsed['explanation']}\n\n"
            f"❔ <b>To'g'ri javob va kategoriya?</b>\n\n"
            f"Format: <code>javob_raqami kategoriya</code>\n"
            f"Masalan: <code>0 a</code> yoki <code>2 d</code>\n\n"
            f"a=🚦Belgilar b=🚗Qoidalar c=⚡Tezlik d=🧠Aralash"
        )
        
        pending_admin_questions[user_id] = parsed
        
        await update.message.reply_text(preview, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")

# Export broadcast functions
__all__ = ['admin_command', 'handle_admin_message', 'pending_admin_questions', 
           'broadcast_command', 'handle_broadcast_message']
