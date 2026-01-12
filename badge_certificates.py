"""
Badge Certificate Generator - Creates shareable badge images
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime

def generate_badge_certificate(badge_name: str, badge_emoji: str, username: str, date_earned: str) -> BytesIO:
    """
    Generate a beautiful shareable certificate image for a badge
    Returns BytesIO object that can be sent as photo
    """
    
    # Create image (1200x630 - optimal for social media)
    width, height = 1200, 630
    img = Image.new('RGB', (width, height), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Add gradient background (simulate with rectangles)
    for i in range(height):
        opacity = int(255 * (i / height))
        color = (26 + opacity // 10, 26 + opacity // 10, 46 + opacity // 5)
        draw.rectangle([(0, i), (width, i + 1)], fill=color)
    
    # Draw border
    border_color = '#ffd700'  # Gold
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=border_color, width=5)
    draw.rectangle([(30, 30), (width - 30, height - 30)], outline=border_color, width=2)
    
    # Load fonts (fallback to default if not available)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw emoji (large)
    emoji_size = 150
    draw.text((width // 2, 100), badge_emoji, fill='white', anchor='mm', font=title_font)
    
    # Draw "YUTUQ" text
    draw.text((width // 2, 220), "YUTUQ", fill='#ffd700', anchor='mm', font=text_font)
    
    # Draw badge name
    draw.text((width // 2, 300), badge_name, fill='white', anchor='mm', font=name_font)
    
    # Draw username
    draw.text((width // 2, 380), f"@{username}", fill='#00d4ff', anchor='mm', font=text_font)
    
    # Draw earned date
    date_text = f"Olingan sana: {date_earned}"
    draw.text((width // 2, 450), date_text, fill='#aaaaaa', anchor='mm', font=small_font)
    
    # Draw footer
    footer_text = "🚗 PDD Test Bot"
    draw.text((width // 2, 550), footer_text, fill='#888888', anchor='mm', font=small_font)
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='PNG', quality=95)
    output.seek(0)
    
    return output

def generate_leaderboard_rank_image(rank: int, username: str, points: int, stats: dict) -> BytesIO:
    """
    Generate shareable leaderboard rank image
    """
    
    width, height = 1200, 630
    img = Image.new('RGB', (width, height), color='#0f0f1e')
    draw = ImageDraw.Draw(img)
    
    # Gradient background
    for i in range(height):
        opacity = int(255 * (i / height))
        color = (15 + opacity // 15, 15 + opacity // 15, 30 + opacity // 10)
        draw.rectangle([(0, i), (width, i + 1)], fill=color)
    
    # Border
    if rank == 1:
        border_color = '#ffd700'  # Gold
    elif rank == 2:
        border_color = '#c0c0c0'  # Silver
    elif rank == 3:
        border_color = '#cd7f32'  # Bronze
    else:
        border_color = '#4a4a6a'  # Purple
    
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=border_color, width=8)
    
    # Fonts
    try:
        huge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
    except:
        huge_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw rank with medal
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    rank_text = medals.get(rank, f"#{rank}")
    draw.text((width // 2, 120), rank_text, fill=border_color, anchor='mm', font=huge_font)
    
    # Draw title
    draw.text((width // 2, 240), "REYTINGI", fill='white', anchor='mm', font=title_font)
    
    # Draw username
    draw.text((width // 2, 330), f"@{username}", fill='#00d4ff', anchor='mm', font=title_font)
    
    # Draw stats
    stats_text = f"📊 {points} ball  |  ✅ {stats['correct']}/{stats['total']}  |  🎯 {stats['accuracy']}%"
    draw.text((width // 2, 420), stats_text, fill='white', anchor='mm', font=text_font)
    
    # Draw tests taken
    tests_text = f"📝 {stats['tests_taken']} ta test topshirildi"
    draw.text((width // 2, 490), tests_text, fill='#aaaaaa', anchor='mm', font=small_font)
    
    # Footer
    draw.text((width // 2, 560), "🚗 PDD Test Bot", fill='#666666', anchor='mm', font=small_font)
    
    output = BytesIO()
    img.save(output, format='PNG', quality=95)
    output.seek(0)
    
    return output

# Usage in badges.py:

async def send_badge_certificate(context, user_id: int, badge_id: str):
    """Send badge as shareable certificate image"""
    from handlers.badges import BADGE_DEFINITIONS, get_user_badges
    
    if badge_id not in BADGE_DEFINITIONS:
        return
    
    badge = BADGE_DEFINITIONS[badge_id]
    
    # Get user info
    try:
        chat = await context.bot.get_chat(user_id)
        username = chat.username or chat.first_name or f"User{user_id}"
    except:
        username = f"User{user_id}"
    
    # Generate certificate
    date_earned = datetime.now().strftime('%d.%m.%Y')
    certificate = generate_badge_certificate(
        badge_name=badge['name'],
        badge_emoji=badge['emoji'],
        username=username,
        date_earned=date_earned
    )
    
    # Send as photo
    caption = (
        f"🎉 <b>YANGI YUTUQ!</b>\n\n"
        f"{badge['emoji']} <b>{badge['name']}</b>\n"
        f"{badge['description']}\n\n"
        f"Do'stlaringiz bilan ulashing! 👆"
    )
    
    try:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=certificate,
            caption=caption,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending certificate: {e}")

async def send_rank_certificate(context, user_id: int, rank: int, stats: dict):
    """Send leaderboard rank as shareable image"""
    
    # Get user info
    try:
        chat = await context.bot.get_chat(user_id)
        username = chat.username or chat.first_name or f"User{user_id}"
    except:
        username = f"User{user_id}"
    
    # Generate image
    rank_image = generate_leaderboard_rank_image(
        rank=rank,
        username=username,
        points=stats['points'],
        stats={
            'correct': stats['correct_answers'],
            'total': stats['questions_solved'],
            'accuracy': stats['accuracy'],
            'tests_taken': stats['tests_taken']
        }
    )
    
    # Send
    caption = (
        f"🏆 <b>Sizning reytingingiz</b>\n\n"
        f"{'🥇🥈🥉'[rank-1] if rank <= 3 else f'#{rank}'} o'rin\n"
        f"📊 {stats['points']} ball\n\n"
        f"Do'stlaringiz bilan ulashing! 👆"
    )
    
    try:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=rank_image,
            caption=caption,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending rank image: {e}")
