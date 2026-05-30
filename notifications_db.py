"""
Notification Database Module
Store and manage notifications in Firebase
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

class NotificationDB:
    """Firebase-based notification storage"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        
        cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        cred_path = os.environ.get('FIREBASE_CREDENTIALS')
        
        if FIREBASE_AVAILABLE:
            try:
                if cred_json:
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                elif cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    raise Exception("No Firebase credentials")
                
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                
                self.db = firestore.client()
                self.initialized = True
            except Exception as e:
                print(f"NotificationDB init error: {e}")
    
    def add_notification(self, user_id: str, notification: Dict) -> bool:
        """Add a new notification for a user"""
        if not self.initialized or not self.db:
            return False
        
        try:
            notification['created_at'] = datetime.now().isoformat()
            notification['read'] = False
            
            self.db.collection('notifications').add({
                'user_id': user_id,
                **notification
            })
            return True
        except Exception as e:
            print(f"Error adding notification: {e}")
            return False
    
    def get_notifications(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get notifications for a user"""
        if not self.initialized or not self.db:
            return []
        
        try:
            docs = (self.db.collection('notifications')
                   .where('user_id', '==', user_id)
                   .order_by('created_at', direction='DESCENDING')
                   .limit(limit)
                   .get())
            
            notifications = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                notifications.append(data)
            
            return notifications
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        if not self.initialized or not self.db:
            return 0
        
        try:
            docs = (self.db.collection('notifications')
                   .where('user_id', '==', user_id)
                   .where('read', '==', False)
                   .get())
            
            return len(docs)
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        if not self.initialized or not self.db:
            return False
        
        try:
            self.db.collection('notifications').document(notification_id).update({'read': True})
            return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user"""
        if not self.initialized or not self.db:
            return False
        
        try:
            docs = (self.db.collection('notifications')
                   .where('user_id', '==', user_id)
                   .where('read', '==', False)
                   .get())
            
            for doc in docs:
                doc.reference.update({'read': True})
            
            return True
        except Exception as e:
            print(f"Error marking all as read: {e}")
            return False
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification"""
        if not self.initialized or not self.db:
            return False
        
        try:
            self.db.collection('notifications').document(notification_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False
    
    def clear_old_notifications(self, user_id: str, days: int = 7) -> bool:
        """Clear notifications older than specified days"""
        if not self.initialized or not self.db:
            return False
        
        try:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            docs = (self.db.collection('notifications')
                   .where('user_id', '==', user_id)
                   .where('created_at', '<', cutoff)
                   .get())
            
            for doc in docs:
                doc.reference.delete()
            
            return True
        except Exception as e:
            print(f"Error clearing old notifications: {e}")
            return False


# Global instance
notification_db = NotificationDB()


def create_signal_notification(user_id: str, symbol: str, action: str, 
                               price: float, target: float, stop: float,
                               confidence: float, source: str = 'system') -> bool:
    """Create a signal notification"""
    emoji = "📈" if action == "BUY" else "📉"
    
    notification = {
        'type': 'signal',
        'title': f'{emoji} {action} Signal: {symbol}',
        'message': f'{action} {symbol} @ ${price:.2f}\nTarget: ${target:.2f} | Stop: ${stop:.2f}\nConfidence: {confidence:.0%}',
        'symbol': symbol,
        'action': action,
        'price': price,
        'target': target,
        'stop': stop,
        'confidence': confidence,
        'source': source
    }
    
    return notification_db.add_notification(user_id, notification)


def create_alert_notification(user_id: str, title: str, message: str,
                               alert_type: str = 'info') -> bool:
    """Create an alert notification"""
    notification = {
        'type': 'alert',
        'alert_type': alert_type,
        'title': title,
        'message': message
    }
    
    return notification_db.add_notification(user_id, notification)