"""
Test session management WITH AUTO MESSAGE CLEANUP and LONGER EXPLANATION DELAY
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import get_random_questions
from user_stats import record_answer, record_test_completion
from utils.keyboards import get_answer_keyboard, get_result_keyboard
import config

# Store active test sessions with message tracking
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
        
        # Store session with message tracking
        user_sessions[user_id] = {
            'questions': questions,
            'current': 0,
            'correct': 0,
            'category': category,
            'last_question_id': None,  # Track for deletion
            'last_result_id': None      # Track for deletion
        }
        
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == category),
            config.CATEGORIES['d']
        )
        
        # Delete the category selection message
        try:
            await query.message.delete()
        except:
            pass
        
        # Send start message
        start_msg = await query.message.chat.send_message(
            f"🎯 <b>Test boshlandi!</b>\n\n"
            f"📚 Bo'lim: {cat_info['name']}\n"
            f"❓ Savollar: {len(questions)} ta\n\n"
            f"Omad! 🍀",
            parse_mode='HTML'
        )
        
        # Delete start message after 2 seconds
        await asyncio.sleep(2)
        try:
            await start_msg.delete()
        except:
            pass
        
        await send_question(query.message, context, user_id)
        
    except Exception as e:
        await query.message.chat.send_message(f"❌ Xatolik: {str(e)}")

import asyncio

async def send_question(message_or_update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send next question to user"""
    
    # Handle both message and Update objects
    if hasattr(message_or_update, 'message'):
        # It's an Update object
        message = message_or_update.message
    else:
        # It's already a message object
        message = message_or_update
    
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    current_num = session['current']
    questions = session['questions']
    
    # Check if test is complete
    if current_num >= len(questions):
        await show_results(message, context, user_id)
        return
    
    question = questions[current_num]
    
    try:
        # Use shuffled options
        keyboard = get_answer_keyboard(question['shuffled_options'])
        
        question_text = (
            f"❓ <b>Savol {current_num + 1}/{len(questions)}</b>\n\n"
            f"{question['question']}"
        )
        
        # Send with image if available
        if question.get('file_id'):
            try:
                sent_msg = await message.chat.send_photo(
                    photo=question['file_id'],
                    caption=question_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except:
                sent_msg = await message.chat.send_message(
                    question_text, 
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        else:
            sent_msg = await message.chat.send_message(
                question_text, 
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        # Store message ID for cleanup
        session['last_question_id'] = sent_msg.message_id
            
    except Exception as e:
        print(f"Error sending question: {e}")
        await message.chat.send_message(f"❌ Savol yuborishda xatolik: {str(e)}")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_index: int):
    """Handle user's answer WITH MESSAGE CLEANUP and LONGER EXPLANATION DELAY"""
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
            result_text = "✅ <b>To'g'ri!</b>\n\n"
        else:
            correct_letter = chr(65 + question['shuffled_correct_index'])
            result_text = f"❌ <b>Noto'g'ri. To'g'ri javob: {correct_letter})</b>\n\n"
        
        result_text += f"💡 {question['explanation']}"
        
        # Delete the question message
        try:
            await query.message.delete()
        except:
            pass
        
        # Send result
        result_msg = await query.message.chat.send_message(
            result_text,
            parse_mode='HTML'
        )
        
        # Store result message ID
        session['last_result_id'] = result_msg.message_id
        
        # Move to next question
        session['current'] += 1
        
        # LONGER WAIT TIME: 5-6 seconds (random between 5 and 6)
        import random
        wait_time = random.uniform(5.0, 6.0)
        await asyncio.sleep(wait_time)
        
        try:
            await result_msg.delete()
        except:
            pass
        
        await send_question(query.message, context, user_id)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik: {str(e)}")

async def show_results(message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show test results"""
    
    if user_id not in user_sessions:
        return
    
    try:
        session = user_sessions[user_id]
        correct = session['correct']
        total = len(session['questions'])
        percentage = (correct / total) * 100
        
        # Record test completion
        await record_test_completion(
            user_id=user_id,
            category=session['category'],
            score=correct,
            total=total,
            context=context
        )
        
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == session['category']),
            config.CATEGORIES['d']
        )
        
        result_text = (
            f"✅ <b>Test tugadi!</b>\n\n"
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
        
        await message.chat.send_message(
            result_text, 
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        del user_sessions[user_id]
        
    except Exception as e:
        await message.chat.send_message(f"❌ Natijalarni ko'rsatishda xatolik: {str(e)}")
