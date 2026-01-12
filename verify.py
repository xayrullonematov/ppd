#!/usr/bin/env python3
import sys

print("🔍 Checking badge & certificate system...\n")

errors = []

# Check 1: Utils directory
try:
    import utils.badge_images
    print("✅ utils/badge_images.py found")
except ImportError as e:
    errors.append(f"❌ utils/badge_images.py missing: {e}")

# Check 2: Pillow installed
try:
    from PIL import Image
    print("✅ Pillow installed")
except ImportError:
    errors.append("❌ Pillow not installed (run: pip install Pillow)")

# Check 3: handlers/badges.py
try:
    from handlers.badges import notify_new_badge, BADGE_DEFINITIONS
    print("✅ handlers/badges.py OK")
except ImportError as e:
    errors.append(f"❌ handlers/badges.py error: {e}")

# Check 4: handlers/leaderboard.py
try:
    from handlers.leaderboard import share_rank_certificate
    print("✅ handlers/leaderboard.py OK")
except ImportError as e:
    errors.append(f"❌ handlers/leaderboard.py error: {e}")

# Check 5: user_stats.py
try:
    from user_stats import record_test_completion
    import inspect
    if inspect.iscoroutinefunction(record_test_completion):
        print("✅ record_test_completion is async")
    else:
        errors.append("❌ record_test_completion is not async")
except Exception as e:
    errors.append(f"❌ user_stats.py error: {e}")

print("\n" + "="*50)
if errors:
    print("❌ ERRORS FOUND:\n")
    for error in errors:
        print(error)
    sys.exit(1)
else:
    print("✅ ALL CHECKS PASSED!")
    print("\nYou can now run: python main.py")
    sys.exit(0)
