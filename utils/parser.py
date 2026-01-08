"""
Parse question captions from admin
"""

import re
from typing import Dict, Optional, Tuple

def parse_question_caption(caption: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Parse caption in format:
    
    Question text
    
    A) Answer 1
    B) Answer 2
    C) Answer 3
    D) Answer 4
    
    ---
    
    Explanation
    """
    
    try:
        # Split by --- to separate answers from explanation
        if '---' in caption:
            parts = caption.split('---')
            top_part = parts[0].strip()
            explanation = parts[1].strip()
        else:
            top_part = caption.strip()
            explanation = "Tushuntirish kiritilmagan."
        
        lines = [line.strip() for line in top_part.split('\n') if line.strip()]
        option_pattern = re.compile(r'^[A-D]\)')
        
        question_lines = []
        option_lines = []
        in_options = False
        
        for line in lines:
            if option_pattern.match(line):
                in_options = True
                option_lines.append(line)
            elif in_options:
                if option_lines:
                    option_lines[-1] += " " + line
            else:
                question_lines.append(line)
        
        question = ' '.join(question_lines)
        
        # Remove A), B), C), D) prefixes
        options = []
        for line in option_lines:
            option_text = re.sub(r'^[A-D]\)\s*', '', line).strip()
            options.append(option_text)
        
        if not question:
            return None, "❌ Savol topilmadi"
        
        if len(options) != 4:
            return None, f"❌ {len(options)} ta javob topildi. 4 ta kerak (A, B, C, D)"
        
        return {
            'question': question,
            'options': options,
            'explanation': explanation
        }, None
        
    except Exception as e:
        return None, f"❌ Xatolik: {str(e)}"
