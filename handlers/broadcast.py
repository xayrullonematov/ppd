"""
Broadcast functionality for admin
"""

from telegram import Update
from telegram.ext import ContextTypes
import config
from user_stats import load_stats
import asyncio

# Store broadcast state
broadcast_state = {}

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast mode"""
    user_id = update.effective_user.id
    
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q")
        return
    
    # Get user count
    stats = load_stats()
    user_count = len(stats)
    
    broadcast_state[user_id] = {
        'action': 'broadcast',
        'waiting': True
    }
    
    await update.message.reply_text(
        f"📢 <b>Broadcast xabari</b>\n\n"
        f"👥 Jami foydalanuvchilar: {user_count}\n\n"
        f"Yubormoqchi bo'lgan xabaringizni yuboring.\n"
        f"(Matn, rasm, video qo'llab-quvvatlanadi)\n\n"
        f"Bekor qilish: /cancel",
        parse_mode='HTML'
    )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message from admin"""
    user_id = update.effective_user.id
    
    if user_id not in broadcast_state:
        return
    
    # Get all users
    stats = load_stats()
    user_ids = [int(uid) for uid in stats.keys()]
    
    # Delete broadcast state
    del broadcast_state[user_id]
    
    # Send confirmation
    total_users = len(user_ids)
    
    await update.message.reply_text(
        f"📤 Xabar yuborilmoqda...\n\n"
        f"👥 Foydalanuvchilar: {total_users}"
    )
    
    # Send to all users
    success = 0
    failed = 0
    
    for uid in user_ids:
        try:
            if update.message.photo:
                # Forward photo with caption
                await context.bot.send_photo(
                    chat_id=uid,
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption or ""
                )
            elif update.message.video:
                await context.bot.send_video(
                    chat_id=uid,
                    video=update.message.video.file_id,
                    caption=update.message.caption or ""
                )
            else:
                # Send text
                await context.bot.send_message(
                    chat_id=uid,
                    text=update.message.text
                )
            success += 1
            
            # Rate limit: 30 messages per second
            if success % 30 == 0:
                await asyncio.sleep(1)
                
        except Exception as e:
            failed += 1
            print(f"Failed to send to {uid}: {e}")
    
    # Send final report
    await update.message.reply_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"📊 Natijalar:\n"
        f"✅ Yuborildi: {success}\n"
        f"❌ Xato: {failed}\n"
        f"📈 Muvaffaqiyat: {(success/total_users*100):.1f}%",
        parse_mode='HTML'
    )

# Export for main.py
__all__ = ['broadcast_command', 'handle_broadcast_message', 'broadcast_state']
