from pyrogram import Client, filters
from pyrogram.types import Message
from database import Database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdminHandler:
    def __init__(self, bot: Client, db: Database, user_manager, owner_id: int):
        self.bot = bot
        self.db = db
        self.user_manager = user_manager
        self.owner_id = owner_id
        self.owner_ad_state = {}
    
    async def payments_command(self, message: Message):
        """View pending payments"""
        if message.from_user.id != self.owner_id:
            return
        
        pending = self.db.get_pending_payments()
        
        if not pending:
            await message.reply_text("✅ No pending payments!")
            return
        
        text = "💰 **Pending Payment Requests:**\n\n"
        
        for payment in pending:
            text += f"**Payment #{payment['id']}**\n"
            text += f"User: @{payment['username'] or 'unknown'} (ID: {payment['user_id']})\n"
            text += f"Plan: {payment['plan_type']}\n"
            text += f"Amount: ₹{payment['amount']}\n"
            text += f"Date: {payment['created_at']}\n"
            text += f"\nApprove: /approve {payment['id']}\n"
            text += f"Reject: /reject {payment['id']}\n\n"
            text += "─" * 30 + "\n\n"
        
        await message.reply_text(text)
        
        # Send payment proofs
        for payment in pending:
            await self.bot.send_photo(
                self.owner_id,
                payment['payment_proof'],
                caption=f"Payment #{payment['id']} - User {payment['user_id']}"
            )
    
    async def approve_command(self, message: Message):
        """Approve a payment"""
        if message.from_user.id != self.owner_id:
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("Usage: /approve <payment_id>")
            return
        
        try:
            payment_id = int(args[1])
        except:
            await message.reply_text("❌ Invalid payment ID")
            return
        
        # Get payment details
        pending = self.db.get_pending_payments()
        payment = next((p for p in pending if p['id'] == payment_id), None)
        
        if not payment:
            await message.reply_text("❌ Payment not found")
            return
        
        # Approve payment
        self.db.approve_payment(payment_id)
        
        # Update user to premium
        from config import PRICING
        plan_info = PRICING.get(payment['plan_type'], PRICING['basic'])
        self.db.update_user_premium(payment['user_id'], True, plan_info['duration_days'])
        
        # Notify user
        await self.bot.send_message(
            payment['user_id'],
            f"🎉 **Payment Approved!**\n\n"
            f"Your {payment['plan_type']} plan has been activated!\n"
            f"Duration: {plan_info['duration_days']} days\n\n"
            f"✨ Premium features unlocked:\n"
            f"• Custom delays (10s - 10min)\n"
            f"• No forced footer\n"
            f"• No owner ads\n"
            f"• Free bio/name\n\n"
            f"Thank you for upgrading! 🚀"
        )
        
        await message.reply_text(
            f"✅ Payment #{payment_id} approved!\n"
            f"User {payment['user_id']} is now premium."
        )
    
    async def reject_command(self, message: Message):
        """Reject a payment"""
        if message.from_user.id != self.owner_id:
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("Usage: /reject <payment_id> [reason]")
            return
        
        try:
            payment_id = int(args[1])
            reason = " ".join(args[2:]) if len(args) > 2 else "Payment verification failed"
        except:
            await message.reply_text("❌ Invalid payment ID")
            return
        
        # Get payment details
        pending = self.db.get_pending_payments()
        payment = next((p for p in pending if p['id'] == payment_id), None)
        
        if not payment:
            await message.reply_text("❌ Payment not found")
            return
        
        # Update payment status
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE payments 
            SET status = 'rejected'
            WHERE id = ?
        """, (payment_id,))
        conn.commit()
        conn.close()
        
        # Notify user
        await self.bot.send_message(
            payment['user_id'],
            f"❌ **Payment Rejected**\n\n"
            f"Payment ID: #{payment_id}\n"
            f"Reason: {reason}\n\n"
            f"Please contact support or try again with correct payment proof."
        )
        
        await message.reply_text(f"✅ Payment #{payment_id} rejected")
    
    async def ownerads_command(self, message: Message):
        """Save owner ad"""
        if message.from_user.id != self.owner_id:
            return
        
        self.owner_ad_state[self.owner_id] = "awaiting_ad"
        
        await message.reply_text(
            "📢 **Save Owner Promotional Ad**\n\n"
            "Send me the advertisement you want to save.\n"
            "This will be used for promotional purposes on free user accounts.\n\n"
            "You can send:\n"
            "• Text message\n"
            "• Photo with caption\n"
            "• Video with caption\n\n"
            "Send /cancel to cancel."
        )
    
    async def handle_owner_ad(self, message: Message):
        """Handle owner ad message"""
        if message.from_user.id != self.owner_id:
            return
        
        if self.owner_id not in self.owner_ad_state:
            return
        
        try:
            ad_text = message.text or message.caption or ""
            media_type = None
            media_file_id = None
            
            if message.photo:
                media_type = "photo"
                media_file_id = message.photo.file_id
            elif message.video:
                media_type = "video"
                media_file_id = message.video.file_id
            
            if not ad_text and not media_file_id:
                await message.reply_text("❌ Please send a valid advertisement.")
                return
            
            # Save owner ad
            ad_id = self.db.save_owner_ad(ad_text, media_type, media_file_id)
            
            # Remove state
            del self.owner_ad_state[self.owner_id]
            
            await message.reply_text(
                f"✅ **Owner Ad Saved!**\n\n"
                f"Ad ID: #{ad_id}\n\n"
                f"Use /broadcast {ad_id} to broadcast this ad through free user accounts."
            )
            
        except Exception as e:
            logger.error(f"Error saving owner ad: {e}")
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def stats_command(self, message: Message):
        """Show bot statistics"""
        if message.from_user.id != self.owner_id:
            return
        
        active_users = self.db.get_active_users()
        free_users = self.db.get_free_users()
        premium_users = len(active_users) - len(free_users)
        
        # Get total groups
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_groups")
        total_groups = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM forwarding_logs WHERE status = 'success' AND date(timestamp) = date('now')")
        today_forwards = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_registered = cursor.fetchone()[0]
        
        conn.close()
        
        stats_text = f"""
📊 **Bot Statistics**

👥 **Users:**
• Total Registered: {total_registered}
• Active Users: {len(active_users)}
• Free Users: {len(free_users)}
• Premium Users: {premium_users}

👥 **Groups:**
• Total Groups: {total_groups}

📈 **Activity (Today):**
• Successful Forwards: {today_forwards}

⚙️ **System:**
• Active Sessions: {len(self.user_manager.active_sessions)}
• Running Automations: {len(self.user_manager.automation_tasks)}

🕐 **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await message.reply_text(stats_text)
    
    async def broadcast_text_command(self, message: Message):
        """Broadcast message to all users"""
        if message.from_user.id != self.owner_id:
            return
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text("Usage: /broadcasttext <message>")
            return
        
        broadcast_text = args[1]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        sent = 0
        failed = 0
        
        for user_row in users:
            user_id = user_row[0]
            try:
                await self.bot.send_message(user_id, broadcast_text)
                sent += 1
            except:
                failed += 1
        
        await message.reply_text(
            f"📢 **Broadcast Complete**\n\n"
            f"✅ Sent: {sent}\n"
            f"❌ Failed: {failed}"
        )
