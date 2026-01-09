from telegram import Update
from telegram.ext import ContextTypes
import config
from database import get_total_count, get_category_stats, load_questions
from utils.keyboards import get_category_keyboard
from user_stats import get_user_stats, get_wrong_questions

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

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    
    if stats['tests_taken'] == 0:
        await update.message.reply_text(
            "📊 Sizda hali statistika yo'q.\n\n"
            "/test buyrug'i bilan test boshlang!"
        )
        return
    
    # Calculate overall percentage
    if stats['total_questions'] > 0:
        overall = round((stats['correct_answers'] / stats['total_questions']) * 100, 1)
    else:
        overall = 0
    
    # Find best score
    best_score = 0
    if stats['test_history']:
        best_score = max(t['percentage'] for t in stats['test_history'])
    
    text = (
        f"📊 Sizning statistikangiz:\n\n"
        f"Jami testlar: {stats['tests_taken']}\n"
        f"Jami savollar: {stats['total_questions']}\n"
        f"To'g'ri javoblar: {stats['correct_answers']}\n"
        f"O'rtacha ball: {overall}%\n"
        f"Eng yaxshi natija: {best_score}%\n"
        f"Xato javoblar: {len(stats['wrong_questions'])}\n\n"
    )
    
    # Category breakdown
    if stats['category_stats']:
        text += "📈 Kategoriya bo'yicha:\n"
        for cat_id, cat_stats in stats['category_stats'].items():
            cat_info = next(
                (c for c in config.CATEGORIES.values() if c['id'] == cat_id),
                None
            )
            if cat_info and cat_stats['total'] > 0:
                pct = round((cat_stats['correct'] / cat_stats['total']) * 100, 1)
                text += f"{cat_info['emoji']} {cat_info['name']}: {pct}% ({cat_stats['correct']}/{cat_stats['total']})\n"
    
    if len(stats['wrong_questions']) > 0:
        text += f"\n💡 /review - Xato javoblarni qayta ishlash"
    
    await update.message.reply_text(text)

async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start review mode with wrong answers"""
    user_id = update.effective_user.id
    wrong_ids = get_wrong_questions(user_id)
    
    if not wrong_ids:
        await update.message.reply_text(
            "✅ Sizda xato javoblar yo'q!\n\n"
            "Barcha savollarga to'g'ri javob bergansiz. Ajoyib! 🎉"
        )
        return
    
    # Get wrong questions
    all_questions = load_questions()
    wrong_questions = [q for q in all_questions if q['id'] in wrong_ids]
    
    if not wrong_questions:
        await update.message.reply_text("❌ Xato javoblar topilmadi.")
        return
    
    # Start review test with wrong questions
    from handlers.test import user_sessions, send_question
    from database import get_random_questions
    import random
    
    # Shuffle wrong questions
    shuffled = []
    for q in random.sample(wrong_questions, len(wrong_questions)):
        shuffled_q = q.copy()
        options_with_correct = [
            (opt, i == q['correct_index']) 
            for i, opt in enumerate(q['options'])
        ]
        random.shuffle(options_with_correct)
        shuffled_q['shuffled_options'] = [opt for opt, _ in options_with_correct]
        shuffled_q['shuffled_correct_index'] = next(
            i for i, (_, is_correct) in enumerate(options_with_correct) if is_correct
        )
        shuffled.append(shuffled_q)
    
    user_sessions[user_id] = {
        'questions': shuffled,
        'current': 0,
        'correct': 0,
        'category': 'review'
    }
    
    await update.message.reply_text(
        f"🔄 Xato javoblarni qayta ishlash\n\n"
        f"📚 Savollar: {len(shuffled)} ta\n"
        f"💡 Bu savollar sizda xato javoblar\n\n"
        f"Omad! 🍀"
    )
    
    await send_question(update, context, user_id)
