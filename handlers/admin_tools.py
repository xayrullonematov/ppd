"""
Advanced admin tools for question management
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import load_questions, save_questions, get_category_stats, get_total_count

# Store admin state
admin_state = {}

async def admin_tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin tools menu"""
    user_id = update.effective_user.id
    
    if user_id != config.ADMIN_ID:
        await update.message.reply_text("❌ Ruxsat yo'q")
        return
    
    keyboard = [
        [InlineKeyboardButton("📝 Savollarni ko'rish", callback_data="admin_list")],
        [InlineKeyboardButton("🔍 Qidirish", callback_data="admin_search")],
        [InlineKeyboardButton("📊 Batafsil statistika", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton("📥 Export", callback_data="admin_export")],
        [InlineKeyboardButton("🏠 Orqaga", callback_data="admin_back")]
    ]
    
    await update.message.reply_text(
        "🔧 Admin asboblari\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """List all questions with pagination"""
    query = update.callback_query
    await query.answer()
    
    questions = load_questions()
    
    if not questions:
        await query.edit_message_text("❌ Savollar yo'q.")
        return
    
    # Pagination
    per_page = 5
    start = page * per_page
    end = start + per_page
    total_pages = (len(questions) + per_page - 1) // per_page
    
    page_questions = questions[start:end]
    
    text = f"📚 Savollar ({start + 1}-{min(end, len(questions))} / {len(questions)})\n\n"
    
    for q in page_questions:
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == q.get('category', 'mixed')),
            config.CATEGORIES['d']
        )
        text += f"#{q['id']} {cat_info['emoji']} {q['question'][:50]}...\n"
    
    # Pagination buttons
    keyboard = []
    
    # Previous/Next buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_list_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ Keyingi", callback_data=f"admin_list_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Action buttons for each question
    for q in page_questions:
        keyboard.append([
            InlineKeyboardButton(f"✏️ #{q['id']}", callback_data=f"admin_edit_{q['id']}"),
            InlineKeyboardButton(f"🗑️ #{q['id']}", callback_data=f"admin_delete_{q['id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_tools")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_question_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int):
    """Show detailed view of a question"""
    query = update.callback_query
    await query.answer()
    
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        await query.edit_message_text("❌ Savol topilmadi.")
        return
    
    cat_info = next(
        (cat for cat in config.CATEGORIES.values() if cat['id'] == question.get('category', 'mixed')),
        config.CATEGORIES['d']
    )
    
    text = (
        f"📝 Savol #{question['id']}\n\n"
        f"📚 Kategoriya: {cat_info['name']}\n\n"
        f"❓ Savol:\n{question['question']}\n\n"
        f"Javoblar:\n"
    )
    
    for i, opt in enumerate(question['options']):
        prefix = "✅" if i == question['correct_index'] else "   "
        text += f"{prefix} {chr(65+i)}) {opt}\n"
    
    text += f"\n💡 Tushuntirish:\n{question['explanation']}"
    
    if question.get('file_id'):
        text += "\n\n🖼️ Rasm: Mavjud"
    
    keyboard = [
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin_edit_start_{question_id}"),
            InlineKeyboardButton("🗑️ O'chirish", callback_data=f"admin_delete_confirm_{question_id}")
        ],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_list")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int, confirmed: bool = False):
    """Delete a question"""
    query = update.callback_query
    await query.answer()
    
    if not confirmed:
        # Show confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"admin_delete_yes_{question_id}"),
                InlineKeyboardButton("❌ Yo'q", callback_data=f"admin_edit_{question_id}")
            ]
        ]
        await query.edit_message_text(
            f"⚠️ Savol #{question_id}ni o'chirishni tasdiqlaysizmi?\n\n"
            f"Bu amal qaytarilmaydi!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Delete confirmed
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        await query.edit_message_text("❌ Savol topilmadi.")
        return
    
    # Remove question
    questions = [q for q in questions if q['id'] != question_id]
    save_questions(questions)
    
    await query.edit_message_text(
        f"✅ Savol #{question_id} o'chirildi!\n\n"
        f"Jami savollar: {len(questions)}"
    )

async def edit_question_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int):
    """Show edit menu for a question"""
    query = update.callback_query
    await query.answer()
    
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        await query.edit_message_text("❌ Savol topilmadi.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📝 Savol matnini tahrirlash", callback_data=f"admin_edit_question_{question_id}")],
        [InlineKeyboardButton("🔤 Javoblarni tahrirlash", callback_data=f"admin_edit_options_{question_id}")],
        [InlineKeyboardButton("✅ To'g'ri javobni o'zgartirish", callback_data=f"admin_edit_correct_{question_id}")],
        [InlineKeyboardButton("💡 Tushuntirishni tahrirlash", callback_data=f"admin_edit_explanation_{question_id}")],
        [InlineKeyboardButton("📚 Kategoriyani o'zgartirish", callback_data=f"admin_edit_category_{question_id}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_edit_{question_id}")]
    ]
    
    await query.edit_message_text(
        f"✏️ Savol #{question_id}ni tahrirlash\n\n"
        f"Nimani o'zgartirmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE, question_id: int, field: str):
    """Start editing a specific field"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Store edit state
    admin_state[user_id] = {
        'action': 'edit_field',
        'question_id': question_id,
        'field': field
    }
    
    field_names = {
        'question': 'savol matni',
        'explanation': 'tushuntirish',
        'correct': "to'g'ri javob raqami (0-3)",
        'category': 'kategoriya (a/b/c/d)'
    }
    
    await query.edit_message_text(
        f"✏️ Yangi {field_names.get(field, field)}ni yuboring:\n\n"
        f"Bekor qilish uchun /cancel"
    )

async def handle_admin_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin edits"""
    user_id = update.effective_user.id
    
    if user_id not in admin_state:
        return
    
    state = admin_state[user_id]
    
    if state['action'] != 'edit_field':
        return
    
    question_id = state['question_id']
    field = state['field']
    new_value = update.message.text.strip()
    
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        await update.message.reply_text("❌ Savol topilmadi.")
        del admin_state[user_id]
        return
    
    try:
        if field == 'question':
            question['question'] = new_value
        elif field == 'explanation':
            question['explanation'] = new_value
        elif field == 'correct':
            correct_index = int(new_value)
            if correct_index not in [0, 1, 2, 3]:
                raise ValueError("Javob raqami 0-3 orasida bo'lishi kerak")
            question['correct_index'] = correct_index
        elif field == 'category':
            category_letter = new_value.lower()
            if category_letter not in config.CATEGORIES:
                raise ValueError("Kategoriya a, b, c yoki d bo'lishi kerak")
            question['category'] = config.get_category_id(category_letter)
        
        save_questions(questions)
        
        await update.message.reply_text(
            f"✅ Savol #{question_id} yangilandi!\n\n"
            f"Yangi qiymat: {new_value}"
        )
        
    except ValueError as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Kutilmagan xatolik: {str(e)}")
    
    del admin_state[user_id]

async def search_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start question search"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    admin_state[user_id] = {
        'action': 'search'
    }
    
    await query.edit_message_text(
        "🔍 Qidiruv\n\n"
        "Qidiruv so'zini kiriting:\n"
        "(Savol matni, javoblar yoki ID bo'yicha)\n\n"
        "Bekor qilish: /cancel"
    )

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search query"""
    user_id = update.effective_user.id
    
    if user_id not in admin_state or admin_state[user_id]['action'] != 'search':
        return
    
    search_term = update.message.text.strip().lower()
    questions = load_questions()
    
    # Search by ID if numeric
    if search_term.isdigit():
        results = [q for q in questions if q['id'] == int(search_term)]
    else:
        # Search in question text and options
        results = []
        for q in questions:
            if (search_term in q['question'].lower() or
                any(search_term in opt.lower() for opt in q['options']) or
                search_term in q.get('explanation', '').lower()):
                results.append(q)
    
    if not results:
        await update.message.reply_text("❌ Hech narsa topilmadi.")
        del admin_state[user_id]
        return
    
    text = f"🔍 Topildi: {len(results)} ta\n\n"
    
    for q in results[:10]:  # Show first 10
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == q.get('category', 'mixed')),
            config.CATEGORIES['d']
        )
        text += f"#{q['id']} {cat_info['emoji']} {q['question'][:60]}...\n"
    
    if len(results) > 10:
        text += f"\n... va yana {len(results) - 10} ta"
    
    # Add buttons for first 5 results
    keyboard = []
    for q in results[:5]:
        keyboard.append([
            InlineKeyboardButton(f"✏️ #{q['id']}", callback_data=f"admin_edit_{q['id']}"),
            InlineKeyboardButton(f"🗑️ #{q['id']}", callback_data=f"admin_delete_{q['id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_tools")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    del admin_state[user_id]

async def detailed_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    query = update.callback_query
    await query.answer()
    
    questions = load_questions()
    stats = get_category_stats()
    
    # Calculate stats
    total = len(questions)
    
    # Questions by category
    category_breakdown = {}
    for letter, cat_info in config.CATEGORIES.items():
        if cat_info['id'] != 'mixed':
            count = stats.get(cat_info['id'], 0)
            category_breakdown[cat_info['name']] = count
    
    # Questions with images
    with_images = sum(1 for q in questions if q.get('file_id'))
    without_images = total - with_images
    
    # Average explanation length
    avg_explanation = sum(len(q.get('explanation', '')) for q in questions) / total if total > 0 else 0
    
    # Recent additions (last 5)
    recent = sorted(questions, key=lambda x: x['id'], reverse=True)[:5]
    
    text = (
        "📊 Batafsil statistika\n\n"
        f"📚 Jami savollar: {total}\n\n"
        f"Kategoriyalar:\n"
    )
    
    for cat_name, count in category_breakdown.items():
        percentage = (count / total * 100) if total > 0 else 0
        text += f"  • {cat_name}: {count} ({percentage:.1f}%)\n"
    
    text += (
        f"\n🖼️ Rasmlar:\n"
        f"  • Rasm bilan: {with_images} ({with_images/total*100:.1f}%)\n"
        f"  • Rasmsiz: {without_images} ({without_images/total*100:.1f}%)\n\n"
        f"📝 O'rtacha tushuntirish: {avg_explanation:.0f} belgi\n\n"
        f"🆕 So'nggi qo'shilganlar:\n"
    )
    
    for q in recent:
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == q.get('category', 'mixed')),
            config.CATEGORIES['d']
        )
        text += f"  #{q['id']} {cat_info['emoji']} {q['question'][:40]}...\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_tools")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def export_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export questions as text"""
    query = update.callback_query
    await query.answer()
    
    questions = load_questions()
    
    # Create export text
    export_text = f"📥 PDD Test Bot - Savollar Export\n"
    export_text += f"Jami: {len(questions)} ta savol\n"
    export_text += f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    export_text += "="*50 + "\n\n"
    
    for q in questions:
        cat_info = next(
            (cat for cat in config.CATEGORIES.values() if cat['id'] == q.get('category', 'mixed')),
            config.CATEGORIES['d']
        )
        
        export_text += f"#{q['id']} - {cat_info['name']}\n"
        export_text += f"Savol: {q['question']}\n\n"
        
        for i, opt in enumerate(q['options']):
            prefix = "✅" if i == q['correct_index'] else "  "
            export_text += f"{prefix} {chr(65+i)}) {opt}\n"
        
        export_text += f"\nTushuntirish: {q['explanation']}\n"
        export_text += "\n" + "-"*50 + "\n\n"
    
    # Send as file
    from io import BytesIO
    file = BytesIO(export_text.encode('utf-8'))
    file.name = f"questions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    await query.message.reply_document(
        document=file,
        filename=file.name,
        caption="📥 Barcha savollar eksport qilindi"
    )
    
    await query.answer("✅ Eksport tayyor!")

# For imports
from datetime import datetime
