"""
Database migration script for premium features
Fixed version that auto-detects your database path
"""

import sqlite3
import os
from datetime import datetime

# Auto-detect database path
def get_db_path():
    """Find the database file in your project"""
    possible_paths = [
        'ppd_bot.db',
        'bot.db',
        'database.db',
        'data/ppd_bot.db',
        'data/bot.db',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✓ Found database at: {path}")
            return path
    
    # If not found, create new one
    db_path = 'ppd_bot.db'
    print(f"Creating new database at: {db_path}")
    return db_path

DB_PATH = get_db_path()

def migrate_database():
    """
    Add premium subscription tables to existing database
    Safe to run multiple times - checks if tables exist first
    """
    
    print("\n" + "="*60)
    print("PPD Bot Premium Features - Database Migration")
    print("="*60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First, let's see what tables already exist
        print("\n📋 Checking existing tables...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"   Existing tables: {', '.join(existing_tables) if existing_tables else 'None'}")
        
        # 1. Create subscriptions table
        print("\n1️⃣  Creating subscriptions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                plan_type TEXT NOT NULL DEFAULT 'free',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                payment_id TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Subscriptions table ready")
        
        # 2. Create payments table
        print("\n2️⃣  Creating payments table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'XTR',
                plan_type TEXT NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_provider TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        print("   ✅ Payments table ready")
        
        # 3. Create daily_usage table
        print("\n3️⃣  Creating daily_usage table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                tests_taken INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        """)
        print("   ✅ Daily usage table ready")
        
        # 4. Initialize free subscriptions for existing users (if users table exists)
        print("\n4️⃣  Initializing subscriptions for existing users...")
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO subscriptions (user_id, plan_type, status)
                SELECT user_id, 'free', 'active'
                FROM users
            """)
            rows_affected = cursor.rowcount
            print(f"   ✅ Initialized {rows_affected} user subscriptions")
        else:
            print("   ⚠️  No 'users' table found - will initialize subscriptions when users join")
        
        # 5. Create indexes for better performance
        print("\n5️⃣  Creating performance indexes...")
        
        indexes = [
            ("idx_subscriptions_user_id", "subscriptions", "user_id"),
            ("idx_subscriptions_status", "subscriptions", "status"),
            ("idx_payments_user_id", "payments", "user_id"),
            ("idx_daily_usage_user_date", "daily_usage", "user_id, date"),
        ]
        
        for idx_name, table, columns in indexes:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} 
                ON {table}({columns})
            """)
        
        print("   ✅ All indexes created")
        
        # Commit all changes
        conn.commit()
        
        # 6. Verify tables were created
        print("\n6️⃣  Verifying migration...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('subscriptions', 'payments', 'daily_usage')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if len(tables) == 3:
            print("   ✅ All premium tables verified")
        else:
            print(f"   ⚠️  Warning: Only found {len(tables)}/3 tables: {tables}")
        
        # 7. Show table statistics
        print("\n7️⃣  Database statistics:")
        
        cursor.execute("SELECT COUNT(*) FROM subscriptions")
        sub_count = cursor.fetchone()[0]
        print(f"   📊 Subscriptions: {sub_count}")
        
        cursor.execute("SELECT COUNT(*) FROM payments")
        pay_count = cursor.fetchone()[0]
        print(f"   💳 Payments: {pay_count}")
        
        cursor.execute("SELECT COUNT(*) FROM daily_usage")
        usage_count = cursor.fetchone()[0]
        print(f"   📈 Daily usage records: {usage_count}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Migration completed successfully!")
        print("="*60)
        print("\n📋 Next steps:")
        print("   1. Add utils/premium.py to your project")
        print("   2. Add handlers/premium.py to your project")
        print("   3. Update main.py to register premium handlers")
        print("   4. Configure payment provider in @BotFather")
        print("   5. Test with /premium command")
        print("\n💡 Tip: Run 'python migrate_premium_fixed.py status' to check migration status")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"   Database path: {DB_PATH}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_migration_status():
    """
    Check if migration has been run
    """
    print("\n" + "="*60)
    print("Checking Premium Migration Status")
    print("="*60 + "\n")
    
    try:
        if not os.path.exists(DB_PATH):
            print(f"❌ Database not found at: {DB_PATH}")
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check for premium tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('subscriptions', 'payments', 'daily_usage')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['subscriptions', 'payments', 'daily_usage']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Migration incomplete")
            print(f"   Missing tables: {', '.join(missing_tables)}")
            print(f"\n   Run: python migrate_premium_fixed.py")
            conn.close()
            return False
        
        print("✅ All premium tables exist\n")
        
        # Show detailed status
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✓ {table:20s} - {count} records")
        
        # Check for indexes
        print("\n📊 Checking indexes...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"   Found {len(indexes)} indexes: {', '.join(indexes)}")
        
        conn.close()
        
        print("\n✅ Premium features are ready to use!")
        return True
            
    except sqlite3.Error as e:
        print(f"❌ Error checking migration status: {e}")
        return False

def create_test_subscription():
    """
    Create a test premium subscription for testing
    """
    print("\n" + "="*60)
    print("Creating Test Premium Subscription")
    print("="*60 + "\n")
    
    try:
        user_id = input("Enter your Telegram user ID (or press Enter to skip): ").strip()
        
        if not user_id:
            print("Skipped - no user ID provided")
            return
        
        user_id = int(user_id)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create test subscription (7 days)
        from datetime import datetime, timedelta
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        cursor.execute("""
            INSERT OR REPLACE INTO subscriptions 
            (user_id, plan_type, start_date, end_date, payment_id, status)
            VALUES (?, 'premium', ?, ?, 'TEST_PAYMENT', 'active')
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Test premium subscription created!")
        print(f"   User ID: {user_id}")
        print(f"   Duration: 7 days")
        print(f"   Expires: {end_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"\n💡 Test with: /premium command in your bot")
        
    except ValueError:
        print("❌ Invalid user ID - must be a number")
    except Exception as e:
        print(f"❌ Error creating test subscription: {e}")

def rollback_migration():
    """
    Rollback migration by dropping premium tables
    WARNING: This will delete all subscription and payment data!
    """
    
    print("\n" + "="*60)
    print("⚠️  ROLLBACK MIGRATION - THIS WILL DELETE ALL DATA!")
    print("="*60 + "\n")
    
    print("This will permanently delete:")
    print("  • All subscriptions")
    print("  • All payment records")
    print("  • All usage statistics")
    print()
    
    confirm = input("Type 'DELETE ALL DATA' to confirm: ")
    
    if confirm != 'DELETE ALL DATA':
        print("\n✅ Rollback cancelled - no data deleted")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n🗑️  Dropping premium tables...")
        
        cursor.execute("DROP TABLE IF EXISTS daily_usage")
        print("   ✓ Dropped daily_usage")
        
        cursor.execute("DROP TABLE IF EXISTS payments")
        print("   ✓ Dropped payments")
        
        cursor.execute("DROP TABLE IF EXISTS subscriptions")
        print("   ✓ Dropped subscriptions")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Rollback completed - all premium tables removed")
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Rollback failed: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            check_migration_status()
        elif command == 'test':
            create_test_subscription()
        elif command == 'rollback':
            rollback_migration()
        else:
            print("Usage:")
            print("  python migrate_premium_fixed.py           - Run migration")
            print("  python migrate_premium_fixed.py status    - Check migration status")
            print("  python migrate_premium_fixed.py test      - Create test subscription")
            print("  python migrate_premium_fixed.py rollback  - Rollback migration (DANGEROUS!)")
    else:
        # Run migration
        migrate_database()
