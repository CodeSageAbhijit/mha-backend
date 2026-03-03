# utils/bson_helper.py
from bson import ObjectId
from datetime import datetime

def obj_to_str(o):
    if isinstance(o, ObjectId):
        return str(o)
    if isinstance(o, datetime):
        return o.isoformat()
    return o

def document_to_json(doc: dict) -> dict:
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v

    if "_id" in out:
        out["_id"] = out["_id"]
    return out