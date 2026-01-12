from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
import asyncio
from database import get_total_count, get_category_stats, load_questions
from utils.keyboards import get_category_keyboard
from user_stats import get_user_stats, get_wrong_questions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with main menu"""
    user_id = update.effective_user.id
    is_admin = (user_id == config.ADMIN_ID)
    
    # Get stats
    total = get_total_count()
    user_stats = get_user_stats(user_id)
    wrong_count = len(get_wrong_questions(user_id))
    
    # Get badges (first 3)
    badge_display = ""
    try:
        from handlers.badges import get_user_badges
        badges = get_user_badges(user_id)
        if badges:
            badge_display = " ".join([b['emoji'] for b in badges[:3]])
            if len(badges) > 3:
                badge_display += f" +{len(badges)-3}"
            badge_display = f"\n🏅 {badge_display}"
    except:
        pass
    
    # Get rank
    rank_display = ""
    try:
        from handlers.leaderboard import get_user_rank
        rank, _ = get_user_rank(user_id, 'alltime')
        if rank > 0 and rank <= 10:
            rank_display = f"\n🏆 Reyting: #{rank}"
    except:
        pass
    
    # Main welcome text
    text = (
        "🚗 <b>PDD Test Bot</b>\n\n"
        "Haydovchilik guvohnomasini olish uchun\n"
        "eng yaxshi tayyorgarlik dasturi!\n\n"
        f"📊 <b>{total} ta savol</b> bazada"
        f"{badge_display}"
        f"{rank_display}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🎯 ASOSIY FUNKSIYALAR</b>\n\n"
        "📝 <b>Test topshirish</b>\n"
        "   Kategoriya tanlang va mashq qiling\n\n"
        "🔥 <b>Imtihon rejimi</b>\n"
        "   Haqiqiy imtihon kabi vaqt bilan\n\n"
        "🏆 <b>Reytingi</b>\n"
        "   Eng yaxshi o'quvchilar ro'yxati\n\n"
        "🏅 <b>Nishonlar</b>\n"
        "   O'z yutuqlaringizni ko'ring\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 Quyidagi tugmalardan birini tanlang"
    )
    
    # Build keyboard
    keyboard = [
        [InlineKeyboardButton("📝 Test boshlash", callback_data="menu_test")],
        [InlineKeyboardButton("🔥 Imtihon rejimi", callback_data="menu_exam")],
    ]
    
    # Only show review if user has wrong answers
    if wrong_count > 0:
        keyboard.append([InlineKeyboardButton(
            f"🔄 Xato javoblar ({wrong_count})", 
            callback_data="menu_review"
        )])
    
    # Leaderboard and badges
    keyboard.append([
        InlineKeyboardButton("🏆 Reytingi", callback_data="menu_leaderboard"),
        InlineKeyboardButton("🏅 Nishonlar", callback_data="menu_badges")
    ])
    
    # Only show stats if user has taken tests
    if user_stats['tests_taken'] > 0:
        keyboard.append([InlineKeyboardButton(
            "📊 Statistika", 
            callback_data="menu_stats"
        )])
    
    # Admin button
    if is_admin:
        keyboard.append([InlineKeyboardButton("🔐 Admin", callback_data="menu_admin")])
    
    # Add help button
    keyboard.append([InlineKeyboardButton("ℹ️ Yordam", callback_data="menu_help")])
    
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
