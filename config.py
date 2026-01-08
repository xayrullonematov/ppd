"""
Bot configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token from @BotFather - LOAD FROM ENVIRONMENT
TOKEN = os.getenv("BOT_TOKEN", "")

# Admin Telegram user ID (get from @userinfobot) - LOAD FROM ENVIRONMENT
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Category definitions
CATEGORIES = {
    'a': {
        'id': 'signs',
        'name': '🚦 Yo\'l belgilari',
        'emoji': '🚦'
    },
    'b': {
        'id': 'rules',
        'name': '🚗 Yo\'l harakati qoidalari',
        'emoji': '🚗'
    },
    'c': {
        'id': 'speed',
        'name': '⚡ Tezlik va jarimalar',
        'emoji': '⚡'
    },
    'd': {
        'id': 'mixed',
        'name': '🧠 Aralash',
        'emoji': '🧠'
    }
}

# Map category IDs to letters for easy admin input
CATEGORY_MAP = {cat['id']: letter for letter, cat in CATEGORIES.items()}

def get_category_name(letter):
    """Get category name from letter (a/b/c/d)"""
    return CATEGORIES.get(letter, {}).get('name', 'Unknown')

def get_category_id(letter):
    """Get category ID from letter"""
    return CATEGORIES.get(letter, {}).get('id', 'mixed')

# Validate configuration
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables!")

if ADMIN_ID == 0:
    raise ValueError("ADMIN_ID not found in environment variables!")
