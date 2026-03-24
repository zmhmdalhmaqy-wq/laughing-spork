"""
MongoDB Handler - إدارة قاعدة البيانات السحابية
"""

import os
import json
import hashlib
from datetime import datetime

# ============== MONGODB CONFIGURATION ==============
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://omar_admin:OmarHost2026@cluster0.mongodb.net/omar_host_db?retryWrites=true&w=majority')
DB_NAME = 'omar_host_db'

ADMIN_USERNAME = "Ziad00"
ADMIN_PASSWORD_RAW = "Ziad00"

class MongoDBHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            self.connected = True
            print("✅ تم الاتصال بـ MongoDB بنجاح")
            self._initialize_collections()
        except Exception as e:
            print(f"⚠️ تعذر الاتصال بـ MongoDB: {e}")
            self.connected = False
    
    def _initialize_collections(self):
        if self.connected:
            try:
                existing = self.db.list_collection_names()
                if 'users' not in existing:
                    self.db.create_collection('users')
                if 'servers' not in existing:
                    self.db.create_collection('servers')
                admin_hash = hashlib.sha256(ADMIN_PASSWORD_RAW.encode()).hexdigest()
                self.db['users'].update_one(
                    {"_id": ADMIN_USERNAME},
                    {"$set": {
                        "password": admin_hash,
                        "is_admin": True,
                        "created_at": str(datetime.now()),
                        "custom_max_servers": 999,
                        "expiry_days": 3650,
                        "plan": "king"
                    }},
                    upsert=True
                )
            except Exception as e:
                print(f"❌ خطأ في تهيئة المجموعات: {e}")
    
    def load_db(self):
        if not self.connected:
            return self._load_local_db()
        try:
            users = {}
            for user in self.db['users'].find():
                uid = user.pop('_id')
                users[uid] = user
            servers = {}
            for server in self.db['servers'].find():
                sid = server.pop('_id')
                servers[sid] = server
            return {"users": users, "servers": servers, "logs": []}
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {e}")
            return self._load_local_db()
    
    def save_db(self, db_data):
        if not self.connected:
            return self._save_local_db(db_data)
        try:
            if 'users' in db_data:
                for username, user_data in db_data['users'].items():
                    user_data_copy = user_data.copy()
                    user_data_copy['_id'] = username
                    self.db['users'].replace_one({"_id": username}, user_data_copy, upsert=True)
            if 'servers' in db_data:
                for server_id, server_data in db_data['servers'].items():
                    server_data_copy = server_data.copy()
                    server_data_copy['_id'] = server_id
                    self.db['servers'].replace_one({"_id": server_id}, server_data_copy, upsert=True)
            print("✅ تم مزامنة البيانات مع MongoDB")
        except Exception as e:
            print(f"❌ خطأ في حفظ البيانات: {e}")
            self._save_local_db(db_data)
    
    def _load_local_db(self):
        db_file = os.path.join(os.path.dirname(__file__), "db.json")
        admin_hash = hashlib.sha256(ADMIN_PASSWORD_RAW.encode()).hexdigest()
        default_db = {
            "users": {
                ADMIN_USERNAME: {
                    "password": admin_hash,
                    "is_admin": True,
                    "created_at": str(datetime.now()),
                    "custom_max_servers": 999,
                    "expiry_days": 3650,
                    "plan": "king"
                }
            },
            "servers": {},
            "logs": []
        }
        if os.path.exists(db_file):
            try:
                with open(db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if ADMIN_USERNAME not in data.get("users", {}):
                        if "users" not in data: data["users"] = {}
                        data["users"][ADMIN_USERNAME] = default_db["users"][ADMIN_USERNAME]
                    return data
            except:
                pass
        return default_db
    
    def _save_local_db(self, db_data):
        db_file = os.path.join(os.path.dirname(__file__), "db.json")
        try:
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(db_data, f, indent=4, ensure_ascii=False)
            print(f"✅ تم حفظ البيانات محلياً")
        except Exception as e:
            print(f"❌ خطأ في حفظ البيانات: {e}")

db_handler = MongoDBHandler()