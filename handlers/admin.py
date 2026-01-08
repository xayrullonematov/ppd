"""
Admin commands for adding questions
"""

from telegram import Update
from telegram.ext import ContextTypes
import config
from database import add_question, get_category_stats, get_total_count
from utils.parser import parse_question_caption

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
    
    await update.message.reply_text(
        f"🔐 Admin panel\n\n"
        f"📊 Statistika:\n{stats_text}\n\n"
        f"Jami: {total}\n\n"
        f"📝 Savol qo'shish:\n\n"
        f"Rasm yoki matn yuboring:\n"
        f"```\n"
        f"Savol matni?\n\n"
        f"A) Javob 1\n"
        f"B) Javob 2\n"
        f"C) Javob 3\n"
        f"D) Javob 4\n\n"
        f"---\n\n"
        f"Tushuntirish\n"
        f"```\n\n"
        f"Keyin bot so'raydi:\n"
        f"To'g'ri javob va kategoriya?\n\n"
        f"Siz javob berasiz:\n"
        f"`0 a` - Birinchi javob to'g'ri, Belgilar\n"
        f"`2 d` - Uchinchi javob to'g'ri, Aralash\n\n"
        f"Kategoriyalar:\n"
        f"a = 🚦 Belgilar\n"
        f"b = 🚗 Qoidalar\n"
        f"c = ⚡ Tezlik\n"
        f"d = 🧠 Aralash",
        parse_mode='Markdown'
    )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from admin"""
    user_id = update.effective_user.id
    
    if user_id != config.ADMIN_ID:
        return
    
    # Check if replying with answer + category
    if user_id in pending_admin_questions:
        response = update.message.text.strip()
        
        # Parse "0 a" or "2 d" format
        parts = response.split()
        
        if len(parts) != 2:
            await update.message.reply_text(
                "❌ Format: `0 a` (javob_raqami kategoriya)\n"
                "Masalan: `0 a` yoki `2 d`",
                parse_mode='Markdown'
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
            correct_option = pending_q['options'][answer_index]
            
            preview = (
                f"✅ Savol #{question_id} qo'shildi!\n\n"
                f"📚 {cat_name}\n\n"
                f"❓ {pending_q['question']}\n\n"
            )
            
            for i, opt in enumerate(pending_q['options']):
                prefix = "✅" if i == answer_index else "   "
                preview += f"{prefix} {chr(65+i)}) {opt}\n"
            
            preview += f"\n💡 {pending_q['explanation']}\n\n"
            preview += f"📊 Jami: {get_total_count()} ta savol"
            
            await update.message.reply_text(preview)
            
            # Clean up
            del pending_admin_questions[user_id]
            return
            
        except ValueError:
            await update.message.reply_text("❌ Format: `0 a` (raqam harf)", parse_mode='Markdown')
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
            f"✅ Savol qabul qilindi!\n\n"
            f"❓ {parsed['question']}\n\n"
        )
        
        for i, opt in enumerate(parsed['options']):
            preview += f"{i}) {opt}\n"
        
        preview += (
            f"\n💡 {parsed['explanation']}\n\n"
            f"❔ To'g'ri javob va kategoriya?\n\n"
            f"Format: `javob_raqami kategoriya`\n"
            f"Masalan: `0 a` yoki `2 d`\n\n"
            f"a=🚦Belgilar b=🚗Qoidalar c=⚡Tezlik d=🧠Aralash"
        )
        
        pending_admin_questions[user_id] = parsed
        
        await update.message.reply_text(preview, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")
