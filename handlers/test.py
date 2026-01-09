"""
Test session management
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import get_random_questions
from user_stats import record_answer, record_test_completion, get_wrong_questions
from utils.keyboards import get_answer_keyboard, get_result_keyboard
import config

# Store active test sessions
user_sessions = {}

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Start a new test"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        # Get randomized questions
        questions = get_random_questions(category, count=10)
        
        if not questions:
            await query.edit_message_text("❌ Bu bo'limda savollar yo'q.")
            return
        
        # Store session
        user_sessions[user_id] = {
            'questions': questions,
            'current': 0,
            'correct': 0,
            'category': category
        }
        
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == category),
            config.CATEGORIES['d']
        )
        
        await query.edit_message_text(
            f"🎯 Test boshlandi!\n\n"
            f"📚 Bo'lim: {cat_info['name']}\n"
            f"❓ Savollar: {len(questions)} ta\n\n"
            f"Omad! 🍀"
        )
        
        await send_question(update, context, user_id)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik: {str(e)}")

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send next question to user"""
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    current_num = session['current']
    questions = session['questions']
    
    # Check if test is complete
    if current_num >= len(questions):
        await show_results(update, context, user_id)
        return
    
    question = questions[current_num]
    
    try:
        # Use shuffled options
        keyboard = get_answer_keyboard(question['shuffled_options'])
        
        question_text = (
            f"❓ Savol {current_num + 1}/{len(questions)}\n\n"
            f"{question['question']}"
        )
        
        # Send with image if available
        if question.get('file_id'):
            try:
                if update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=question['file_id'],
                        caption=question_text,
                        reply_markup=keyboard
                    )
                else:
                    await update.message.reply_photo(
                        photo=question['file_id'],
                        caption=question_text,
                        reply_markup=keyboard
                    )
            except Exception as img_error:
                # Fallback to text if image fails
                print(f"Image failed: {img_error}")
                if update.callback_query:
                    await update.callback_query.message.reply_text(question_text, reply_markup=keyboard)
                else:
                    await update.message.reply_text(question_text, reply_markup=keyboard)
        else:
            if update.callback_query:
                await update.callback_query.message.reply_text(question_text, reply_markup=keyboard)
            else:
                await update.message.reply_text(question_text, reply_markup=keyboard)
                
    except Exception as e:
        error_msg = f"❌ Savol yuborishda xatolik: {str(e)}"
        if update.callback_query:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_index: int):
    """Handle user's answer"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await query.message.reply_text("❌ Test tugagan. /test buyrug'i bilan yangi test boshlang.")
        return
    
    try:
        session = user_sessions[user_id]
        question = session['questions'][session['current']]
        
        if 'shuffled_correct_index' not in question:
            await query.message.reply_text("❌ Savol noto'g'ri formatda.")
            return
            
        is_correct = (answer_index == question['shuffled_correct_index'])
        
        # Record answer to statistics
        record_answer(
            user_id=user_id,
            question_id=question['id'],
            is_correct=is_correct,
            category=question.get('category', 'mixed')
        )
        
        if is_correct:
            session['correct'] += 1
            result_text = "✅ To'g'ri!\n\n"
        else:
            correct_letter = chr(65 + question['shuffled_correct_index'])
            result_text = f"❌ Noto'g'ri. To'g'ri javob: {correct_letter})\n\n"
        
        result_text += f"💡 {question['explanation']}"
        
        await query.message.reply_text(result_text)
        
        session['current'] += 1
        await send_question(update, context, user_id)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik: {str(e)}")

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show test results"""
    
    if user_id not in user_sessions:
        return
    
    try:
        session = user_sessions[user_id]
        correct = session['correct']
        total = len(session['questions'])
        percentage = (correct / total) * 100
        
        # Record test completion
        record_test_completion(
            user_id=user_id,
            category=session['category'],
            score=correct,
            total=total
        )
        
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == session['category']),
            config.CATEGORIES['d']
        )
        
        result_text = (
            f"✅ Test tugadi!\n\n"
            f"📚 Bo'lim: {cat_info['name']}\n"
            f"📊 Natija: {correct}/{total} ({percentage:.0f}%)\n\n"
        )
        
        if percentage >= 90:
            result_text += "🎉 Ajoyib! Imtihonga tayyor!"
        elif percentage >= 75:
            result_text += "👍 Yaxshi! Davom eting."
        elif percentage >= 50:
            result_text += "📚 Ko'proq mashq qiling."
        else:
            result_text += "❌ Bu bo'limni qayta o'rganishingiz kerak."
        
        keyboard = get_result_keyboard()
        
        if update.callback_query:
            await update.callback_query.message.reply_text(result_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(result_text, reply_markup=keyboard)
        
        del user_sessions[user_id]
        
    except Exception as e:
        error_msg = f"❌ Natijalarni ko'rsatishda xatolik: {str(e)}"
        if update.callback_query:
            await update.callback_query.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)