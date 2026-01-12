"""
Leaderboard System - Weekly, Monthly, All-time rankings
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.badge_images import generate_leaderboard_certificate
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

LEADERBOARD_FILE = 'leaderboard.json'

def load_leaderboard_data() -> Dict:
    """Load leaderboard data"""
    try:
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'weekly': {},
            'monthly': {},
            'alltime': {},
            'last_reset': {
                'weekly': datetime.now().isoformat(),
                'monthly': datetime.now().isoformat()
            }
        }
    except Exception as e:
        print(f"Error loading leaderboard: {e}")
        return {
            'weekly': {},
            'monthly': {},
            'alltime': {},
            'last_reset': {
                'weekly': datetime.now().isoformat(),
                'monthly': datetime.now().isoformat()
            }
        }

def save_leaderboard_data(data: Dict) -> None:
    """Save leaderboard data"""
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

def check_and_reset_periods(data: Dict) -> Dict:
    """Check if weekly/monthly periods need reset"""
    now = datetime.now()
    
    # Check weekly reset (every Monday)
    last_weekly = datetime.fromisoformat(data['last_reset']['weekly'])
    if now.weekday() == 0 and (now - last_weekly).days >= 7:
        data['weekly'] = {}
        data['last_reset']['weekly'] = now.isoformat()
    
    # Check monthly reset (first day of month)
    last_monthly = datetime.fromisoformat(data['last_reset']['monthly'])
    if now.day == 1 and now.month != last_monthly.month:
        data['monthly'] = {}
        data['last_reset']['monthly'] = now.isoformat()
    
    return data

def update_leaderboard(user_id: int, username: str, questions_solved: int, correct_answers: int, tests_taken: int) -> None:
    """Update leaderboard for all periods"""
    data = load_leaderboard_data()
    data = check_and_reset_periods(data)
    
    user_key = str(user_id)
    
    # Update all three periods
    for period in ['weekly', 'monthly', 'alltime']:
        if user_key not in data[period]:
            data[period][user_key] = {
                'user_id': user_id,
                'username': username,
                'questions_solved': 0,
                'correct_answers': 0,
                'tests_taken': 0,
                'accuracy': 0.0
            }
        
        user_data = data[period][user_key]
        user_data['username'] = username  # Update username
        user_data['questions_solved'] += questions_solved
        user_data['correct_answers'] += correct_answers
        user_data['tests_taken'] += tests_taken
        
        # Calculate accuracy
        if user_data['questions_solved'] > 0:
            user_data['accuracy'] = round(
                (user_data['correct_answers'] / user_data['questions_solved']) * 100, 1
            )
    
    save_leaderboard_data(data)

async def share_rank_certificate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send rank certificate"""
    query = update.callback_query
    await query.answer("Sertifikat tayyorlanmoqda...")
    
    user_id = update.effective_user.id
    
    # Get user rank and stats
    rank, stats = get_user_rank(user_id, 'alltime')
    
    if rank == 0:
        await query.message.reply_text(
            "❌ Avval test topshiring!\n\n"
            "Sertifikat olish uchun kamida bitta test tugatishingiz kerak."
        )
        return
    
    # Get username
    try:
        chat = await context.bot.get_chat(user_id)
        if chat.username:
            username = chat.username
        elif chat.first_name:
            username = chat.first_name
        else:
            username = f"User{user_id}"
    except:
        username = f"User{user_id}"
    
    # Generate certificate
    try:
        certificate = generate_leaderboard_certificate(
            rank=rank,
            username=username,
            points=stats['points'],
            correct=stats['correct_answers'],
            total=stats['questions_solved'],
            accuracy=stats['accuracy'],
            tests_taken=stats['tests_taken']
        )
        
        # Rank emoji
        if rank == 1:
            rank_emoji = "🥇"
        elif rank == 2:
            rank_emoji = "🥈"
        elif rank == 3:
            rank_emoji = "🥉"
        else:
            rank_emoji = f"#{rank}"
        
        caption = (
            f"🏆 <b>REYTINGI SERTIFIKATI</b>\n\n"
            f"{rank_emoji} <b>{rank}-o'rin</b>\n"
            f"📊 {stats['points']} ball\n\n"
            f"Do'stlaringiz bilan ulashing! 👆"
        )
        
        await query.message.reply_photo(
            photo=certificate,
            caption=caption,
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"Error generating rank certificate: {e}")
        await query.message.reply_text(
            f"❌ Sertifikat yaratishda xatolik: {str(e)}"
        )

# Update show_my_rank function to add share button
# Find the keyboard in show_my_rank and add this button:
keyboard = [
    [InlineKeyboardButton("📸 Sertifikat olish", callback_data="share_rank_cert")],
    [InlineKeyboardButton("📊 Reytingni ko'rish", callback_data="leaderboard_alltime")],
    [InlineKeyboardButton("◀️ Orqaga", callback_data="leaderboard_menu")]
]

def get_leaderboard(period: str = 'alltime', limit: int = 10) -> List[Dict]:
    """Get sorted leaderboard for a period"""
    data = load_leaderboard_data()
    data = check_and_reset_periods(data)
    
    if period not in data:
        return []
    
    # Convert to list and sort by points (weighted ranking)
    leaderboard = []
    for user_id, stats in data[period].items():
        # Calculate ranking points
        points = calculate_ranking_points(
            stats['questions_solved'],
            stats['correct_answers'],
            stats['tests_taken'],
            stats['accuracy']
        )
        
        leaderboard.append({
            'user_id': stats['user_id'],
            'username': stats['username'],
            'questions_solved': stats['questions_solved'],
            'correct_answers': stats['correct_answers'],
            'tests_taken': stats['tests_taken'],
            'accuracy': stats['accuracy'],
            'points': points
        })
    
    # Sort by points (descending)
    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    
    return leaderboard[:limit]

def calculate_ranking_points(questions: int, correct: int, tests: int, accuracy: float) -> int:
    """
    Calculate ranking points based on multiple factors
    
    Formula:
    - Correct answers: 10 points each
    - Test completion: 50 points each
    - Accuracy bonus: accuracy% * questions / 10
    - Activity bonus: sqrt(questions) * 5
    
    This ensures fair ranking considering both quantity and quality
    """
    import math
    
    # Base points from correct answers
    correct_points = correct * 10
    
    # Test completion bonus
    test_points = tests * 50
    
    # Accuracy bonus (rewards quality)
    accuracy_bonus = int((accuracy / 100) * questions * 0.5)
    
    # Activity bonus (rewards engagement, diminishing returns)
    activity_bonus = int(math.sqrt(questions) * 5)
    
    total_points = correct_points + test_points + accuracy_bonus + activity_bonus
    
    return total_points

def get_user_rank(user_id: int, period: str = 'alltime') -> Tuple[int, Dict]:
    """Get user's rank and stats in leaderboard"""
    leaderboard = get_leaderboard(period, limit=1000)  # Get full leaderboard
    
    for rank, user_stats in enumerate(leaderboard, 1):
        if user_stats['user_id'] == user_id:
            return rank, user_stats
    
    return 0, {}

def format_leaderboard_text(period: str, leaderboard: List[Dict], current_user_id: int = None) -> str:
    """Format leaderboard text with emoji medals"""
    period_names = {
        'weekly': '📅 Haftalik',
        'monthly': '📆 Oylik',
        'alltime': '🏆 Barcha vaqt'
    }
    
    text = f"<b>{period_names[period]} Reytingi</b>\n\n"
    
    if not leaderboard:
        text += "Hali hech kim test topshirmagan.\n\n"
        text += "Birinchi bo'ling! 🚀"
        return text
    
    # Medal emojis
    medals = ['🥇', '🥈', '🥉']
    
    for rank, user in enumerate(leaderboard[:10], 1):
        # Medal or rank number
        if rank <= 3:
            rank_symbol = medals[rank - 1]
        else:
            rank_symbol = f"{rank}."
        
        # Username (truncate if too long)
        username = user['username']
        if len(username) > 15:
            username = username[:12] + "..."
        
        # Highlight current user
        if current_user_id and user['user_id'] == current_user_id:
            username = f"<b>{username} (Siz)</b>"
        
        # Format line
        text += (
            f"{rank_symbol} {username}\n"
            f"   📊 {user['points']} ball | "
            f"✅ {user['correct_answers']}/{user['questions_solved']} | "
            f"🎯 {user['accuracy']}%\n\n"
        )
    
    return text

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard menu"""
    keyboard = [
        [InlineKeyboardButton("📅 Haftalik", callback_data="leaderboard_weekly")],
        [InlineKeyboardButton("📆 Oylik", callback_data="leaderboard_monthly")],
        [InlineKeyboardButton("🏆 Barcha vaqt", callback_data="leaderboard_alltime")],
        [InlineKeyboardButton("👤 Mening o'rnim", callback_data="leaderboard_myrank")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="menu_back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🏆 <b>Reytingi</b>\n\n"
        "Eng yaxshi o'quvchilar ro'yxati\n\n"
        "📊 <b>Ball tizimi:</b>\n"
        "• To'g'ri javob: 10 ball\n"
        "• Test tugatish: 50 ball\n"
        "• Aniqlik bonusi: Sifat uchun\n"
        "• Faollik bonusi: Muntazamlik uchun\n\n"
        "Qaysi reytingni ko'rmoqchisiz?"
    )
    
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

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str):
    """Show specific leaderboard period"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    leaderboard = get_leaderboard(period, limit=10)
    
    text = format_leaderboard_text(period, leaderboard, user_id)
    
    # Add user's rank if not in top 10
    rank, user_stats = get_user_rank(user_id, period)
    if rank > 10 and rank > 0:
        text += (
            f"\n━━━━━━━━━━━━━━━\n\n"
            f"<b>Sizning o'rningiz:</b>\n"
            f"{rank}. Siz\n"
            f"   📊 {user_stats['points']} ball | "
            f"✅ {user_stats['correct_answers']}/{user_stats['questions_solved']} | "
            f"🎯 {user_stats['accuracy']}%"
        )
    elif rank == 0:
        text += (
            f"\n━━━━━━━━━━━━━━━\n\n"
            f"<b>Sizning reytingingiz:</b>\n"
            f"Hali test topshirmadingiz.\n"
            f"Test topshiring va reytingga kiring! 🚀"
        )
    
    keyboard = [
        [
            InlineKeyboardButton("📅 Haftalik", callback_data="leaderboard_weekly"),
            InlineKeyboardButton("📆 Oylik", callback_data="leaderboard_monthly")
        ],
        [InlineKeyboardButton("🏆 Barcha vaqt", callback_data="leaderboard_alltime")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data=f"leaderboard_{period}")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="leaderboard_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_my_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's rank across all periods"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    text = "<b>👤 Sizning reytingingiz</b>\n\n"
    
    for period, name in [('weekly', '📅 Haftalik'), ('monthly', '📆 Oylik'), ('alltime', '🏆 Barcha vaqt')]:
        rank, stats = get_user_rank(user_id, period)
        
        if rank > 0:
            # Medal or rank
            if rank == 1:
                rank_text = "🥇 1-o'rin"
            elif rank == 2:
                rank_text = "🥈 2-o'rin"
            elif rank == 3:
                rank_text = "🥉 3-o'rin"
            else:
                rank_text = f"{rank}-o'rin"
            
            text += (
                f"<b>{name}</b>\n"
                f"📍 {rank_text}\n"
                f"📊 {stats['points']} ball\n"
                f"✅ {stats['correct_answers']}/{stats['questions_solved']} to'g'ri\n"
                f"🎯 {stats['accuracy']}% aniqlik\n"
                f"📝 {stats['tests_taken']} test\n\n"
            )
        else:
            text += (
                f"<b>{name}</b>\n"
                f"❌ Reytingda yo'qsiz\n\n"
            )
    
    keyboard = [
        [InlineKeyboardButton("📊 Reytingni ko'rish", callback_data="leaderboard_alltime")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="leaderboard_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# Export functions
__all__ = [
    'leaderboard_command',
    'show_leaderboard',
    'show_my_rank',
    'update_leaderboard',
    'get_user_rank',
    'get_leaderboard'
]
