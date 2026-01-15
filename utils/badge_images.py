"""
PROFESSIONAL Badge Certificate Generator - Uses your beautiful badge templates!
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
import os

# Get the script directory for asset paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')

def generate_badge_certificate(badge_name: str, badge_emoji: str, username: str, date_earned: str) -> BytesIO:
    """
    Generate certificate using professional badge template
    Overlays text on your beautiful badge design!
    """
    
    try:
        # Load your badge template
        template_path = os.path.join(ASSETS_DIR, 'badge_template_2.png')
        
        if not os.path.exists(template_path):
            print(f"⚠️ Template not found at {template_path}, using fallback")
            return generate_simple_fallback(badge_name, badge_emoji, username, date_earned)
        
        # Open template image
        img = Image.open(template_path).convert('RGBA')
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        except:
            large_font = ImageFont.load_default()
            medium_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Get image dimensions
        width, height = img.size
        
        # Overlay text in center-bottom area (below the badge graphic)
        # These positions work well with your badge design
        
        # Badge name (main text) - middle area
        badge_text = badge_name.upper()
        draw.text(
            (width // 2, int(height * 0.70)), 
            badge_text, 
            fill='white', 
            anchor='mm', 
            font=large_font,
            stroke_width=2,
            stroke_fill='#000033'  # Outline for readability
        )
        
        # Username - below badge name
        username_display = username if username.startswith('@') else f"@{username}"
        draw.text(
            (width // 2, int(height * 0.80)), 
            username_display, 
            fill='#FFD700',  # Gold color
            anchor='mm', 
            font=medium_font,
            stroke_width=1,
            stroke_fill='#000033'
        )
        
        # Date - bottom
        draw.text(
            (width // 2, int(height * 0.90)), 
            date_earned, 
            fill='#CCCCCC', 
            anchor='mm', 
            font=small_font
        )
        
        # Convert to RGB for JPEG (better for Telegram)
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        
        # Save to BytesIO
        output = BytesIO()
        rgb_img.save(output, format='JPEG', quality=95, optimize=True)
        output.seek(0)
        output.name = f'badge_{badge_name.replace(" ", "_")}.jpg'
        
        return output
        
    except Exception as e:
        print(f"❌ Error using template: {e}")
        return generate_simple_fallback(badge_name, badge_emoji, username, date_earned)


def generate_leaderboard_certificate(rank: int, username: str, points: int, 
                                     correct: int, total: int, accuracy: float, 
                                     tests_taken: int) -> BytesIO:
    """
    Generate leaderboard rank certificate using template
    """
    
    try:
        # Use template 1 for leaderboard (with TOP 10)
        template_path = os.path.join(ASSETS_DIR, 'badge_template_1.png')
        
        if not os.path.exists(template_path):
            print(f"⚠️ Template not found, using fallback")
            return generate_rank_fallback(rank, username, points, correct, total, accuracy, tests_taken)
        
        img = Image.open(template_path).convert('RGBA')
        draw = ImageDraw.Draw(img)
        
        # Fonts
        try:
            huge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
            medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            huge_font = ImageFont.load_default()
            large_font = ImageFont.load_default()
            medium_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        width, height = img.size
        
        # Rank number (big, in center)
        rank_text = f"#{rank}" if rank > 3 else ['🥇', '🥈', '🥉'][rank-1]
        draw.text(
            (width // 2, int(height * 0.40)), 
            rank_text, 
            fill='#FFD700', 
            anchor='mm', 
            font=huge_font,
            stroke_width=3,
            stroke_fill='#000033'
        )
        
        # Username
        username_display = username if username.startswith('@') else f"@{username}"
        draw.text(
            (width // 2, int(height * 0.62)), 
            username_display, 
            fill='white', 
            anchor='mm', 
            font=large_font,
            stroke_width=2,
            stroke_fill='#000033'
        )
        
        # Points
        draw.text(
            (width // 2, int(height * 0.73)), 
            f"{points} BALL", 
            fill='#FFD700', 
            anchor='mm', 
            font=medium_font,
            stroke_width=1,
            stroke_fill='#000033'
        )
        
        # Stats
        stats_text = f"✅ {correct}/{total}  •  🎯 {accuracy}%  •  📝 {tests_taken}"
        draw.text(
            (width // 2, int(height * 0.82)), 
            stats_text, 
            fill='white', 
            anchor='mm', 
            font=small_font
        )
        
        # Date
        draw.text(
            (width // 2, int(height * 0.91)), 
            datetime.now().strftime('%d.%m.%Y'), 
            fill='#AAAAAA', 
            anchor='mm', 
            font=small_font
        )
        
        # Convert to RGB
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        
        output = BytesIO()
        rgb_img.save(output, format='JPEG', quality=95, optimize=True)
        output.seek(0)
        output.name = f'rank_{rank}_certificate.jpg'
        
        return output
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return generate_rank_fallback(rank, username, points, correct, total, accuracy, tests_taken)


def generate_simple_fallback(badge_name: str, badge_emoji: str, username: str, date_earned: str) -> BytesIO:
    """Fallback if template not found"""
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color='#1a1a3e')
    draw = ImageDraw.Draw(img)
    
    # Simple gradient
    for i in range(height):
        ratio = i / height
        r = int(26 + (30 * ratio))
        g = int(26 + (40 * ratio))
        b = int(62 + (50 * ratio))
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # Gold border
    draw.rectangle([(40, 40), (width - 40, height - 40)], outline='#FFD700', width=12)
    
    try:
        large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
    except:
        large_font = ImageFont.load_default()
        medium_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Text
    draw.text((width // 2, 300), badge_emoji * 3, fill='white', anchor='mm', font=large_font)
    draw.text((width // 2, 500), badge_name, fill='#FFD700', anchor='mm', font=medium_font)
    draw.text((width // 2, 650), f"@{username}", fill='white', anchor='mm', font=small_font)
    draw.text((width // 2, 800), date_earned, fill='#CCCCCC', anchor='mm', font=small_font)
    
    output = BytesIO()
    img.save(output, format='JPEG', quality=95)
    output.seek(0)
    return output


def generate_rank_fallback(rank: int, username: str, points: int, 
                           correct: int, total: int, accuracy: float, 
                           tests_taken: int) -> BytesIO:
    """Fallback for rank certificates"""
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color='#1a1a3e')
    draw = ImageDraw.Draw(img)
    
    # Gradient
    for i in range(height):
        ratio = i / height
        r = int(26 + (30 * ratio))
        b = int(62 + (50 * ratio))
        draw.line([(0, i), (width, i)], fill=(r, 26, b))
    
    # Border
    border_color = '#FFD700' if rank <= 3 else '#4a4a6a'
    draw.rectangle([(40, 40), (width - 40, height - 40)], outline=border_color, width=12)
    
    try:
        huge_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 150)
        large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
    except:
        huge_font = ImageFont.load_default()
        large_font = ImageFont.load_default()
        medium_font = ImageFont.load_default()
    
    # Rank
    rank_text = f"#{rank}" if rank > 3 else ['🥇', '🥈', '🥉'][rank-1]
    draw.text((width // 2, 300), rank_text, fill='#FFD700', anchor='mm', font=huge_font)
    
    # Username
    draw.text((width // 2, 500), f"@{username}", fill='white', anchor='mm', font=large_font)
    
    # Stats
    draw.text((width // 2, 650), f"{points} BALL", fill='#FFD700', anchor='mm', font=medium_font)
    draw.text((width // 2, 750), f"✅ {correct}/{total}  •  🎯 {accuracy}%", fill='white', anchor='mm', font=medium_font)
    
    output = BytesIO()
    img.save(output, format='JPEG', quality=95)
    output.seek(0)
    return output
