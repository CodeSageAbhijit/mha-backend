import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import base64

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return str(obj)

async def get_all_data():
    mongo_uri = 'mongodb+srv://MentalHealth:Manthan%2312345@cluster0.pnbho29.mongodb.net/?tls=true'
    client = AsyncIOMotorClient(mongo_uri)
    db = client['mental_health']
    
    all_data = {}
    
    collections_to_fetch = [
        'admin', 'psychiatrists', 'patients', 'counselors', 'appointments',
        'calls', 'chats', 'review', 'wallet', 'wallet_transactions',
        'prescriptions', 'rooms', 'departments', 'assessments', 'user_assessments'
    ]
    
    for collection_name in collections_to_fetch:
        try:
            collection = db[collection_name]
            count = await collection.count_documents({})
            if count > 0:
                docs = await collection.find({}).to_list(length=None)
                all_data[collection_name] = {'count': count, 'data': docs}
                print(f'✅ {collection_name}: {count} docs exported')
        except Exception as e:
            print(f'❌ {collection_name}: {str(e)[:100]}')
    
    output_file = 'db_export.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
    
    print(f'\n✅ Database exported to: {output_file}')
    print(f'File size: {len(json.dumps(all_data, cls=JSONEncoder)) / (1024*1024):.2f} MB')

asyncio.run(get_all_data())
