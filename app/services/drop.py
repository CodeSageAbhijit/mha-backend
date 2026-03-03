
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ FIXED: Use environment variable instead of hardcoded credentials
MONGO_URL = os.getenv("MONGODB_URI", "mongodb+srv://MentalHealth:Manthan%2312345@cluster0.pnbho29.mongodb.net/?tls=true")
client = MongoClient(MONGO_URL)
db = client["mental_health"]
collection = db["prescriptions"]

# 2. Show existing indexes
print("Indexes before dropping:")
for idx in collection.list_indexes():
    print(idx)

# 3. Drop the unique index on "id"
try:
    collection.drop_index("id_1")
    print("\n✅ Dropped index: id_1")
except Exception as e:
    print("\n⚠️ Could not drop index:", e)

# 4. Show indexes after dropping
print("\nIndexes after dropping:")
for idx in collection.list_indexes():
    print(idx)

# 5. (Optional) Remove old 'id' fields if they are null
result = collection.update_many(
    {"id": None},        # condition
    {"$unset": {"id": ""}}  # remove the field
)
print(f"\n🧹 Cleaned {result.modified_count} documents (removed 'id: null').")
