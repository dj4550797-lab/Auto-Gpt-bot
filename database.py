from pymongo import MongoClient
import info
import sys

# DEBUG: Check karne ke liye ki URI mil raha hai ya nahi
if not info.MONGO_URI:
    print("❌ ERROR: MONGO_URI is empty! Check Render Environment Variables.")
    sys.exit(1) # Bot ko yahi rok dega agar URI nahi hai

try:
    client = MongoClient(info.MONGO_URI)
    db = client['flixora_ai']
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    sys.exit(1)

class Database:
    def __init__(self):
        self.users_col = db['users']
        self.payments_col = db['payments']

    def get_user(self, user_id):
        return self.users_col.find_one({"user_id": user_id})

    def create_user(self, user_data):
        self.users_col.insert_one(user_data)

    def update_user(self, user_id, data):
        self.users_col.update_one({"user_id": user_id}, {"$set": data})

    def get_all_users(self):
        return list(self.users_col.find())

    def insert_payment(self, data):
        self.payments_col.insert_one(data)

    def get_pending_payments(self):
        return list(self.payments_col.find({"status": "pending"}))

    def update_payment(self, user_id, status):
        self.payments_col.update_one({"user_id": user_id}, {"$set": {"status": status}})

db_client = Database()
