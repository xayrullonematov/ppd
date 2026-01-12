"""
Enhanced User statistics with leaderboard and badge integration
"""

import json
from typing import Dict, List, Set
from datetime import datetime, date

STATS_FILE = 'user_stats.json'

def load_stats() -> Dict:
    """Load user statistics"""
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading stats: {e}")
        return {}

def save_stats(stats: Dict) -> None:
    """Save user statistics"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")

def initialize_user_stats(user_id: int) -> Dict:
    """Initialize stats structure for new user"""
    return {
        'tests_taken': 0,
        'total_questions': 0,
        'correct_answers': 0,
        'wrong_questions': [],
        'category_stats': {},
        'test_history': [],
        'perfect_scores': 0,
        'exams_passed': 0,
        'exams_taken': 0,
        'daily_streak': 0,
        'last_activity_date': None,
        'tests_today': 0,
        'tests_in_day': 0,
        'night_tests': 0,
        'early_tests': 0,
        'wrong_questions_corrected': 0,
        'accuracy': 0.0
    }

def record_answer(user_id: int, question_id: int, is_correct: bool, category: str) -> None:
    """Record user's answer and update leaderboard"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        stats[user_key] = initialize_user_stats(user_id)
    
    user_stats = stats[user_key]
    user_stats['total_questions'] += 1
    
    # Track corrections
    if is_correct and question_id in user_stats['wrong_questions']:
        user_stats['wrong_questions_corrected'] = user_stats.get('wrong_questions_corrected', 0) + 1
    
    if is_correct:
        user_stats['correct_answers'] += 1
        # Remove from wrong questions if previously failed
        if question_id in user_stats['wrong_questions']:
            user_stats['wrong_questions'].remove(question_id)
    else:
        # Add to wrong questions if not already there
        if question_id not in user_stats['wrong_questions']:
            user_stats['wrong_questions'].append(question_id)
    
    # Update category stats
    if category not in user_stats['category_stats']:
        user_stats['category_stats'][category] = {
            'total': 0,
            'correct': 0
        }
    
    user_stats['category_stats'][category]['total'] += 1
    if is_correct:
        user_stats['category_stats'][category]['correct'] += 1
    
    # Calculate accuracy
    if user_stats['total_questions'] > 0:
        user_stats['accuracy'] = round(
            (user_stats['correct_answers'] / user_stats['total_questions']) * 100, 1
        )
    
    save_stats(stats)

async def record_test_completion(user_id: int, category: str, score: int, total: int, context=None) -> None:
    """Record completed test and update leaderboard/badges"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        stats[user_key] = initialize_user_stats(user_id)
    
    user_stats = stats[user_key]
    user_stats['tests_taken'] += 1
    
    # Track time-based tests
    now = datetime.now()
    hour = now.hour
    
    if 0 <= hour < 6:
        user_stats['night_tests'] = user_stats.get('night_tests', 0) + 1
    elif 5 <= hour < 7:
        user_stats['early_tests'] = user_stats.get('early_tests', 0) + 1
    
    # Track daily activity and streak
    today = date.today().isoformat()
    
    if user_stats.get('last_activity_date') != today:
        # New day
        yesterday = (date.today().replace(day=date.today().day-1)).isoformat()
        
        if user_stats.get('last_activity_date') == yesterday:
            # Continuing streak
            user_stats['daily_streak'] = user_stats.get('daily_streak', 0) + 1
        else:
            # Streak broken
            user_stats['daily_streak'] = 1
        
        user_stats['last_activity_date'] = today
        user_stats['tests_today'] = 1
    else:
        # Same day
        user_stats['tests_today'] += 1
    
    # Track max tests in a day
    if user_stats['tests_today'] > user_stats.get('tests_in_day', 0):
        user_stats['tests_in_day'] = user_stats['tests_today']
    
    # Track perfect scores
    percentage = (score / total) * 100
    if percentage == 100:
        user_stats['perfect_scores'] = user_stats.get('perfect_scores', 0) + 1
    
    # Track exam passes
    if category == 'exam':
        user_stats['exams_taken'] = user_stats.get('exams_taken', 0) + 1
        if percentage >= 70:
            user_stats['exams_passed'] = user_stats.get('exams_passed', 0) + 1
    
    # Add to test history
    user_stats['test_history'].append({
        'date': datetime.now().isoformat(),
        'category': category,
        'score': score,
        'total': total,
        'percentage': round(percentage, 1)
    })
    
    # Keep only last 20 tests
    if len(user_stats['test_history']) > 20:
        user_stats['test_history'] = user_stats['test_history'][-20:]
    
    save_stats(stats)
    
    # Update leaderboard
    try:
        from handlers.leaderboard import update_leaderboard
        from telegram import Update
        
        # Get username
        username = f"User{user_id}"  # Default
        if context and hasattr(context, 'bot'):
            try:
                chat = await context.bot.get_chat(user_id)
                if chat.username:
                    username = f"@{chat.username}"
                elif chat.first_name:
                    username = chat.first_name
            except:
                pass
        
        update_leaderboard(
            user_id=user_id,
            username=username,
            questions_solved=1,  # Incremental
            correct_answers=score,
            tests_taken=1
        )
    except Exception as e:
        print(f"Error updating leaderboard: {e}")
    
    # Check and award badges
    try:
        from handlers.badges import check_and_award_badges, notify_new_badge
        from handlers.leaderboard import get_user_rank
        
        # Add rank info for legend badge
        rank, _ = get_user_rank(user_id, 'alltime')
        user_stats['top_rank'] = rank if rank > 0 else 999
        
        # Check badges
        newly_earned = check_and_award_badges(user_id, user_stats)
        
        # Notify user of new badges
        if newly_earned and context:
            for badge_id in newly_earned:
                await notify_new_badge(context, user_id, badge_id)
    except Exception as e:
        print(f"Error checking badges: {e}")

def get_user_stats(user_id: int) -> Dict:
    """Get user statistics"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        return initialize_user_stats(user_id)
    
    return stats[user_key]

def get_wrong_questions(user_id: int) -> List[int]:
    """Get list of question IDs user got wrong"""
    user_stats = get_user_stats(user_id)
    return user_stats.get('wrong_questions', [])

def get_user_summary(user_id: int) -> str:
    """Get formatted user summary with badges and rank"""
    stats = get_user_stats(user_id)
    
    # Get badges
    try:
        from handlers.badges import get_user_badges
        badges = get_user_badges(user_id)
        badge_text = " ".join([b['emoji'] for b in badges[:5]])  # Show first 5 badges
        if len(badges) > 5:
            badge_text += f" +{len(badges) - 5}"
    except:
        badge_text = ""
    
    # Get rank
    try:
        from handlers.leaderboard import get_user_rank
        rank, _ = get_user_rank(user_id, 'alltime')
        if rank > 0 and rank <= 3:
            rank_medals = ['🥇', '🥈', '🥉']
            rank_text = f"\n🏆 Reyting: {rank_medals[rank-1]} {rank}-o'rin"
        elif rank > 0:
            rank_text = f"\n🏆 Reyting: {rank}-o'rin"
        else:
            rank_text = ""
    except:
        rank_text = ""
    
    summary = (
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"🏅 Nishonlar: {badge_text}\n" if badge_text else ""
        f"{rank_text}\n" if rank_text else ""
        f"\n"
        f"📝 Testlar: {stats['tests_taken']}\n"
        f"❓ Savollar: {stats['total_questions']}\n"
        f"✅ To'g'ri: {stats['correct_answers']}\n"
        f"🎯 Aniqlik: {stats['accuracy']}%\n"
        f"🔥 Ketma-ketlik: {stats.get('daily_streak', 0)} kun\n"
    )
    
    if stats.get('perfect_scores', 0) > 0:
        summary += f"💯 Mukammal: {stats['perfect_scores']}\n"
    
    if stats.get('exams_passed', 0) > 0:
        summary += f"🎓 Imtihonlar: {stats['exams_passed']}/{stats.get('exams_taken', 0)}\n"
    
    return summary
