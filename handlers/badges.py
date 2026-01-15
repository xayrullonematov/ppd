"""
Badge System - Achievement badges with improved UI and Telegraph integration
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.badge_images import generate_badge_certificate
from typing import Dict, List, Set
import json
from datetime import datetime

BADGES_FILE = 'user_badges.json'

# Badge definitions with requirements
BADGE_DEFINITIONS = {
    # Beginner badges
    'first_test': {
        'name': '🎯 Birinchi Test',
        'description': 'Birinchi testni tugatdingiz',
        'emoji': '🎯',
        'requirement': 'tests_taken >= 1'
    },
    'first_perfect': {
        'name': '💯 Mukammal',
        'description': 'Birinchi 100% natija',
        'emoji': '💯',
        'requirement': 'perfect_scores >= 1'
    },
    
    # Question badges
    'bronze_solver': {
        'name': '🥉 Bronza O\'quvchi',
        'description': '50 ta savolga javob berdingiz',
        'emoji': '🥉',
        'requirement': 'questions_solved >= 50'
    },
    'silver_solver': {
        'name': '🥈 Kumush O\'quvchi',
        'description': '200 ta savolga javob berdingiz',
        'emoji': '🥈',
        'requirement': 'questions_solved >= 200'
    },
    'gold_solver': {
        'name': '🥇 Oltin O\'quvchi',
        'description': '500 ta savolga javob berdingiz',
        'emoji': '🥇',
        'requirement': 'questions_solved >= 500'
    },
    'diamond_solver': {
        'name': '💎 Olmos O\'quvchi',
        'description': '1000 ta savolga javob berdingiz',
        'emoji': '💎',
        'requirement': 'questions_solved >= 1000'
    },
    
    # Test completion badges
    'bronze_tester': {
        'name': '🎓 Bronza Sinov',
        'description': '10 ta test tugatdingiz',
        'emoji': '🎓',
        'requirement': 'tests_taken >= 10'
    },
    'silver_tester': {
        'name': '🏅 Kumush Sinov',
        'description': '50 ta test tugatdingiz',
        'emoji': '🏅',
        'requirement': 'tests_taken >= 50'
    },
    'gold_tester': {
        'name': '🏆 Oltin Sinov',
        'description': '100 ta test tugatdingiz',
        'emoji': '🏆',
        'requirement': 'tests_taken >= 100'
    },
    
    # Accuracy badges
    'accurate': {
        'name': '🎯 Aniq',
        'description': '80% aniqlik (50+ savol)',
        'emoji': '🎯',
        'requirement': 'accuracy >= 80 and questions_solved >= 50'
    },
    'sharpshooter': {
        'name': '🏹 Nishonchi',
        'description': '90% aniqlik (100+ savol)',
        'emoji': '🏹',
        'requirement': 'accuracy >= 90 and questions_solved >= 100'
    },
    'sniper': {
        'name': '🎖️ Snayper',
        'description': '95% aniqlik (200+ savol)',
        'emoji': '🎖️',
        'requirement': 'accuracy >= 95 and questions_solved >= 200'
    },
    
    # Streak badges
    'week_warrior': {
        'name': '📅 Haftalik Jangchi',
        'description': '7 kun ketma-ket test topdingiz',
        'emoji': '📅',
        'requirement': 'daily_streak >= 7'
    },
    'month_master': {
        'name': '📆 Oylik Usta',
        'description': '30 kun ketma-ket test topdingiz',
        'emoji': '📆',
        'requirement': 'daily_streak >= 30'
    },
    
    # Exam badges
    'exam_passer': {
        'name': '🎓 Imtihonchi',
        'description': 'Imtihon rejimini o\'tdingiz',
        'emoji': '🎓',
        'requirement': 'exams_passed >= 1'
    },
    'exam_ace': {
        'name': '⭐ Imtihon Ustasi',
        'description': '5 ta imtihonni o\'tdingiz',
        'emoji': '⭐',
        'requirement': 'exams_passed >= 5'
    },
    
    # Speed badges
    'speed_demon': {
        'name': '⚡ Tez',
        'description': '10 ta testni 1 kunda tugatdingiz',
        'emoji': '⚡',
        'requirement': 'tests_in_day >= 10'
    },
    
    # Special badges
    'night_owl': {
        'name': '🦉 Tungi Qush',
        'description': 'Tunda (00:00-06:00) test topdingiz',
        'emoji': '🦉',
        'requirement': 'night_tests >= 1'
    },
    'early_bird': {
        'name': '🐦 Erta Qush',
        'description': 'Erta (05:00-07:00) test topdingiz',
        'emoji': '🐦',
        'requirement': 'early_tests >= 1'
    },
    'comeback': {
        'name': '🔥 Qaytish',
        'description': 'Barcha xato javoblarni to\'g\'riladingiz',
        'emoji': '🔥',
        'requirement': 'wrong_questions_corrected >= 10'
    },
    
    # Legendary badges
    'legend': {
        'name': '👑 Afsonaviy',
        'description': 'TOP-3 reytingda',
        'emoji': '👑',
        'requirement': 'top_rank <= 3'
    },
    'perfectionist': {
        'name': '💎 Perfektsionist',
        'description': '10 ta mukammal test (100%)',
        'emoji': '💎',
        'requirement': 'perfect_scores >= 10'
    }
}

# Telegraph page URL for all badges (you'll need to create this)
TELEGRAPH_ALL_BADGES_URL = "https://telegra.ph/PDD-Test-Bot---Barcha-Yutuq-Nishonlari-01-15"

def load_user_badges() -> Dict:
    """Load user badges"""
    try:
        with open(BADGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading badges: {e}")
        return {}

def save_user_badges(badges: Dict) -> None:
    """Save user badges"""
    try:
        with open(BADGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(badges, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving badges: {e}")

def check_and_award_badges(user_id: int, user_stats: Dict) -> List[str]:
    """
    Check if user earned any new badges
    Returns list of newly earned badge IDs
    """
    badges_data = load_user_badges()
    user_key = str(user_id)
    
    if user_key not in badges_data:
        badges_data[user_key] = {
            'earned_badges': [],
            'badge_dates': {}
        }
    
    user_badges = badges_data[user_key]
    newly_earned = []
    
    # Check each badge
    for badge_id, badge_def in BADGE_DEFINITIONS.items():
        # Skip if already earned
        if badge_id in user_badges['earned_badges']:
            continue
        
        # Evaluate requirement
        requirement = badge_def['requirement']
        
        # Build context for eval
        context = {
            'questions_solved': user_stats.get('total_questions', 0),
            'correct_answers': user_stats.get('correct_answers', 0),
            'tests_taken': user_stats.get('tests_taken', 0),
            'accuracy': user_stats.get('accuracy', 0),
            'perfect_scores': user_stats.get('perfect_scores', 0),
            'exams_passed': user_stats.get('exams_passed', 0),
            'daily_streak': user_stats.get('daily_streak', 0),
            'tests_in_day': user_stats.get('tests_in_day', 0),
            'night_tests': user_stats.get('night_tests', 0),
            'early_tests': user_stats.get('early_tests', 0),
            'wrong_questions_corrected': user_stats.get('wrong_questions_corrected', 0),
            'top_rank': user_stats.get('top_rank', 999)
        }
        
        try:
            if eval(requirement, {"__builtins__": {}}, context):
                # Award badge
                user_badges['earned_badges'].append(badge_id)
                user_badges['badge_dates'][badge_id] = datetime.now().isoformat()
                newly_earned.append(badge_id)
        except Exception as e:
            print(f"Error checking badge {badge_id}: {e}")
    
    if newly_earned:
        save_user_badges(badges_data)
    
    return newly_earned

def get_user_badges(user_id: int) -> List[Dict]:
    """Get all badges earned by user"""
    badges_data = load_user_badges()
    user_key = str(user_id)
    
    if user_key not in badges_data:
        return []
    
    user_badges = badges_data[user_key]['earned_badges']
    badge_dates = badges_data[user_key]['badge_dates']
    
    result = []
    for badge_id in user_badges:
        if badge_id in BADGE_DEFINITIONS:
            badge_info = BADGE_DEFINITIONS[badge_id].copy()
            badge_info['id'] = badge_id
            badge_info['earned_date'] = badge_dates.get(badge_id, 'Unknown')
            result.append(badge_info)
    
    return result

def get_badge_progress(user_stats: Dict) -> List[Dict]:
    """Get progress towards unearned badges"""
    badges_data = load_user_badges()
    user_id = user_stats.get('user_id', 0)
    user_key = str(user_id)
    
    earned_ids = []
    if user_key in badges_data:
        earned_ids = badges_data[user_key]['earned_badges']
    
    progress = []
    
    # Build context
    context = {
        'questions_solved': user_stats.get('total_questions', 0),
        'correct_answers': user_stats.get('correct_answers', 0),
        'tests_taken': user_stats.get('tests_taken', 0),
        'accuracy': user_stats.get('accuracy', 0),
        'perfect_scores': user_stats.get('perfect_scores', 0),
        'exams_passed': user_stats.get('exams_passed', 0),
        'daily_streak': user_stats.get('daily_streak', 0),
        'tests_in_day': user_stats.get('tests_in_day', 0),
        'night_tests': user_stats.get('night_tests', 0),
        'early_tests': user_stats.get('early_tests', 0),
        'wrong_questions_corrected': user_stats.get('wrong_questions_corrected', 0),
        'top_rank': user_stats.get('top_rank', 999)
    }
    
    for badge_id, badge_def in BADGE_DEFINITIONS.items():
        # Skip earned badges
        if badge_id in earned_ids:
            continue
        
        # Parse requirement to show progress
        req = badge_def['requirement']
        
        # Simple progress tracking for numeric requirements
        if 'questions_solved >=' in req:
            target = int(req.split('>=')[1].strip().split()[0])
            current = context['questions_solved']
            if current < target:
                progress.append({
                    'badge': badge_def,
                    'current': current,
                    'target': target,
                    'percentage': min(100, int((current / target) * 100))
                })
        
        elif 'tests_taken >=' in req:
            target = int(req.split('>=')[1].strip().split()[0])
            current = context['tests_taken']
            if current < target:
                progress.append({
                    'badge': badge_def,
                    'current': current,
                    'target': target,
                    'percentage': min(100, int((current / target) * 100))
                })
    
    # Sort by percentage (closest to completion first)
    progress.sort(key=lambda x: x['percentage'], reverse=True)
    
    return progress[:5]  # Return top 5 closest badges

async def badges_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show badges main menu"""
    user_id = update.effective_user.id
    
    # Get user badges
    badges = get_user_badges(user_id)
    badge_count = len(badges)
    total_badges = len(BADGE_DEFINITIONS)
    
    text = (
        "🏅 <b>Yutuq Nishonlari</b>\n\n"
        f"Sizda {badge_count}/{total_badges} ta nishon bor\n\n"
    )
    
    if badge_count > 0:
        # Show first 5 badges as preview
        text += "<b>So'nggi nishonlaringiz:</b>\n"
        for badge in badges[:5]:
            text += f"{badge['emoji']} {badge['name']}\n"
        
        if badge_count > 5:
            text += f"\n... va yana {badge_count - 5} ta nishon\n"
    else:
        text += "Hali nishonlaringiz yo'q.\nTest topshiring va yutuqlar qo'lga kiriting! 🎯"
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🎖️ Mening nishonlarim", callback_data="badges_my")],
        [InlineKeyboardButton("📜 Barcha nishonlar", url=TELEGRAPH_ALL_BADGES_URL)],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="menu_back")]
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

async def show_my_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's earned badges with shareable certificates"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user stats
    from user_stats import get_user_stats
    user_stats = get_user_stats(user_id)
    user_stats['user_id'] = user_id
    
    # Get badges
    badges = get_user_badges(user_id)
    
    if not badges:
        text = (
            "🏅 <b>Mening nishonlarim</b>\n\n"
            "Sizda hali nishonlar yo'q.\n\n"
            "Test topshiring va nishonlar yutib oling! 🎯"
        )
        
        keyboard = [
            [InlineKeyboardButton("📝 Test boshlash", callback_data="menu_test")],
            [InlineKeyboardButton("◀️ Orqaga", callback_data="menu_badges")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return
    
    # Sort badges by date (newest first)
    badges.sort(key=lambda x: x['earned_date'], reverse=True)
    
    text = (
        f"🏅 <b>Mening nishonlarim ({len(badges)})</b>\n\n"
        "<b>Sizning yutuqlaringiz:</b>\n\n"
    )
    
    # Group badges by rarity
    legendary = [b for b in badges if b['id'] in ['legend', 'perfectionist', 'diamond_solver']]
    rare = [b for b in badges if b['id'] in ['gold_solver', 'gold_tester', 'sniper', 'exam_ace', 'month_master']]
    common = [b for b in badges if b not in legendary and b not in rare]
    
    if legendary:
        text += "<b>👑 AFSONAVIY:</b>\n"
        for badge in legendary:
            date = badge['earned_date'][:10] if len(badge['earned_date']) > 10 else badge['earned_date']
            text += f"{badge['emoji']} {badge['name']} - {date}\n"
        text += "\n"
    
    if rare:
        text += "<b>⭐ KAMYOB:</b>\n"
        for badge in rare:
            date = badge['earned_date'][:10] if len(badge['earned_date']) > 10 else badge['earned_date']
            text += f"{badge['emoji']} {badge['name']} - {date}\n"
        text += "\n"
    
    if common:
        text += "<b>🎖️ ODDIY:</b>\n"
        for badge in common[:10]:  # Show max 10 common badges
            date = badge['earned_date'][:10] if len(badge['earned_date']) > 10 else badge['earned_date']
            text += f"{badge['emoji']} {badge['name']} - {date}\n"
        
        if len(common) > 10:
            text += f"\n... va yana {len(common) - 10} ta nishon\n"
    
    text += "\n💡 Har bir nishon uchun sertifikat olishingiz mumkin!"
    
    # Keyboard with share option
    keyboard = [
        [InlineKeyboardButton("📜 Barcha nishonlar", url=TELEGRAPH_ALL_BADGES_URL)],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="menu_badges")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_all_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redirect to Telegraph page"""
    query = update.callback_query
    await query.answer("Telegraph sahifasi ochilmoqda...")
    
    # This will be handled by the URL button in the keyboard

async def notify_new_badge(context: ContextTypes.DEFAULT_TYPE, user_id: int, badge_id: str):
    """Send notification with certificate image when user earns a new badge"""
    if badge_id not in BADGE_DEFINITIONS:
        return
    
    badge = BADGE_DEFINITIONS[badge_id]
    
    # Get username
    try:
        chat = await context.bot.get_chat(user_id)
        if chat.username:
            username = chat.username
        elif chat.first_name:
            username = chat.first_name
        else:
            username = f"User{user_id}"
    except Exception as e:
        print(f"Error getting username: {e}")
        username = f"User{user_id}"
    
    # Generate certificate image
    try:
        date_earned = datetime.now().strftime('%d.%m.%Y')
        certificate = generate_badge_certificate(
            badge_name=badge['name'],
            badge_emoji=badge['emoji'],
            username=username,
            date_earned=date_earned
        )
        
        # Caption text
        caption = (
            f"🎉 <b>YANGI YUTUQ!</b> 🎉\n\n"
            f"{badge['emoji']} <b>{badge['name']}</b>\n\n"
            f"{badge['description']}\n\n"
            f"Tabriklaymiz! Do'stlaringiz bilan ulashing! 👆"
        )
        
        # Send certificate image
        await context.bot.send_photo(
            chat_id=user_id,
            photo=certificate,
            caption=caption,
            parse_mode='HTML'
        )
        
        print(f"✅ Badge certificate sent to user {user_id}: {badge['name']}")
        
    except Exception as e:
        print(f"❌ Error sending badge certificate: {e}")
        # Fallback to text notification if image fails
        text = (
            f"🎉 <b>YANGI NISHON!</b> 🎉\n\n"
            f"{badge['emoji']} <b>{badge['name']}</b>\n\n"
            f"{badge['description']}\n\n"
            f"Tabriklaymiz! Davom eting! 🚀"
        )
        
        keyboard = [[InlineKeyboardButton("🏅 Mening nishonlarim", callback_data="badges_my")]]
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        except Exception as e2:
            print(f"Error sending fallback notification: {e2}")

# Export functions
__all__ = [
    'badges_command',
    'show_my_badges',
    'show_all_badges',
    'check_and_award_badges',
    'get_user_badges',
    'notify_new_badge',
    'BADGE_DEFINITIONS'
]
