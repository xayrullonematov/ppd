from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
import asyncio
from database import get_total_count, get_category_stats, load_questions
from utils.keyboards import get_category_keyboard
from user_stats import get_user_stats, get_wrong_questions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with minimalist main menu"""
    user_id = update.effective_user.id
    is_admin = (user_id == config.ADMIN_ID)
    
    # Get stats
    total = get_total_count()
    user_stats = get_user_stats(user_id)
    wrong_count = len(get_wrong_questions(user_id))
    
    # Get badges count
    badge_count = 0
    try:
        from handlers.badges import get_user_badges
        badges = get_user_badges(user_id)
        badge_count = len(badges)
    except:
        pass
    
    # Get rank
    rank = 0
    try:
        from handlers.leaderboard import get_user_rank
        rank, _ = get_user_rank(user_id, 'alltime')
    except:
        pass
    
    # Minimalist welcome text
    text = (
        "🚗 <b>PDD Test Bot</b>\n"
        "Haydovchilik imtihoniga professional tayyorgarlik\n\n"
        f"📊 <b>{total}</b> ta savol bazada"
    )
    
    # Add user achievements if exists
    if user_stats['tests_taken'] > 0:
        text += f"\n🎯 {user_stats['accuracy']}% aniqlik"
    
    if badge_count > 0:
        text += f" | 🏅 {badge_count} nishon"
    
    if rank > 0 and rank <= 10:
        text += f" | 🏆 #{rank}"
    
    # Build minimalist keyboard
    keyboard = [
        [
            InlineKeyboardButton("📝 Test ishlash", callback_data="menu_test"),
            InlineKeyboardButton("🔥 Imtihon rejimi", callback_data="menu_exam")
        ]
    ]
    
    # Second row - conditional buttons
    second_row = []
    if wrong_count > 0:
        second_row.append(InlineKeyboardButton(f"🔄 Xato javoblar ({wrong_count})", callback_data="menu_review"))
    
    if second_row:
        keyboard.append(second_row)
    
    # Third row - Rankings and Badges
    keyboard.append([
        InlineKeyboardButton("🏆 Reyting", callback_data="menu_leaderboard"),
        InlineKeyboardButton("🏅 Nishonlar", callback_data="menu_badges")
    ])
    
    # Fourth row - Stats (only if user has activity)
    if user_stats['tests_taken'] > 0:
        keyboard.append([InlineKeyboardButton("📊 Statistika", callback_data="menu_stats")])
    
    # Admin and help buttons
    bottom_row = []
    if is_admin:
        bottom_row.append(InlineKeyboardButton("🔐 Admin", callback_data="menu_admin"))
    bottom_row.append(InlineKeyboardButton("ℹ️ Yordam", callback_data="menu_help"))
    
    if bottom_row:
        keyboard.append(bottom_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


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
    """Show user statistics with enhanced info"""
    user_id = update.effective_user.id
    stats = get_user_stats(user_id)
    
    if stats['tests_taken'] == 0:
        text = (
            "📊 <b>Statistika</b>\n\n"
            "Sizda hali statistika yo'q.\n\n"
            "Test topshirib, natijalaringizni kuzatishni boshlang!"
        )
        
        keyboard = [[InlineKeyboardButton("📝 Test boshlash", callback_data="menu_test")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        return
    
    # Get enhanced stats
    try:
        from user_stats import get_user_summary
        text = get_user_summary(user_id)
    except:
        # Fallback to basic stats
        if stats['total_questions'] > 0:
            overall = round((stats['correct_answers'] / stats['total_questions']) * 100, 1)
        else:
            overall = 0
        
        best_score = 0
        if stats['test_history']:
            best_score = max(t['percentage'] for t in stats['test_history'])
        
        avg_score = 0
        if stats['test_history']:
            avg_score = round(sum(t['percentage'] for t in stats['test_history']) / len(stats['test_history']), 1)
        
        text = (
            f"📊 <b>Sizning statistikangiz</b>\n\n"
            f"<b>Umumiy:</b>\n"
            f"Testlar: {stats['tests_taken']} ta\n"
            f"Savollar: {stats['total_questions']} ta\n"
            f"To'g'ri: {stats['correct_answers']} ta\n"
            f"O'rtacha ball: {avg_score}%\n"
            f"Eng yaxshi: {best_score}%\n"
            f"Xato javoblar: {len(stats['wrong_questions'])} ta\n\n"
        )
    
    # Category breakdown
    if stats['category_stats']:
        text += "<b>📈 Kategoriya bo'yicha:</b>\n"
        for cat_id, cat_stats in stats['category_stats'].items():
            cat_info = next(
                (c for c in config.CATEGORIES.values() if c['id'] == cat_id),
                None
            )
            if cat_info and cat_stats['total'] > 0:
                pct = round((cat_stats['correct'] / cat_stats['total']) * 100, 1)
                text += f"{cat_info['emoji']} {cat_info['name']}: {pct}% ({cat_stats['correct']}/{cat_stats['total']})\n"
    
    # Recent tests
    if stats['test_history']:
        text += "\n<b>📅 Oxirgi testlar:</b>\n"
        for test in stats['test_history'][-5:]:
            cat_info = next(
                (c for c in config.CATEGORIES.values() if c['id'] == test['category']),
                None
            )
            if cat_info:
                emoji = cat_info['emoji']
            else:
                emoji = "📝"
            text += f"{emoji} {test['score']}/{test['total']} ({test['percentage']}%)\n"
    
    keyboard = [
        [InlineKeyboardButton("📝 Test boshlash", callback_data="menu_test")],
        [
            InlineKeyboardButton("🏆 Reytingi", callback_data="menu_leaderboard"),
            InlineKeyboardButton("🏅 Nishonlar", callback_data="menu_badges")
        ],
        [InlineKeyboardButton("◀️ Bosh menyu", callback_data="menu_back")]
    ]
    
    if len(stats['wrong_questions']) > 0:
        keyboard.insert(1, [InlineKeyboardButton(
            f"🔄 Xato javoblar ({len(stats['wrong_questions'])})", 
            callback_data="menu_review"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start review mode with wrong answers - FIXED VERSION"""
    user_id = update.effective_user.id
    wrong_ids = get_wrong_questions(user_id)
    
    if not wrong_ids:
        text = (
            "✅ <b>Xato javoblar yo'q!</b>\n\n"
            "Barcha savollarga to'g'ri javob bergansiz. Ajoyib! 🎉\n\n"
            "Yangi testlar topshiring va ko'nikmalaringizni oshiring!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📝 Test boshlash", callback_data="menu_test")],
            [InlineKeyboardButton("◀️ Bosh menyu", callback_data="menu_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        return
    
    # Get wrong questions
    all_questions = load_questions()
    wrong_questions = [q for q in all_questions if q['id'] in wrong_ids]
    
    if not wrong_questions:
        await update.message.reply_text("❌ Xato javoblar topilmadi.")
        return
    
    # Start review test
    from handlers.test import user_sessions, send_question
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
    
    text = (
        f"🔄 <b>Xato javoblarni qayta ishlash</b>\n\n"
        f"📚 Savollar: {len(shuffled)} ta\n"
        f"💡 Bu savollar sizda xato javoblar\n\n"
        f"Omad! 🍀"
    )
    
    # Get the message object properly - FIXED!
    if update.callback_query:
        # Delete old message
        try:
            await update.callback_query.message.delete()
        except:
            pass
        
        # Send info message
        info_msg = await update.callback_query.message.chat.send_message(
            text, 
            parse_mode='HTML'
        )
        
        # Delete info after 2 seconds
        await asyncio.sleep(2)
        try:
            await info_msg.delete()
        except:
            pass
        
        # Send first question using the MESSAGE object (not Update!)
        await send_question(update.callback_query.message, context, user_id)
    else:
        # Send info message
        info_msg = await update.message.reply_text(text, parse_mode='HTML')
        
        # Delete info after 2 seconds
        await asyncio.sleep(2)
        try:
            await info_msg.delete()
        except:
            pass
        
        # Send first question using the MESSAGE object (not Update!)
        await send_question(update.message, context, user_id)

async def exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show exam mode (redirects to exam_mode.py)"""
    from handlers.exam_mode import exam_command as real_exam_command
    await real_exam_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    text = (
        "ℹ️ <b>Yordam</b>\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start - Bosh menyu\n"
        "/test - Test boshlash\n"
        "/exam - Imtihon rejimi\n"
        "/review - Xato javoblarni qayta ishlash\n"
        "/stats - Statistika\n"
        "/leaderboard - Reytingi\n"
        "/badges - Nishonlar\n"
        "/help - Yordam\n\n"
        "<b>Test haqida:</b>\n"
        "• Har bir testda 10 ta savol\n"
        "• Kategoriya bo'yicha tanlash mumkin\n"
        "• Javoblar tasodifiy tartibda\n"
        "• Noto'g'ri javoblar saqlanadi\n\n"
        "<b>Imtihon rejimi:</b>\n"
        "• 20 ta savol\n"
        "• 20 daqiqa vaqt\n"
        "• Haqiqiy imtihon kabi\n\n"
        "<b>Reytingi va Nishonlar:</b>\n"
        "• Haftalik, oylik, barcha vaqt reytingi\n"
        "• Ball tizimi: aniq va adolatli\n"
        "• 25+ yutuq nishonlari\n"
        "• Maxsus va afsonaviy nishonlar\n\n"
        "<b>Murojaat:</b>\n"
        "Savol yoki taklif bo'lsa: @mrxnm"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data="menu_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
