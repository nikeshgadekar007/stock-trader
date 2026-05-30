"""
Firebase Authentication Module
User login, session management, and user data
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    FIREBASE_AUTH_AVAILABLE = True
except ImportError:
    FIREBASE_AUTH_AVAILABLE = False

class FirebaseAuth:
    """Firebase Authentication and User Management"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        self.current_user = None
        
        # Check for Firebase credentials
        cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        cred_path = os.environ.get('FIREBASE_CREDENTIALS')
        
        if FIREBASE_AUTH_AVAILABLE:
            try:
                if cred_json:
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                elif cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    raise Exception("No Firebase credentials found")
                
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                
                self.db = firestore.client()
                self.initialized = True
                print("Firebase Auth initialized successfully")
            except Exception as e:
                print(f"Firebase Auth init error: {e}")
                self.initialized = False
        else:
            print("Firebase Auth not available")
    
    def create_user(self, email: str, password: str) -> Dict:
        """Create a new user account"""
        if not self.initialized:
            return {'success': False, 'error': 'Firebase not initialized'}
        
        try:
            user = auth.create_user(email=email, password=password)
            return {'success': True, 'user_id': user.uid, 'email': user.email}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sign_in(self, email: str, password: str) -> Dict:
        """Sign in with email and password"""
        # Note: Firebase Admin SDK doesn't support email/password sign-in
        # This requires Firebase Client SDK or a custom auth flow
        # For now, we'll use a simplified approach
        
        if not self.initialized:
            return {'success': False, 'error': 'Firebase not initialized'}
        
        try:
            # Check if user exists in our database
            users_ref = self.db.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            docs = list(query.get())
            
            if docs:
                user_data = docs[0].to_dict()
                # In production, verify password hash here
                self.current_user = {
                    'id': docs[0].id,
                    'email': email,
                    'data': user_data
                }
                return {'success': True, 'user_id': docs[0].id, 'email': email}
            else:
                return {'success': False, 'error': 'User not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sign_in_google(self, id_token: str) -> Dict:
        """Verify Google ID token and sign in"""
        if not self.initialized:
            return {'success': False, 'error': 'Firebase not initialized'}
        
        try:
            # Verify the Google ID token
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email', '')
            
            # Check if user exists, if not create
            user_doc = self.db.collection('users').document(uid).get()
            
            if not user_doc.exists:
                # Create new user document
                self.db.collection('users').document(uid).set({
                    'email': email,
                    'created_at': datetime.now().isoformat(),
                    'watchlist': [],
                    'settings': {
                        'notifications_enabled': True,
                        'email_alerts': True
                    }
                })
            
            self.current_user = {
                'id': uid,
                'email': email,
                'name': decoded_token.get('name', '')
            }
            
            return {'success': True, 'user_id': uid, 'email': email}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sign_out(self):
        """Sign out current user"""
        self.current_user = None
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current logged in user"""
        return self.current_user
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None
    
    def get_user_data(self) -> Dict:
        """Get user-specific data from Firestore"""
        if not self.current_user or not self.db:
            return {}
        
        try:
            doc = self.db.collection('users').document(self.current_user['id']).get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"Error getting user data: {e}")
        
        return {}
    
    def update_user_data(self, data: Dict) -> bool:
        """Update user data in Firestore"""
        if not self.current_user or not self.db:
            return False
        
        try:
            self.db.collection('users').document(self.current_user['id']).update(data)
            return True
        except Exception as e:
            print(f"Error updating user data: {e}")
            return False
    
    def add_to_watchlist(self, symbol: str) -> bool:
        """Add stock to user's watchlist"""
        user_data = self.get_user_data()
        watchlist = user_data.get('watchlist', [])
        
        if symbol not in watchlist:
            watchlist.append(symbol)
            return self.update_user_data({'watchlist': watchlist})
        
        return True
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove stock from user's watchlist"""
        user_data = self.get_user_data()
        watchlist = user_data.get('watchlist', [])
        
        if symbol in watchlist:
            watchlist.remove(symbol)
            return self.update_user_data({'watchlist': watchlist})
        
        return True
    
    def get_user_watchlist(self) -> list:
        """Get user's personal watchlist"""
        user_data = self.get_user_data()
        return user_data.get('watchlist', [])


# Global instance
firebase_auth = FirebaseAuth()