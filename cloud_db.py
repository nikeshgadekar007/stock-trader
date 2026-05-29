"""
Firebase Cloud Database for Trade Persistence
"""

import json
import os
from datetime import datetime

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

class CloudDatabase:
    """Cloud database for persisting trades across devices"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        
        # Check for Firebase credentials
        cred_path = os.environ.get('FIREBASE_CREDENTIALS')
        cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        
        if FIREBASE_AVAILABLE:
            try:
                if cred_json:
                    # Streamlit Secrets - JSON string
                    import json
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                elif cred_path and os.path.exists(cred_path):
                    # Local file
                    cred = credentials.Certificate(cred_path)
                else:
                    raise Exception("No credentials found")
                
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.initialized = True
                print("Firebase initialized successfully")
            except Exception as e:
                print(f"Firebase init error: {e}")
                self.initialized = False
        else:
            print("Firebase not configured - using local storage")
            self.initialized = False
    
    def save_trades(self, trades_data: dict) -> bool:
        """Save trades to cloud or local file"""
        if self.initialized:
            try:
                doc_ref = self.db.collection('trades').document('current')
                doc_ref.set({
                    'cash': trades_data.get('cash', 0),
                    'positions': trades_data.get('positions', {}),
                    'trades': trades_data.get('trades', []),
                    'last_updated': datetime.now().isoformat()
                })
                return True
            except Exception as e:
                print(f"Cloud save error: {e}")
                return False
        else:
            # Fallback to local file
            return self._save_local(trades_data)
    
    def load_trades(self) -> dict:
        """Load trades from cloud or local file"""
        if self.initialized:
            try:
                doc = self.db.collection('trades').document('current').get()
                if doc.exists:
                    data = doc.to_dict()
                    return {
                        'cash': data.get('cash', 100000),
                        'positions': data.get('positions', {}),
                        'trades': data.get('trades', [])
                    }
            except Exception as e:
                print(f"Cloud load error: {e}")
        
        return self._load_local()
    
    def _save_local(self, trades_data: dict) -> bool:
        """Save to local JSON file"""
        try:
            os.makedirs('output', exist_ok=True)
            with open('output/paper_trades.json', 'w') as f:
                json.dump(trades_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Local save error: {e}")
            return False
    
    def _load_local(self) -> dict:
        """Load from local JSON file"""
        try:
            if os.path.exists('output/paper_trades.json'):
                with open('output/paper_trades.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Local load error: {e}")
        
        return {'cash': 100000, 'positions': {}, 'trades': []}

# Global instance
cloud_db = CloudDatabase()