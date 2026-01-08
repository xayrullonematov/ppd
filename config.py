"""
Bot configuration
"""

# Bot token from @BotFather
TOKEN = "8534427551:AAF8F-AJzoo1pko77mMj2HN4AiaFjYEVsBw"

# Admin Telegram user ID (get from @userinfobot)
ADMIN_ID = 7038406097

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
