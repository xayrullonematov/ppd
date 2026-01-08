"""
Telegram keyboard layouts
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
import config

def get_category_keyboard() -> InlineKeyboardMarkup:
    """Create category selection keyboard"""
    from database import get_category_stats
    
    stats = get_category_stats()
    keyboard = []
    
    for letter, cat_info in config.CATEGORIES.items():
        cat_id = cat_info['id']
        count = stats.get(cat_id, 0)
        
        if count > 0:
            keyboard.append([InlineKeyboardButton(
                f"{cat_info['emoji']} {cat_info['name']} ({count})",
                callback_data=f"start_{cat_id}"
            )])
    
    return InlineKeyboardMarkup(keyboard)

def get_answer_keyboard(options: List[str]) -> InlineKeyboardMarkup:
    """Create answer buttons (already shuffled)"""
    keyboard = []
    
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(
            f"{chr(65+i)}) {option}",
            callback_data=f"answer_{i}"
        )])
    
    return InlineKeyboardMarkup(keyboard)

def get_result_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard after test completion"""
    keyboard = [
        [InlineKeyboardButton("🔄 Yana test", callback_data="back_to_categories")],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)
