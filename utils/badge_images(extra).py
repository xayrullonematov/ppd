# Badge certificate generator

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime

def generate_badge_certificate(badge_name: str, badge_emoji: str, username: str, date_earned: str) -> BytesIO:
    """
    Generate a beautiful shareable certificate image for a badge
    """
    
    # Create image (1200x630 - optimal for social media)
    width, height = 1200, 630
    
    # Create base image with dark blue background
    img = Image.new('RGB', (width, height), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect (dark to lighter)
    for i in range(height):
        # Calculate color gradient
        ratio = i / height
        r = int(26 + (20 * ratio))
        g = int(26 + (20 * ratio))
        b = int(46 + (30 * ratio))
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # Draw golden border (double border effect)
    border_color = '#ffd700'  # Gold
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=border_color, width=8)
    draw.rectangle([(30, 30), (width - 30, height - 30)], outline=border_color, width=2)
    
    # Load fonts (with fallback)
    try:
        # Try to load DejaVu fonts (available on most Linux systems)
        emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 120)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception as e:
        print(f"Font loading warning: {e}")
        # Fallback to default fonts with larger sizes
        emoji_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw emoji (large, centered at top)
    emoji_text = badge_emoji * 3  # Repeat emoji 3 times for impact
    draw.text((width // 2, 120), emoji_text, fill='white', anchor='mm', font=emoji_font)
    
    # Draw "YUTUQ" text (Achievement)
    draw.text((width // 2, 230), "YUTUQ", fill='#ffd700', anchor='mm', font=title_font)
    
    # Draw badge name (main text)
    draw.text((width // 2, 320), badge_name, fill='white', anchor='mm', font=name_font)
    
    # Draw username with @ symbol
    username_display = username if username.startswith('@') else f"@{username}"
    draw.text((width // 2, 400), username_display, fill='#00d4ff', anchor='mm', font=text_font)
    
    # Draw earned date
    date_text = f"Olingan sana: {date_earned}"
    draw.text((width // 2, 470), date_text, fill='#aaaaaa', anchor='mm', font=small_font)
    
    # Draw decorative line
    draw.line([(200, 520), (width - 200, 520)], fill='#ffd700', width=2)
    
    # Draw footer with bot name
    footer_text = "🚗 PDD Test Bot"
    draw.text((width // 2, 560), footer_text, fill='#888888', anchor='mm', font=small_font)
    
    # Save to BytesIO object
    output = BytesIO()
    img.save(output, format='PNG', quality=95, optimize=True)
    output.seek(0)
    output.name = f'badge_{badge_name.replace(" ", "_")}.png'
    
    return output


def generate_leaderboard_certificate(rank: int, username: str, points: int, 
                                     correct: int, total: int, accuracy: float, 
                                     tests_taken: int) -> BytesIO:
    """
    Generate shareable leaderboard rank certificate
    """
    
    width, height = 1200, 630
    
    # Determine rank color
    if rank == 1:
        bg_color = '#1a1a1a'  # Dark for gold
        border_color = '#ffd700'  # Gold
        rank_color = '#ffd700'
    elif rank == 2:
        bg_color = '#1a1a1a'
        border_color = '#c0c0c0'  # Silver
        rank_color = '#c0c0c0'
    elif rank == 3:
        bg_color = '#1a1a1a'
        border_color = '#cd7f32'  # Bronze
        rank_color = '#cd7f32'
    else:
        bg_color = '#0f0f1e'
        border_color = '#4a4a6a'  # Purple
        rank_color = '#8a8aff'
    
    # Create base image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Gradient
    for i in range(height):
        ratio = i / height
        if rank == 1:
            r = int(26 + (40 * ratio))
            g = int(26 + (40 * ratio))
            b = int(10 + (20 * ratio))
        else:
            r = int(15 + (20 * ratio))
            g = int(15 + (20 * ratio))
            b = int(30 + (20 * ratio))
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # Draw border (thicker for top ranks)
    border_width = 10 if rank <= 3 else 6
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=border_color, width=border_width)
    draw.rectangle([(30, 30), (width - 30, height - 30)], outline=border_color, width=2)
    
    # Fonts
    try:
        huge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        huge_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw rank with medal emoji
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    if rank <= 3:
        rank_display = medals[rank]
        draw.text((width // 2, 130), rank_display, fill=rank_color, anchor='mm', font=huge_font)
        draw.text((width // 2, 220), f"{rank}-O'RIN", fill=rank_color, anchor='mm', font=title_font)
    else:
        draw.text((width // 2, 130), f"#{rank}", fill=rank_color, anchor='mm', font=huge_font)
        draw.text((width // 2, 220), "REYTINGI", fill='white', anchor='mm', font=title_font)
    
    # Draw username
    username_display = username if username.startswith('@') else f"@{username}"
    draw.text((width // 2, 310), username_display, fill='#00d4ff', anchor='mm', font=name_font)
    
    # Draw points
    draw.text((width // 2, 390), f"📊 {points} BALL", fill='white', anchor='mm', font=text_font)
    
    # Draw stats line
    stats_text = f"✅ {correct}/{total}  |  🎯 {accuracy}%  |  📝 {tests_taken} test"
    draw.text((width // 2, 450), stats_text, fill='#cccccc', anchor='mm', font=small_font)
    
    # Draw decorative line
    draw.line([(200, 510), (width - 200, 510)], fill=border_color, width=2)
    
    # Draw date
    date_text = datetime.now().strftime('%d.%m.%Y')
    draw.text((width // 2, 550), f"Sana: {date_text}", fill='#888888', anchor='mm', font=small_font)
    
    # Footer
    draw.text((width // 2, 590), "🚗 PDD Test Bot", fill='#666666', anchor='mm', font=small_font)
    
    # Save
    output = BytesIO()
    img.save(output, format='PNG', quality=95, optimize=True)
    output.seek(0)
    output.name = f'rank_{rank}_certificate.png'
    
    return output
