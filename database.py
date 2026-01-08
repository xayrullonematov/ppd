"""
Question database management
"""

import json
import random
from typing import List, Dict, Optional

QUESTIONS_FILE = 'questions.json'

def load_questions() -> List[Dict]:
    """Load questions from JSON file"""
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Validate and fix question structure
            for q in data:
                # Ensure correct_index exists (backward compatibility)
                if 'correct_index' not in q and 'correct' in q:
                    q['correct_index'] = q['correct']
                
                # Ensure category exists
                if 'category' not in q:
                    q['category'] = 'mixed'
                    
                # Ensure explanation exists
                if 'explanation' not in q:
                    q['explanation'] = 'Tushuntirish kiritilmagan.'
            
            return data
            
    except FileNotFoundError:
        print(f"Warning: {QUESTIONS_FILE} not found. Creating empty file.")
        save_questions([])
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {QUESTIONS_FILE}: {e}")
        return []
    except PermissionError:
        print(f"Error: No permission to read {QUESTIONS_FILE}")
        return []
    except Exception as e:
        print(f"Unexpected error loading questions: {e}")
        return []

def save_questions(questions: List[Dict]) -> None:
    """Save questions to JSON file"""
    try:
        with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
    except PermissionError:
        print(f"Error: No permission to write to {QUESTIONS_FILE}")
    except Exception as e:
        print(f"Error saving questions: {e}")

def add_question(question: Dict) -> int:
    """Add a new question and return its ID"""
    try:
        questions = load_questions()
        question['id'] = len(questions) + 1
        
        # Ensure all required fields exist
        if 'correct_index' not in question:
            raise ValueError("Question must have 'correct_index' field")
        if 'category' not in question:
            question['category'] = 'mixed'
        if 'explanation' not in question:
            question['explanation'] = 'Tushuntirish kiritilmagan.'
        
        questions.append(question)
        save_questions(questions)
        return question['id']
    except Exception as e:
        print(f"Error adding question: {e}")
        return -1

def get_questions_by_category(category: str) -> List[Dict]:
    """Get all questions from a specific category"""
    questions = load_questions()
    
    if category == 'mixed':
        return questions
    
    return [q for q in questions if q.get('category') == category]

def get_random_questions(category: str, count: int = 10) -> List[Dict]:
    """Get random questions from a category with shuffled options"""
    questions = get_questions_by_category(category)
    
    if not questions:
        return []
    
    # Get random sample
    selected = random.sample(questions, min(len(questions), count))
    
    # Shuffle options for each question
    shuffled_questions = []
    for q in selected:
        try:
            shuffled_q = q.copy()
            
            # Ensure correct_index exists
            if 'correct_index' not in q:
                print(f"Warning: Question {q.get('id', 'unknown')} missing correct_index")
                continue
            
            # Create list of (option, is_correct) tuples
            options_with_correct = [
                (opt, i == q['correct_index']) 
                for i, opt in enumerate(q['options'])
            ]
            
            # Shuffle
            random.shuffle(options_with_correct)
            
            # Extract shuffled options and find new correct index
            shuffled_q['shuffled_options'] = [opt for opt, _ in options_with_correct]
            shuffled_q['shuffled_correct_index'] = next(
                i for i, (_, is_correct) in enumerate(options_with_correct) if is_correct
            )
            
            shuffled_questions.append(shuffled_q)
            
        except Exception as e:
            print(f"Error shuffling question {q.get('id', 'unknown')}: {e}")
            continue
    
    return shuffled_questions

def get_category_stats() -> Dict[str, int]:
    """Get question count per category"""
    questions = load_questions()
    
    stats = {
        'signs': 0,
        'rules': 0,
        'speed': 0,
        'mixed': len(questions)
    }
    
    for q in questions:
        category = q.get('category', 'mixed')
        if category in stats:
            stats[category] += 1
    
    return stats

def get_total_count() -> int:
    """Get total number of questions"""
    return len(load_questions())
