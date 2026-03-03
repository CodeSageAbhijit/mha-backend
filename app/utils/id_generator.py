# # from pymongo import ReturnDocument
# # import re

# # async def generate_custom_id(entity: str, prefix: str, collection) -> str:
# #     """
# #     entity: "patient", "doctor", "counselor"
# #     prefix: "MHA-P", "MHA-D", "MHA-C"
# #     collection: MongoDB collection for the entity
# #     """
# #     # Find the latest inserted document by sorting on createdAt
# #     last_doc = await collection.find_one(
# #         {f"{entity}Id": {"$regex": f"^{prefix}"}},
# #         sort=[("createdAt", -1)]
# #     )

# #     if last_doc:
# #         # Extract the numeric part of the ID using regex
# #         match = re.search(rf"{prefix}(\d+)", last_doc.get(f"{entity}Id", ""))
# #         if match:
# #             last_seq = int(match.group(1))
# #         else:
# #             last_seq = 0
# #     else:
# #         last_seq = 0

# #     # Generate next ID (always padded to 3 digits)
# #     next_seq = last_seq + 1
# #     return f"{prefix}{next_seq:03d}"
# from pymongo import ReturnDocument
# from app.database.mongo import counter_collection

# # Map entity to prefix
# # PREFIX_MAP = {
# #     "patient": "MHA-P",
# #     "doctor": "MHA-D",
# #     "counselor": "MHA-C"
# # }

# async def generate_custom_id(entity: str) -> str:
#     PREFIX_MAP = {
#         "user": "MHA-P",
#         "doctor": "MHA-D",
#         "counselor": "MHA-C"
#     }

#     if entity not in PREFIX_MAP:
#         raise ValueError(f"Invalid entity: {entity}")

#     prefix = PREFIX_MAP[entity]

#     # Ensure counter starts from 99 so that first ID = 100
#     result = await counter_collection.find_one_and_update(
#         {"_id": entity},
#         {"$inc": {"seq": 1}},
#         upsert=True,
#         return_document=ReturnDocument.AFTER
#     )
#     print(f"Counter for {entity} updated: {result}")

#     # If it's a fresh document (Mongo creates with seq=1), set it to 100
#     if result["seq"] == 1:
#         await counter_collection.update_one(
#             {"_id": entity},
#             {"$set": {"seq": 100}}
#         )
#         next_seq = 100
#     else:
#         next_seq = result["seq"]

#     return f"{prefix}{next_seq:03d}"
import uuid

async def generate_custom_id(entity: str) -> str:
    PREFIX_MAP = {
        "user": "MHA-P",
        "psychiatrist": "MHA-PSY",
        "mentor": "MHA-M",
        "counselor": "MHA-C",
        "business_coach": "MHA-BC",
        "buddy": "MHA-B",
        "admin": "MHA-A",
        "superadmin": "MHA-SA"
    }
    
    if entity not in PREFIX_MAP:
        print(f"Invalid entity: {entity}")
        raise ValueError(f"Invalid entity: {entity}")

    prefix = PREFIX_MAP[entity]
    unique_id = uuid.uuid4().hex[:8]
    return f"{prefix}{unique_id}"