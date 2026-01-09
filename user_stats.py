"""
User statistics and wrong answer tracking
"""

import json
from typing import Dict, List, Set
from datetime import datetime

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

def record_answer(user_id: int, question_id: int, is_correct: bool, category: str) -> None:
    """Record user's answer"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        stats[user_key] = {
            'tests_taken': 0,
            'total_questions': 0,
            'correct_answers': 0,
            'wrong_questions': [],
            'category_stats': {},
            'test_history': []
        }
    
    user_stats = stats[user_key]
    user_stats['total_questions'] += 1
    
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
    
    save_stats(stats)

def record_test_completion(user_id: int, category: str, score: int, total: int) -> None:
    """Record completed test"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        stats[user_key] = {
            'tests_taken': 0,
            'total_questions': 0,
            'correct_answers': 0,
            'wrong_questions': [],
            'category_stats': {},
            'test_history': []
        }
    
    user_stats = stats[user_key]
    user_stats['tests_taken'] += 1
    
    # Add to test history
    user_stats['test_history'].append({
        'date': datetime.now().isoformat(),
        'category': category,
        'score': score,
        'total': total,
        'percentage': round((score / total) * 100, 1)
    })
    
    # Keep only last 20 tests
    if len(user_stats['test_history']) > 20:
        user_stats['test_history'] = user_stats['test_history'][-20:]
    
    save_stats(stats)

def get_user_stats(user_id: int) -> Dict:
    """Get user statistics"""
    stats = load_stats()
    user_key = str(user_id)
    
    if user_key not in stats:
        return {
            'tests_taken': 0,
            'total_questions': 0,
            'correct_answers': 0,
            'wrong_questions': [],
            'category_stats': {},
            'test_history': []
        }
    
    return stats[user_key]

def get_wrong_questions(user_id: int) -> List[int]:
    """Get list of question IDs user got wrong"""
    user_stats = get_user_stats(user_id)
    return user_stats.get('wrong_questions', [])
