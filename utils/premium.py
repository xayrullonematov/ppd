"""
Premium subscription management for PPD Bot
Handles premium tier checks, limits, and feature access
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict
import sqlite3
import os

# Auto-detect database path
def get_db_path():
    """Find the database file in your project"""
    # Try to import from config first
    try:
        from config import DB_PATH
        return DB_PATH
    except (ImportError, AttributeError):
        pass
    
    # Try common paths
    possible_paths = [
        'ppd_bot.db',
        'bot.db',
        'database.db',
        'data/ppd_bot.db',
        'data/bot.db',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Default
    return 'ppd_bot.db'

DB_PATH = get_db_path()

class PremiumTier:
    """Subscription tier constants"""
    FREE = 'free'
    PREMIUM = 'premium'

class PremiumLimits:
    """Usage limits for different tiers"""
    FREE_DAILY_TESTS = 5
    FREE_HISTORY_LIMIT = 10
    PREMIUM_DAILY_TESTS = -1  # Unlimited
    PREMIUM_HISTORY_LIMIT = -1  # Unlimited

class SubscriptionManager:
    """Manage premium subscriptions and feature access"""
    
    @staticmethod
    def get_user_subscription(user_id: int) -> Optional[Dict]:
        """
        Get user's subscription details
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Subscription dict or None if not found
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM subscriptions 
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except sqlite3.Error as e:
            print(f"Database error in get_user_subscription: {e}")
            return None
    
    @staticmethod
    async def is_premium(user_id: int) -> bool:
        """
        Check if user has active premium subscription
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if premium, False otherwise
        """
        sub = SubscriptionManager.get_user_subscription(user_id)
        
        if not sub:
            return False
        
        # Free tier
        if sub['plan_type'] == PremiumTier.FREE:
            return False
        
        # Check if subscription is active and not expired
        if sub['status'] == 'active':
            try:
                end_date = datetime.fromisoformat(sub['end_date'])
                if end_date > datetime.now():
                    return True
            except (ValueError, TypeError):
                return False
        
        return False
    
    @staticmethod
    def get_today_test_count(user_id: int) -> int:
        """
        Get number of tests taken today
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Test count for today
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            cursor.execute("""
                SELECT tests_taken FROM daily_usage 
                WHERE user_id = ? AND date = ?
            """, (user_id, today))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except sqlite3.Error as e:
            print(f"Database error in get_today_test_count: {e}")
            return 0
    
    @staticmethod
    def increment_daily_usage(user_id: int) -> bool:
        """
        Increment daily test usage counter
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            # Try to increment existing record
            cursor.execute("""
                UPDATE daily_usage 
                SET tests_taken = tests_taken + 1 
                WHERE user_id = ? AND date = ?
            """, (user_id, today))
            
            # If no record exists, create one
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO daily_usage (user_id, date, tests_taken) 
                    VALUES (?, ?, 1)
                """, (user_id, today))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error in increment_daily_usage: {e}")
            return False
    
    @staticmethod
    async def check_daily_limit(user_id: int) -> Dict[str, any]:
        """
        Check if user has reached daily test limit
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict with allowed status and usage info
        """
        is_premium = await SubscriptionManager.is_premium(user_id)
        
        if is_premium:
            return {
                'allowed': True,
                'remaining': 'unlimited',
                'limit': 'unlimited',
                'count': 0,
                'is_premium': True
            }
        
        # Free users: limited tests per day
        today_count = SubscriptionManager.get_today_test_count(user_id)
        limit = PremiumLimits.FREE_DAILY_TESTS
        remaining = max(0, limit - today_count)
        
        return {
            'allowed': remaining > 0,
            'remaining': remaining,
            'limit': limit,
            'count': today_count,
            'is_premium': False
        }
    
    @staticmethod
    async def can_view_explanations(user_id: int) -> bool:
        """
        Check if user can view answer explanations
        Premium feature only
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if allowed, False otherwise
        """
        return await SubscriptionManager.is_premium(user_id)
    
    @staticmethod
    async def can_export_pdf(user_id: int) -> bool:
        """
        Check if user can export results to PDF
        Premium feature only
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if allowed, False otherwise
        """
        return await SubscriptionManager.is_premium(user_id)
    
    @staticmethod
    async def get_history_limit(user_id: int) -> int:
        """
        Get test history limit for user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Number of history items allowed (-1 for unlimited)
        """
        is_premium = await SubscriptionManager.is_premium(user_id)
        
        if is_premium:
            return PremiumLimits.PREMIUM_HISTORY_LIMIT
        
        return PremiumLimits.FREE_HISTORY_LIMIT
    
    @staticmethod
    def save_subscription(
        user_id: int,
        plan_type: str,
        start_date: datetime,
        end_date: datetime,
        payment_id: str
    ) -> bool:
        """
        Save or update user subscription
        
        Args:
            user_id: Telegram user ID
            plan_type: Type of plan (free/premium)
            start_date: Subscription start date
            end_date: Subscription end date
            payment_id: Payment transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, plan_type, start_date, end_date, payment_id, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (
                user_id,
                plan_type,
                start_date.isoformat(),
                end_date.isoformat(),
                payment_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error in save_subscription: {e}")
            return False
    
    @staticmethod
    def save_payment(
        payment_id: str,
        user_id: int,
        amount: float,
        currency: str,
        plan_type: str,
        payment_provider: str
    ) -> bool:
        """
        Save payment record
        
        Args:
            payment_id: Payment transaction ID
            user_id: Telegram user ID
            amount: Payment amount
            currency: Currency code
            plan_type: Plan type (monthly/yearly)
            payment_provider: Payment provider name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO payments 
                (payment_id, user_id, amount, currency, plan_type, payment_provider, status)
                VALUES (?, ?, ?, ?, ?, ?, 'completed')
            """, (
                payment_id,
                user_id,
                amount,
                currency,
                plan_type,
                payment_provider
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error in save_payment: {e}")
            return False
    
    @staticmethod
    def cancel_subscription(user_id: int) -> bool:
        """
        Cancel user's subscription
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE subscriptions 
                SET status = 'cancelled'
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error in cancel_subscription: {e}")
            return False
    
    @staticmethod
    async def get_premium_message() -> str:
        """
        Get upgrade to premium promotional message
        
        Returns:
            Formatted premium promotion message
        """
        return (
            "🌟 <b>Upgrade to Premium!</b>\n\n"
            "✨ <b>Premium Benefits:</b>\n"
            "• 🔓 Unlimited tests per day\n"
            "• 📝 Detailed answer explanations\n"
            "• 📊 Advanced analytics & insights\n"
            "• 📥 Export results to PDF\n"
            "• 📚 Full test history access\n"
            "• ⭐ Priority support\n"
            "• 🚫 Ad-free experience\n\n"
            "💳 <b>Pricing:</b>\n"
            "• Monthly: 500 Stars ($4.99)\n"
            "• Yearly: 4000 Stars ($39.99) - Save 33%!\n\n"
            "Tap /premium to upgrade now!"
        )
    
    @staticmethod
    def get_subscription_info(user_id: int) -> Dict:
        """
        Get formatted subscription information
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with subscription details
        """
        sub = SubscriptionManager.get_user_subscription(user_id)
        
        if not sub or sub['plan_type'] == PremiumTier.FREE:
            return {
                'is_premium': False,
                'plan_name': 'Free',
                'expires': None,
                'status': 'active'
            }
        
        try:
            end_date = datetime.fromisoformat(sub['end_date'])
            days_remaining = (end_date - datetime.now()).days
            
            return {
                'is_premium': True,
                'plan_name': 'Premium',
                'expires': end_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
                'status': sub['status'],
                'auto_renew': False  # Can be extended if you implement auto-renewal
            }
        except (ValueError, TypeError):
            return {
                'is_premium': False,
                'plan_name': 'Free',
                'expires': None,
                'status': 'error'
            }
