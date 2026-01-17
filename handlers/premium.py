"""
Premium subscription and payment handlers for PPD Bot
Handles Telegram Stars payments, subscriptions, and premium features
"""

from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta
from utils.premium import SubscriptionManager, PremiumTier

# Pricing in Telegram Stars
# 1 Star ≈ $0.01 USD
MONTHLY_PRICE_STARS = 500  # ≈ $4.99
YEARLY_PRICE_STARS = 4000  # ≈ $39.99 (Save 33%)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /premium command - Show subscription options
    """
    user_id = update.effective_user.id
    
    # Get current subscription status
    is_premium = await SubscriptionManager.is_premium(user_id)
    sub_info = SubscriptionManager.get_subscription_info(user_id)
    
    if is_premium:
        # User already has premium
        keyboard = [
            [InlineKeyboardButton("📊 My Subscription", callback_data='view_subscription')],
            [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
        ]
        
        message = (
            f"✨ <b>You're a Premium Member!</b>\n\n"
            f"📅 Plan: {sub_info['plan_name']}\n"
            f"📆 Expires: {sub_info['expires']}\n"
            f"⏳ Days remaining: {sub_info['days_remaining']}\n\n"
            f"🎉 Enjoy all premium features!\n\n"
            f"<i>Thank you for your support!</i>"
        )
    else:
        # Show upgrade options
        keyboard = [
            [InlineKeyboardButton("⭐ Monthly - 500 Stars", 
                                callback_data='buy_premium_monthly')],
            [InlineKeyboardButton("💎 Yearly - 4000 Stars (Save 33%!)", 
                                callback_data='buy_premium_yearly')],
            [InlineKeyboardButton("ℹ️ What is Telegram Stars?", 
                                callback_data='stars_info')],
            [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
        ]
        
        message = (
            "🌟 <b>Premium Subscription Plans</b>\n\n"
            "Choose your plan and unlock all features:\n\n"
            "📅 <b>Monthly Plan - 500 Stars</b>\n"
            "• Pay monthly\n"
            "• Cancel anytime\n"
            "• Full feature access\n\n"
            "📆 <b>Yearly Plan - 4000 Stars</b>\n"
            "• Pay once for 12 months\n"
            "• Save 2000 Stars (33% off!)\n"
            "• Best value for money\n\n"
            "✨ <b>Premium Benefits:</b>\n"
            "✅ Unlimited tests per day\n"
            "✅ Detailed answer explanations\n"
            "✅ Advanced analytics\n"
            "✅ Full test history\n"
            "✅ Export to PDF\n"
            "✅ Priority support\n"
            "✅ Ad-free experience\n\n"
            "<i>Select a plan below to continue</i>"
        )
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def stars_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Explain what Telegram Stars are
    """
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Buy Stars", url='https://t.me/PremiumBot')],
        [InlineKeyboardButton("« Back", callback_data='premium_menu')]
    ]
    
    message = (
        "⭐ <b>What are Telegram Stars?</b>\n\n"
        "Telegram Stars is an in-app currency you can use to:\n"
        "• Support content creators\n"
        "• Purchase digital goods and services\n"
        "• Access premium features in bots\n\n"
        "💰 <b>How to get Stars:</b>\n"
        "1. Tap 'Buy Stars' button below\n"
        "2. Choose amount to purchase\n"
        "3. Pay via Apple/Google Pay or card\n"
        "4. Stars appear in your account instantly\n\n"
        "🔒 <b>Secure & Easy:</b>\n"
        "• Instant delivery\n"
        "• Secure payment processing\n"
        "• No credit card info shared with bots\n\n"
        "<i>Approximately: 100 Stars ≈ $1 USD</i>"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def buy_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle premium purchase button clicks
    """
    query = update.callback_query
    await query.answer()
    
    # Extract plan type from callback data
    plan = query.data.split('_')[-1]  # 'monthly' or 'yearly'
    
    # Send invoice
    await send_premium_invoice(update, context, plan)

async def send_premium_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str):
    """
    Send payment invoice to user
    
    Args:
        update: Update object
        context: Context object
        plan: 'monthly' or 'yearly'
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    if plan == 'monthly':
        title = "PPD Bot Premium - Monthly"
        description = "Get 1 month of unlimited access to all premium features"
        amount = MONTHLY_PRICE_STARS
        duration_days = 30
    else:  # yearly
        title = "PPD Bot Premium - Yearly"
        description = "Get 12 months of unlimited access (Save 33%!)"
        amount = YEARLY_PRICE_STARS
        duration_days = 365
    
    # Create price list (amount in smallest currency unit, for Stars it's just the amount)
    prices = [LabeledPrice("Premium Subscription", amount)]
    
    # Create payload to identify this purchase
    payload = f"{plan}_{user_id}_{datetime.now().timestamp()}"
    
    try:
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Empty string for Telegram Stars
            currency="XTR",  # Telegram Stars currency code
            prices=prices,
            start_parameter=f"premium-{plan}",
            photo_url="https://via.placeholder.com/512x512.png?text=Premium",  # Optional: Add your premium badge image
            photo_size=512,
            photo_width=512,
            photo_height=512,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
        
        # Inform user
        await query.message.reply_text(
            "💳 <b>Payment Invoice Sent!</b>\n\n"
            "Please complete the payment to activate your premium subscription.\n\n"
            "<i>Your subscription will start immediately after payment.</i>",
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"Error sending invoice: {e}")
        await query.message.reply_text(
            "❌ <b>Error</b>\n\n"
            "Sorry, there was an error processing your request. "
            "Please try again later or contact support.",
            parse_mode='HTML'
        )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle pre-checkout queries
    This is called before the payment is processed
    """
    query = update.pre_checkout_query
    
    # Validate the invoice payload
    try:
        payload_parts = query.invoice_payload.split('_')
        plan_type = payload_parts[0]
        user_id = int(payload_parts[1])
        
        # Verify user_id matches
        if user_id != query.from_user.id:
            await query.answer(
                ok=False,
                error_message="Invalid purchase request. Please try again."
            )
            return
        
        # Verify plan type is valid
        if plan_type not in ['monthly', 'yearly']:
            await query.answer(
                ok=False,
                error_message="Invalid subscription plan."
            )
            return
        
        # Everything is OK, proceed with payment
        await query.answer(ok=True)
        
    except Exception as e:
        print(f"Pre-checkout error: {e}")
        await query.answer(
            ok=False,
            error_message="Error processing payment. Please try again."
        )

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle successful payment
    This is called after payment is successfully processed
    """
    payment = update.message.successful_payment
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Unknown"
    
    # Extract plan details from payload
    try:
        payload_parts = payment.invoice_payload.split('_')
        plan_type = payload_parts[0]  # 'monthly' or 'yearly'
        
        # Calculate subscription dates
        start_date = datetime.now()
        duration_days = 30 if plan_type == 'monthly' else 365
        end_date = start_date + timedelta(days=duration_days)
        
        # Save subscription to database
        success = SubscriptionManager.save_subscription(
            user_id=user_id,
            plan_type=PremiumTier.PREMIUM,
            start_date=start_date,
            end_date=end_date,
            payment_id=payment.telegram_payment_charge_id
        )
        
        if not success:
            await update.message.reply_text(
                "⚠️ <b>Payment Received but Error Occurred</b>\n\n"
                "Your payment was successful but there was an error activating your subscription. "
                "Please contact support with this payment ID:\n\n"
                f"<code>{payment.telegram_payment_charge_id}</code>",
                parse_mode='HTML'
            )
            return
        
        # Save payment record
        SubscriptionManager.save_payment(
            payment_id=payment.telegram_payment_charge_id,
            user_id=user_id,
            amount=payment.total_amount,
            currency=payment.currency,
            plan_type=plan_type,
            payment_provider='telegram_stars'
        )
        
        # Send success message
        plan_emoji = "📅" if plan_type == 'monthly' else "📆"
        plan_name = "Monthly" if plan_type == 'monthly' else "Yearly"
        
        await update.message.reply_text(
            f"✅ <b>Payment Successful!</b>\n\n"
            f"🎉 Welcome to Premium, {update.message.from_user.first_name}!\n\n"
            f"{plan_emoji} <b>Plan:</b> {plan_name}\n"
            f"🗓 <b>Active until:</b> {end_date.strftime('%Y-%m-%d')}\n"
            f"💳 <b>Payment ID:</b> <code>{payment.telegram_payment_charge_id}</code>\n\n"
            f"✨ <b>Your Premium Benefits:</b>\n"
            f"✅ Unlimited tests per day\n"
            f"✅ Detailed answer explanations\n"
            f"✅ Advanced analytics\n"
            f"✅ Full test history\n"
            f"✅ Export to PDF\n"
            f"✅ Priority support\n\n"
            f"Start exploring with /start",
            parse_mode='HTML'
        )
        
        # Log for admin
        print(f"New premium subscription: User {user_id} (@{username}) - {plan_name} plan")
        
    except Exception as e:
        print(f"Error processing successful payment: {e}")
        await update.message.reply_text(
            "⚠️ <b>Payment Error</b>\n\n"
            "There was an error activating your subscription. "
            "Please contact support with this payment ID:\n\n"
            f"<code>{payment.telegram_payment_charge_id}</code>",
            parse_mode='HTML'
        )

async def view_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show user's current subscription details
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    sub_info = SubscriptionManager.get_subscription_info(user_id)
    
    keyboard = [
        [InlineKeyboardButton("« Back", callback_data='premium_menu')]
    ]
    
    if sub_info['is_premium']:
        message = (
            f"✨ <b>Your Premium Subscription</b>\n\n"
            f"📋 <b>Plan:</b> {sub_info['plan_name']}\n"
            f"📅 <b>Status:</b> {sub_info['status'].capitalize()}\n"
            f"📆 <b>Expires:</b> {sub_info['expires']}\n"
            f"⏳ <b>Days remaining:</b> {sub_info['days_remaining']}\n\n"
            f"✅ <b>Active Features:</b>\n"
            f"• Unlimited tests\n"
            f"• Answer explanations\n"
            f"• Advanced analytics\n"
            f"• Full test history\n"
            f"• PDF export\n"
            f"• Priority support\n\n"
            f"<i>Thank you for being a premium member!</i>"
        )
    else:
        keyboard.insert(0, [InlineKeyboardButton("⭐ Upgrade to Premium", 
                                                 callback_data='buy_premium_monthly')])
        message = (
            f"📋 <b>Your Subscription</b>\n\n"
            f"Plan: {sub_info['plan_name']}\n\n"
            f"🔒 <b>Limited Features:</b>\n"
            f"• 5 tests per day\n"
            f"• No explanations\n"
            f"• Basic analytics\n"
            f"• Limited history (10 tests)\n\n"
            f"Upgrade to unlock all features!"
        )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def premium_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show premium menu (similar to premium_command but for callbacks)
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_premium = await SubscriptionManager.is_premium(user_id)
    sub_info = SubscriptionManager.get_subscription_info(user_id)
    
    if is_premium:
        keyboard = [
            [InlineKeyboardButton("📊 My Subscription", callback_data='view_subscription')],
            [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
        ]
        
        message = (
            f"✨ <b>You're a Premium Member!</b>\n\n"
            f"📅 Plan: {sub_info['plan_name']}\n"
            f"📆 Expires: {sub_info['expires']}\n"
            f"⏳ Days remaining: {sub_info['days_remaining']}\n\n"
            f"🎉 Enjoy all premium features!"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("⭐ Monthly - 500 Stars", 
                                callback_data='buy_premium_monthly')],
            [InlineKeyboardButton("💎 Yearly - 4000 Stars (Save 33%!)", 
                                callback_data='buy_premium_yearly')],
            [InlineKeyboardButton("ℹ️ What is Telegram Stars?", 
                                callback_data='stars_info')],
            [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
        ]
        
        message = (
            "🌟 <b>Premium Subscription Plans</b>\n\n"
            "✨ <b>Premium Benefits:</b>\n"
            "✅ Unlimited tests\n"
            "✅ Detailed explanations\n"
            "✅ Advanced analytics\n"
            "✅ Full history\n"
            "✅ Export to PDF\n"
            "✅ Priority support\n\n"
            "💳 Choose your plan below:"
        )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# Register handlers
def register_premium_handlers(application):
    """
    Register all premium-related handlers
    
    Args:
        application: Application instance
    """
    application.add_handler(CommandHandler('premium', premium_command))
    application.add_handler(CallbackQueryHandler(buy_premium_callback, pattern='^buy_premium_'))
    application.add_handler(CallbackQueryHandler(view_subscription_callback, pattern='^view_subscription$'))
    application.add_handler(CallbackQueryHandler(premium_menu_callback, pattern='^premium_menu$'))
    application.add_handler(CallbackQueryHandler(stars_info_callback, pattern='^stars_info$'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    print("Premium handlers registered successfully")
