"""
Advanced Features for Telegram Ads Forwarding BOT
Includes analytics, scheduling, ad rotation, and more
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import json

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Track and analyze forwarding performance"""
    
    def __init__(self, db):
        self.db = db
    
    def get_user_analytics(self, user_id: int, days: int = 7) -> Dict:
        """Get user analytics for last N days"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get total forwards
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM forwarding_logs
            WHERE user_id = ? AND timestamp >= datetime('now', '-' || ? || ' days')
        """, (user_id, days))
        
        stats = cursor.fetchone()
        
        # Get best performing groups
        cursor.execute("""
            SELECT group_name, COUNT(*) as forwards,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM forwarding_logs
            WHERE user_id = ? AND timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY group_id
            ORDER BY successful DESC
            LIMIT 5
        """, (user_id, days))
        
        top_groups = cursor.fetchall()
        
        # Get daily breakdown
        cursor.execute("""
            SELECT DATE(timestamp) as date,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM forwarding_logs
            WHERE user_id = ? AND timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (user_id, days))
        
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_forwards': stats[0] or 0,
            'successful': stats[1] or 0,
            'failed': stats[2] or 0,
            'success_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0,
            'top_groups': [{'name': g[0], 'forwards': g[1], 'successful': g[2]} for g in top_groups],
            'daily_stats': [{'date': d[0], 'total': d[1], 'successful': d[2]} for d in daily_stats]
        }
    
    def get_group_performance(self, user_id: int, group_id: int) -> Dict:
        """Get detailed performance for a specific group"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_forwards,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                MIN(timestamp) as first_forward,
                MAX(timestamp) as last_forward
            FROM forwarding_logs
            WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'total_forwards': stats[0] or 0,
            'successful': stats[1] or 0,
            'failed': stats[2] or 0,
            'first_forward': stats[3],
            'last_forward': stats[4],
            'success_rate': (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
        }


class ScheduledCampaignManager:
    """Manage scheduled ad campaigns"""
    
    def __init__(self, db):
        self.db = db
        self._init_table()
    
    def _init_table(self):
        """Initialize scheduled campaigns table"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ad_id INTEGER,
                scheduled_time TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (ad_id) REFERENCES ads(id)
            )
        """)
        conn.commit()
        conn.close()
    
    def schedule_campaign(self, user_id: int, ad_id: int, scheduled_time: datetime) -> int:
        """Schedule a campaign"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduled_campaigns (user_id, ad_id, scheduled_time)
            VALUES (?, ?, ?)
        """, (user_id, ad_id, scheduled_time))
        conn.commit()
        campaign_id = cursor.lastrowid
        conn.close()
        return campaign_id
    
    def get_pending_campaigns(self) -> List[Dict]:
        """Get campaigns ready to run"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scheduled_campaigns
            WHERE status = 'pending' AND scheduled_time <= datetime('now')
        """)
        campaigns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return campaigns
    
    def mark_completed(self, campaign_id: int):
        """Mark campaign as completed"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scheduled_campaigns SET status = 'completed' WHERE id = ?
        """, (campaign_id,))
        conn.commit()
        conn.close()


class AdRotationManager:
    """Manage multiple ads and rotate them"""
    
    def __init__(self, db):
        self.db = db
    
    def get_user_ads(self, user_id: int) -> List[Dict]:
        """Get all active ads for a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ads WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """, (user_id,))
        ads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ads
    
    def get_next_ad_to_forward(self, user_id: int) -> Optional[Dict]:
        """Get next ad in rotation"""
        ads = self.get_user_ads(user_id)
        if not ads:
            return None
        
        # Simple round-robin rotation
        # Track which ad was last used
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ad_text FROM forwarding_logs
            WHERE user_id = ? AND status = 'success'
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id,))
        
        last_ad = cursor.fetchone()
        conn.close()
        
        if not last_ad:
            return ads[0]
        
        # Find next ad in rotation
        for i, ad in enumerate(ads):
            if ad['ad_text'] == last_ad[0]:
                return ads[(i + 1) % len(ads)]
        
        return ads[0]
    
    def toggle_ad_status(self, ad_id: int, is_active: bool):
        """Enable/disable an ad"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ads SET is_active = ? WHERE id = ?
        """, (is_active, ad_id))
        conn.commit()
        conn.close()


class GroupManagementFeatures:
    """Advanced group management features"""
    
    def __init__(self, db):
        self.db = db
        self._init_tables()
    
    def _init_tables(self):
        """Initialize group management tables"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Paused groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paused_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                group_id INTEGER,
                paused_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Group priority table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_priority (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                group_id INTEGER,
                priority INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def pause_group(self, user_id: int, group_id: int):
        """Pause forwarding to a group"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO paused_groups (user_id, group_id)
            VALUES (?, ?)
        """, (user_id, group_id))
        conn.commit()
        conn.close()
    
    def resume_group(self, user_id: int, group_id: int):
        """Resume forwarding to a group"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM paused_groups WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        conn.commit()
        conn.close()
    
    def is_group_paused(self, user_id: int, group_id: int) -> bool:
        """Check if group is paused"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM paused_groups WHERE user_id = ? AND group_id = ?
        """, (user_id, group_id))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def set_group_priority(self, user_id: int, group_id: int, priority: int):
        """Set group priority (higher = sent first)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO group_priority (user_id, group_id, priority)
            VALUES (?, ?, ?)
        """, (user_id, group_id, priority))
        conn.commit()
        conn.close()
    
    def get_active_groups_sorted(self, user_id: int) -> List[Dict]:
        """Get active groups sorted by priority"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ug.*, COALESCE(gp.priority, 0) as priority
            FROM user_groups ug
            LEFT JOIN group_priority gp ON ug.user_id = gp.user_id AND ug.group_id = gp.group_id
            LEFT JOIN paused_groups pg ON ug.user_id = pg.user_id AND ug.group_id = pg.group_id
            WHERE ug.user_id = ? AND pg.id IS NULL
            ORDER BY priority DESC, ug.group_name ASC
        """, (user_id,))
        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return groups


class ReferralSystem:
    """Referral system to encourage growth"""
    
    def __init__(self, db):
        self.db = db
        self._init_table()
    
    def _init_table(self):
        """Initialize referral table"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                reward_granted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()
        conn.close()
    
    def create_referral(self, referrer_id: int, referred_id: int):
        """Record a referral"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO referrals (referrer_id, referred_id)
            VALUES (?, ?)
        """, (referrer_id, referred_id))
        conn.commit()
        conn.close()
    
    def get_referral_count(self, user_id: int) -> int:
        """Get number of referrals"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
        """, (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_pending_rewards(self, user_id: int) -> int:
        """Get pending rewards for referrals"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM referrals 
            WHERE referrer_id = ? AND reward_granted = 0
        """, (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def grant_reward(self, referral_id: int):
        """Mark reward as granted"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE referrals SET reward_granted = 1 WHERE id = ?
        """, (referral_id,))
        conn.commit()
        conn.close()


class TemplateManager:
    """Manage ad templates"""
    
    def __init__(self, db):
        self.db = db
        self._init_table()
    
    def _init_table(self):
        """Initialize templates table"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ad_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                template_text TEXT,
                is_public BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Add default templates
        self._add_default_templates()
        conn.close()
    
    def _add_default_templates(self):
        """Add default ad templates"""
        default_templates = [
            {
                'name': 'Product Sale',
                'category': 'ecommerce',
                'text': '🔥 SPECIAL OFFER! 🔥\n\n💰 {product_name}\n✅ {discount}% OFF\n⏰ Limited Time!\n\n📱 Order Now: {link}'
            },
            {
                'name': 'Service Promotion',
                'category': 'service',
                'text': '⭐ {service_name} ⭐\n\n✨ Professional Service\n💯 100% Satisfaction\n📞 Contact: {contact}\n\n🎁 First-time discount available!'
            },
            {
                'name': 'Event Announcement',
                'category': 'event',
                'text': '📢 UPCOMING EVENT!\n\n🎉 {event_name}\n📅 Date: {date}\n📍 Venue: {venue}\n\n🎟️ Register: {link}'
            },
            {
                'name': 'Job Opening',
                'category': 'job',
                'text': '💼 JOB OPENING\n\n🏢 Position: {position}\n📍 Location: {location}\n💰 Salary: {salary}\n\n📩 Apply: {contact}'
            }
        ]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        for template in default_templates:
            cursor.execute("""
                INSERT OR IGNORE INTO ad_templates (name, category, template_text)
                VALUES (?, ?, ?)
            """, (template['name'], template['category'], template['text']))
        
        conn.commit()
        conn.close()
    
    def get_templates(self, category: str = None) -> List[Dict]:
        """Get ad templates"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT * FROM ad_templates WHERE category = ? AND is_public = 1
            """, (category,))
        else:
            cursor.execute("""
                SELECT * FROM ad_templates WHERE is_public = 1
            """)
        
        templates = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return templates


class SessionHealthMonitor:
    """Monitor session health and detect issues"""
    
    def __init__(self, db):
        self.db = db
    
    async def check_session_health(self, user_id: int, user_client: Client) -> Dict:
        """Check if session is healthy"""
        health_status = {
            'is_healthy': True,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Test 1: Can get self info
            try:
                me = await user_client.get_me()
                if not me:
                    health_status['is_healthy'] = False
                    health_status['issues'].append('Cannot fetch user info')
            except Exception as e:
                health_status['is_healthy'] = False
                health_status['issues'].append(f'User info error: {str(e)}')
            
            # Test 2: Check recent forwards success rate
            analytics = AnalyticsManager(self.db)
            stats = analytics.get_user_analytics(user_id, days=1)
            
            if stats['total_forwards'] > 10 and stats['success_rate'] < 50:
                health_status['warnings'].append(f"Low success rate: {stats['success_rate']:.1f}%")
            
            # Test 3: Check if session is connected
            if not user_client.is_connected:
                health_status['is_healthy'] = False
                health_status['issues'].append('Session not connected')
            
        except Exception as e:
            health_status['is_healthy'] = False
            health_status['issues'].append(f'Health check failed: {str(e)}')
        
        return health_status


class ReportGenerator:
    """Generate daily/weekly reports"""
    
    def __init__(self, db):
        self.db = db
        self.analytics = AnalyticsManager(db)
    
    def generate_daily_report(self, user_id: int) -> str:
        """Generate daily report text"""
        stats = self.analytics.get_user_analytics(user_id, days=1)
        
        report = f"""
📊 **Daily Report - {datetime.now().strftime('%Y-%m-%d')}**

📈 **Performance:**
• Total Forwards: {stats['total_forwards']}
• Successful: {stats['successful']} ✅
• Failed: {stats['failed']} ❌
• Success Rate: {stats['success_rate']:.1f}%

🏆 **Top Performing Groups:**
"""
        
        for i, group in enumerate(stats['top_groups'][:3], 1):
            report += f"{i}. {group['name']} - {group['successful']} successful\n"
        
        return report
    
    def generate_weekly_report(self, user_id: int) -> str:
        """Generate weekly report text"""
        stats = self.analytics.get_user_analytics(user_id, days=7)
        
        report = f"""
📊 **Weekly Report**

📈 **7-Day Performance:**
• Total Forwards: {stats['total_forwards']}
• Successful: {stats['successful']} ✅
• Failed: {stats['failed']} ❌
• Success Rate: {stats['success_rate']:.1f}%
• Avg per day: {stats['total_forwards'] // 7}

🏆 **Top 5 Groups:**
"""
        
        for i, group in enumerate(stats['top_groups'], 1):
            success_rate = (group['successful'] / group['forwards'] * 100) if group['forwards'] > 0 else 0
            report += f"{i}. {group['name']}\n   • Forwards: {group['forwards']}\n   • Success: {success_rate:.1f}%\n\n"
        
        report += "\n📅 **Daily Breakdown:**\n"
        for day in stats['daily_stats'][:7]:
            report += f"• {day['date']}: {day['successful']}/{day['total']} successful\n"
        
        return report
