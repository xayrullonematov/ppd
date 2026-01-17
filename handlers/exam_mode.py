"""
Timed Exam Mode - Real exam simulation with countdown timer and MESSAGE CLEANUP
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
from datetime import datetime, timedelta
from database import get_random_questions
from user_stats import record_answer, record_test_completion
from utils.premium import SubscriptionManager
from utils.keyboards import get_answer_keyboard
import config

# Store active exam sessions
exam_sessions = {}

# Exam configuration
EXAM_QUESTIONS = 20
EXAM_TIME_MINUTES = 20
EXAM_TIME_SECONDS = EXAM_TIME_MINUTES * 60

class ExamSession:
    """Class to manage exam session state"""
    def __init__(self, user_id: int, questions: list):
        self.user_id = user_id
        self.questions = questions
        self.current = 0
        self.correct = 0
        self.answers = {}  # question_id -> (answer_index, is_correct)
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=EXAM_TIME_SECONDS)
        self.timer_task = None
        self.is_active = True
        self.last_question_id = None  # For message cleanup
        
    def time_remaining(self) -> int:
        """Get seconds remaining"""
        if not self.is_active:
            return 0
        remaining = (self.end_time - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def time_remaining_formatted(self) -> str:
        """Get formatted time remaining (MM:SS)"""
        seconds = self.time_remaining()
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def is_expired(self) -> bool:
        """Check if exam time has expired"""
        return self.time_remaining() <= 0
    
    def submit_answer(self, question_id: int, answer_index: int, is_correct: bool):
        """Record answer"""
        self.answers[question_id] = (answer_index, is_correct)
        if is_correct:
            self.correct += 1


async def start_exam(update, context):
    user_id = update.effective_user.id
    
    # Check daily limit
    limit_check = await SubscriptionManager.check_daily_limit(user_id)
    if not limit_check['allowed']:
        # Show upgrade prompt
        # (see example in exam_premium_integration.py)
        return

async def exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start timed exam mode"""
    user_id = update.effective_user.id
    
    # Check if user already has active exam
    if user_id in exam_sessions and exam_sessions[user_id].is_active:
        remaining = exam_sessions[user_id].time_remaining_formatted()
        text = (
            f"⚠️ Sizda faol imtihon bor!\n\n"
            f"⏰ Qolgan vaqt: {remaining}\n\n"
            f"Davom etish uchun savolga javob bering."
        )
        
        # Check if called from callback or command
        if update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return
    
    # Show exam info and confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Boshlash", callback_data="exam_start")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="exam_cancel")]
    ]
    
    text = (
        "🎓 <b>HAQIQIY IMTIHON SIMULYATSIYASI</b>\n\n"
        f"📋 Savollar: {EXAM_QUESTIONS} ta\n"
        f"⏰ Vaqt: {EXAM_TIME_MINUTES} daqiqa\n"
        f"⚡ Avtomatik topshirish: Ha\n\n"
        "⚠️ <b>Diqqat:</b>\n"
        "• Vaqt tugashi bilan test avtomatik topshiriladi\n"
        "• Orqaga qaytib javobni o'zgartira olmaysiz\n"
        "• Har bir savol faqat bir marta ko'rsatiladi\n"
        "• Tushuntirish ko'rsatilmaydi (haqiqiy imtihon kabi)\n\n"
        "Tayyor bo'lsangiz boshlang!"
    )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if called from callback or command
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def start_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize and start exam"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        # Get random questions from all categories
        questions = get_random_questions('mixed', count=EXAM_QUESTIONS)
        
        if len(questions) < EXAM_QUESTIONS:
            await query.edit_message_text(
                f"❌ Imtihon uchun kamida {EXAM_QUESTIONS} ta savol kerak.\n"
                f"Hozir bazada: {len(questions)} ta savol."
            )
            return
        
        # Create exam session
        session = ExamSession(user_id, questions)
        exam_sessions[user_id] = session
        
        # Delete the info message
        try:
            await query.message.delete()
        except:
            pass
        
        # Send start message
        start_msg = await query.message.chat.send_message(
            f"🎓 <b>Imtihon boshlandi!</b>\n\n"
            f"⏰ Vaqt: {EXAM_TIME_MINUTES} daqiqa\n"
            f"📊 Savollar: {EXAM_QUESTIONS} ta\n\n"
            f"Omad! 🍀",
            parse_mode='HTML'
        )
        
        # Start countdown timer
        session.timer_task = asyncio.create_task(
            countdown_timer(user_id, query.message, context)
        )
        
        # Delete start message after 2 seconds
        await asyncio.sleep(2)
        try:
            await start_msg.delete()
        except:
            pass
        
        # Send first question
        await send_exam_question(query.message, context, user_id)
        
    except Exception as e:
        await query.message.chat.send_message(f"❌ Xatolik: {str(e)}")
        if user_id in exam_sessions:
            del exam_sessions[user_id]

async def send_exam_question(message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send next exam question with timer and MESSAGE CLEANUP"""
    if user_id not in exam_sessions:
        return
    
    session = exam_sessions[user_id]
    
    # Check if exam is expired
    if session.is_expired():
        await finish_exam(message, context, user_id, auto_submit=True)
        return
    
    # Check if all questions answered
    if session.current >= len(session.questions):
        await finish_exam(message, context, user_id, auto_submit=False)
        return
    
    question = session.questions[session.current]
    
    try:
        # Build question text with timer
        time_remaining = session.time_remaining_formatted()
        question_text = (
            f"⏰ {time_remaining} | "
            f"📊 {session.current + 1}/{len(session.questions)}\n\n"
            f"❓ {question['question']}"
        )
        
        keyboard = get_answer_keyboard(question['shuffled_options'])
        
        # Send with image if available
        if question.get('file_id'):
            try:
                sent_msg = await message.chat.send_photo(
                    photo=question['file_id'],
                    caption=question_text,
                    reply_markup=keyboard
                )
            except:
                sent_msg = await message.chat.send_message(
                    question_text, 
                    reply_markup=keyboard
                )
        else:
            sent_msg = await message.chat.send_message(
                question_text, 
                reply_markup=keyboard
            )
        
        # Store message ID for cleanup
        session.last_question_id = sent_msg.message_id
            
    except Exception as e:
        print(f"Error sending exam question: {e}")
        await message.chat.send_message(f"❌ Xatolik: {str(e)}")

async def handle_exam_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_index: int):
    """Handle answer during timed exam WITH MESSAGE CLEANUP"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id not in exam_sessions:
        await query.message.reply_text("❌ Faol imtihon topilmadi. /exam")
        return
    
    session = exam_sessions[user_id]
    
    # Check if expired
    if session.is_expired():
        await finish_exam(query.message, context, user_id, auto_submit=True)
        return
    
    try:
        question = session.questions[session.current]
        
        if 'shuffled_correct_index' not in question:
            await query.message.reply_text("❌ Savol formati noto'g'ri.")
            return
        
        is_correct = (answer_index == question['shuffled_correct_index'])
        
        # Record answer
        session.submit_answer(question['id'], answer_index, is_correct)
        
        # Record in statistics
        record_answer(
            user_id=user_id,
            question_id=question['id'],
            is_correct=is_correct,
            category=question.get('category', 'mixed')
        )
        
        # DELETE the question message (NO EXPLANATION shown!)
        try:
            await query.message.delete()
        except:
            pass
        
        # Move to next question
        session.current += 1
        
        # Send next question IMMEDIATELY (no delay, no explanation)
        await send_exam_question(query.message, context, user_id)
        
    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik: {str(e)}")

async def countdown_timer(user_id: int, message, context: ContextTypes.DEFAULT_TYPE):
    """Background countdown timer"""
    try:
        session = exam_sessions.get(user_id)
        if not session:
            return
        
        # Update timer every 10 seconds
        while session.is_active and not session.is_expired():
            await asyncio.sleep(10)
            
            if user_id not in exam_sessions:
                break
            
            session = exam_sessions[user_id]
            
            # Send warning at 5 minutes
            remaining = session.time_remaining()
            if 290 <= remaining <= 300 and session.is_active:
                await message.chat.send_message(
                    "⚠️ <b>OGOHLANTIRISH</b>\n\n"
                    "⏰ 5 daqiqa qoldi!\n"
                    "Iltimos, tezroq javob bering.",
                    parse_mode='HTML'
                )
            
            # Send warning at 1 minute
            elif 50 <= remaining <= 60 and session.is_active:
                await message.chat.send_message(
                    "🚨 <b>DIQQAT!</b>\n\n"
                    "⏰ 1 daqiqa qoldi!\n"
                    "Oxirgi imkoniyat!",
                    parse_mode='HTML'
                )
        
        # Time's up!
        if session.is_active:
            await finish_exam(message, context, user_id, auto_submit=True)
            
    except asyncio.CancelledError:
        # Timer was cancelled (exam finished early)
        pass
    except Exception as e:
        print(f"Timer error: {e}")

async def finish_exam(message, context: ContextTypes.DEFAULT_TYPE, user_id: int, auto_submit: bool = False):
    """Finish exam and show results"""
    if user_id not in exam_sessions:
        return
    
    session = exam_sessions[user_id]
    session.is_active = False
    
    # Cancel timer
    if session.timer_task:
        session.timer_task.cancel()
    
    try:
        # Calculate results
        total = len(session.questions)
        answered = len(session.answers)
        correct = session.correct
        unanswered = total - answered
        percentage = (correct / total) * 100
        
        # Calculate time taken
        time_taken = datetime.now() - session.start_time
        minutes_taken = int(time_taken.total_seconds() / 60)
        seconds_taken = int(time_taken.total_seconds() % 60)
        
        # Record completion
        await record_test_completion(
            user_id=user_id,
            category='exam',
            score=correct,
            total=total,
            context=context
        )
        
        # Determine pass/fail (70% to pass)
        passed = percentage >= 70
        
        # Build result message
        result_text = (
            f"{'🎉' if passed else '❌'} <b>IMTIHON YAKUNLANDI!</b>\n\n"
            f"{'⏰ Vaqt tugadi - Avtomatik topshirildi' if auto_submit else '✅ Barcha savollar javoblandi'}\n\n"
            f"📊 <b>NATIJALAR:</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ To'g'ri: {correct}/{total}\n"
            f"❌ Noto'g'ri: {answered - correct}/{total}\n"
            f"⚠️ Javobsiz: {unanswered}/{total}\n"
            f"📈 Ball: {percentage:.1f}%\n"
            f"⏱️ Vaqt: {minutes_taken}:{seconds_taken:02d}\n\n"
        )
        
        if passed:
            result_text += (
                "🎊 <b>TABRIKLAYMIZ!</b>\n"
                "Siz imtihondan o'tdingiz! ✅\n\n"
                "Haqiqiy imtihonga tayyor bo'lishingiz mumkin!"
            )
        else:
            result_text += (
                "📚 <b>O'tmadingiz</b>\n"
                "Minimal ball: 70%\n\n"
                "Ko'proq mashq qiling va qaytadan urinib ko'ring!"
            )
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Qayta imtihon", callback_data="exam_start")],
            [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")]
        ]
        
        await message.chat.send_message(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        await message.chat.send_message(f"❌ Natijalarni ko'rsatishda xatolik: {str(e)}")
    
    # Clean up session
    del exam_sessions[user_id]

async def cancel_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel active exam"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if user_id in exam_sessions:
        session = exam_sessions[user_id]
        session.is_active = False
        if session.timer_task:
            session.timer_task.cancel()
        del exam_sessions[user_id]
    
    await query.edit_message_text(
        "✅ Imtihon bekor qilindi.\n\n"
        "/exam - Qayta boshlash"
    )

# Helper functions
def has_active_exam(user_id: int) -> bool:
    """Check if user has an active exam"""
    return user_id in exam_sessions and exam_sessions[user_id].is_active

def get_exam_info(user_id: int) -> dict:
    """Get exam session info"""
    if user_id not in exam_sessions:
        return None
    
    session = exam_sessions[user_id]
    return {
        'active': session.is_active,
        'current': session.current,
        'total': len(session.questions),
        'time_remaining': session.time_remaining_formatted(),
        'answers': len(session.answers),
        'correct': session.correct
    }
