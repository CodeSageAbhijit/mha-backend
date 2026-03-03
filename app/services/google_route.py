
# app/services/login_routes.py

from bson import ObjectId
from datetime import datetime, timedelta
import os
import json
import logging
import secrets
from typing import Optional, Tuple
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from authlib.integrations.starlette_client import OAuth
from pymongo import ReturnDocument

# Import collections and helpers
from app.database.mongo import psychiatrist_collection, counselor_collection, patient_collection, db
from app.utils.constants import hash_password
from app.utils.jwt_tokens import create_access_token, create_refresh_token
from app.utils.id_generator import generate_custom_id

router = APIRouter(prefix="/api", tags=["Auth"])
logger = logging.getLogger("uvicorn.error")
oauth_states_collection = db["oauth_states"]
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "https://mental-health-frontend.example.com/auth/google/callback",
)




def _safe(v):
    """Safe JSON serialization helper for ObjectId etc."""
    if isinstance(v, ObjectId):
        return str(v)
    try:
        json.dumps(v)
        return v
    except Exception:
        return str(v)


def _role_map() -> dict:
    """
    Returns mapping: role -> (collection, prefix, id_field)
    Adjust prefix/id_field if you keep different structure.
    """
    return {
        "doctor": (psychiatrist_collection, "MHA-D", "doctorId"),
        "counselor": (counselor_collection, "MHA-C", "counselorId"),
        "user": (patient_collection, "MHA-P", "patientId"),
        # add "admin" mapping if you have an admin collection
    }


async def _create_user_in_collection(
    collection,
    prefix: str,
    id_field: str,
    email: str,
    name: Optional[str],
    role: str,
    picture: Optional[str] = None,
) -> Tuple[dict, str]:
    """
    Insert a new user document into the given collection and return (doc, inserted_id_str).
    Uses generate_custom_id if available (async). Falls back to prefix + ObjectId().
    """
    custom_id = None
    try:
        # generate_custom_id may be async in your utils
        custom_id = await generate_custom_id(role)
    except Exception:
        custom_id = f"{prefix}{ObjectId()}"

    new_user = {
        "email": email,
        "username": email,
        "firstName": name or "",
        "role": role,
        "picture": picture or "",
        id_field: f"{custom_id}",
        "password": hash_password("google-oauth"),
        "isProfileComplete": False,
        "authType": "google",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
    res = await collection.insert_one(new_user)
    inserted = await collection.find_one({"_id": res.inserted_id})
    return inserted, str(res.inserted_id)


@router.get("/auth/google")
async def login_google(request: Request, role: str = "user"):
    """
    Initiates Google OAuth redirect.

    Usage from frontend:
      GET /api/auth/google?role=doctor

    Implementation:
    - generate a secure random state
    - store the login_context (role) keyed by state in oauth_states
    - pass the state explicitly to authorize_redirect so Google returns the same state
    """
    try:
        # sanitize role
        role_val = (role or "user").lower()
        if role_val not in _role_map().keys():
            logger.warning("login_google called with invalid role=%s, falling back to 'user'", role_val)
            role_val = "user"

        # generate secure state token
        state = secrets.token_urlsafe(24)
        logger.info(f"[OAuth] Initiating login: role={role_val}, state={state}")

        # Clean up expired states (older than 10 min)
        await oauth_states_collection.delete_many({
            "created_at": {"$lt": datetime.utcnow() - timedelta(minutes=10)}
        })

        # Store minimal context against state in MongoDB (expires in 10 min)
        await oauth_states_collection.insert_one({
            "state": state,
            "role": role_val,
            "created_at": datetime.utcnow()
        })

        # Build redirect, explicitly pass state so authlib uses it
        logger.info(f"[OAuth] Redirecting to Google: redirect_uri={REDIRECT_URI}, state={state}")
        resp = await oauth.google.authorize_redirect(request, REDIRECT_URI, state=state)

        # log location if available
        try:
            logger.info("Google auth URL -> %s", resp.headers.get("location"))
        except Exception:
            logger.info("Google auth redirect created (location not available)")

        return resp
    except Exception as e:
        logger.exception("login_google error")
        raise HTTPException(status_code=500, detail=f"Google login error: {str(e)}")


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    """
    Callback from Google OAuth.
    Validates `state` against saved oauth_states and uses stored context (role) to create user in the correct collection.
    Returns JSON (API) or HTML that posts payload to opener (popup).
    """

    try:
        # Validate state manually
        state = request.query_params.get("state")
        logger.info(f"[OAuth] Callback received: state={state}, query_params={dict(request.query_params)}")
        if not state:
                logger.error(f"OAuth callback missing state param. Query params: {dict(request.query_params)}")
                raise HTTPException(status_code=400, detail="Missing OAuth state (CSRF check failed)")

        context = await oauth_states_collection.find_one({"state": state})
        logger.info(f"[OAuth] Callback DB lookup: state={state}, found={bool(context)}")
        if not context:
                logger.error(f"OAuth callback with unknown state={state}. Query params: {dict(request.query_params)}")
                raise HTTPException(status_code=400, detail="Invalid or expired OAuth state (CSRF check failed)")

        # Exchange code for token
        token = await oauth.google.authorize_access_token(request)

        # Parse id token if present, else fetch userinfo
        user_info = None
        if "id_token" in token:
            try:
                user_info = await oauth.google.parse_id_token(request, token)
            except Exception as e:
                logger.warning(f"Failed to parse id_token: {e}")
                user_info = None

        if not user_info:
            resp = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)
            user_info = resp.json()

        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")

        if not email:
            logger.error("No email returned by Google")
            raise HTTPException(status_code=400, detail="No email returned by Google")

        # Remove login_context for this state (prevent replay)
        await oauth_states_collection.delete_one({"state": state})
        role = (context.get("role") or "user").lower()

        role_map = _role_map()
        if role not in role_map:
            logger.warning(f"Invalid role in stored context: {role} - defaulting to 'user'")
            role = "user"

        target_collection, prefix, id_field = role_map[role]

        # Check if user already exists in the target collection (by email)
        user = await target_collection.find_one({"email": email})
        is_new = False
        if not user:
            is_new = True
            # create user in appropriate collection
            inserted_doc, inserted_id = await _create_user_in_collection(
                target_collection, prefix, id_field, email, name, role, picture
            )
            user = inserted_doc
            user_id = inserted_id
            is_profile_complete = False
        else:
            user_id = str(user.get("_id"))
            is_profile_complete = user.get("isProfileComplete", False)


        # Generate tokens and include role in token payload
        access_token = create_access_token({"userId": user_id, "email": email, "role": role})
        refresh_token = create_refresh_token({"userId": user_id, "email": email, "role": role})

        def _to_str(t):
            if isinstance(t, bytes):
                return t.decode()
            if isinstance(t, str) and t.startswith("b'") and t.endswith("'"):
                return t[2:-1]
            return str(t)

        access_token_str = _to_str(access_token)
        refresh_token_str = _to_str(refresh_token)

        payload = {
            "success": True,
            "message": "Google login successful",
            "data": {
                "accessToken": access_token_str,
                "refreshToken": refresh_token_str,
                "userId": _safe(user_id),
                "email": _safe(email),
                "role": _safe(role),
                "isNewUser": is_new,
                "isProfileComplete": is_profile_complete,
            },
        }

        # Always return JSON to frontend callback handler
        return JSONResponse(payload)
    except Exception as e:
        logger.exception("Google callback failed")
        error_payload = {"success": False, "error": f"Google login error: {str(e)}"}
        return JSONResponse(error_payload, status_code=500)
    
    
# New endpoint: exchange code/state for tokens (called by frontend after redirect)
import httpx

@router.get("/auth/google/exchange")
async def google_exchange(request: Request, code: str, state: str):
    """
    Frontend calls this endpoint with code and state after Google OAuth redirect.
    Returns tokens and user info for session management.
    """
    try:
            # Validate state from MongoDB
        logger.info(f"[OAuth] /exchange called: code={code}, state={state}")
        context = await oauth_states_collection.find_one({"state": state})
        logger.info(f"[OAuth] /exchange DB lookup: state={state}, found={bool(context)}")
        if not context:
                logger.error(f"Google exchange: Invalid or expired state={state}. Code={code}")
                raise HTTPException(status_code=400, detail="Invalid or expired OAuth state (CSRF check failed)")

        # Exchange code for token manually
        token_url = "https://oauth2.googleapis.com/token"
        client_id = oauth.google.client_id
        client_secret = oauth.google.client_secret
        redirect_uri = REDIRECT_URI
        frontend_redirect_uri = request.query_params.get("redirect_uri")
        if frontend_redirect_uri:
            logger.info(f"[OAuth] /exchange using frontend redirect_uri: {frontend_redirect_uri}")
            redirect_uri = frontend_redirect_uri
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data, headers={"Accept": "application/json"})
            resp.raise_for_status()
            token = resp.json()

        # Parse id token if present, else fetch userinfo
        user_info = None
        if "id_token" in token:
            try:
                user_info = await oauth.google.parse_id_token(request, token)
            except Exception:
                user_info = None
        if not user_info:
            resp2 = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)
            user_info = resp2.json()

        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
        if not email:
            raise HTTPException(status_code=400, detail="No email returned by Google")

        # Remove login_context for this state (prevent replay)
        await oauth_states_collection.delete_one({"state": state})
        role = (context.get("role") or "user").lower()
        role_map = _role_map()
        if role not in role_map:
            role = "user"
        target_collection, prefix, id_field = role_map[role]
        user = await target_collection.find_one({"email": email})
        is_new = False
        if not user:
            is_new = True
            inserted_doc, inserted_id = await _create_user_in_collection(
                target_collection, prefix, id_field, email, name, role, picture
            )
            user = inserted_doc
            user_id = inserted_id
            is_profile_complete = False
        else:
            user_id = str(user.get("_id"))
            is_profile_complete = user.get("isProfileComplete", False)
        # Ensure tokens are plain strings, not bytes or b'...'
        access_token = create_access_token({"userId": user_id, "email": email, "role": role})
        refresh_token = create_refresh_token({"userId": user_id, "email": email, "role": role})

        def _to_str(t):
            if isinstance(t, bytes):
                return t.decode()
            if isinstance(t, str) and t.startswith("b'") and t.endswith("'"):
                return t[2:-1]
            return str(t)

        access_token_str = _to_str(access_token)
        refresh_token_str = _to_str(refresh_token)
        payload = {
            "success": True,
            "message": "Google login successful",
            "data": {
                "accessToken": access_token_str,
                "refreshToken": refresh_token_str,
                "userId": _safe(user_id),
                "email": _safe(email),
                "role": _safe(role),
                "isNewUser": is_new,
                "isProfileComplete": is_profile_complete,
            },
        }
        return JSONResponse(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Google exchange failed")
        error_payload = {"success": False, "error": f"Google login error: {str(e)}"}
        return JSONResponse(error_payload, status_code=500)




@router.delete("/auth/google/debug/clear_states")
async def clear_all_oauth_states():
    """
    Deletes all documents in the oauth_states collection and returns the count.
    Use for debugging CSRF state mismatch issues.
    """
    count = await oauth_states_collection.count_documents({})
    await oauth_states_collection.delete_many({})
    return {"success": True, "deleted": count}

#
# Complete-profile (unchanged logic, but cleaned/consistent)
#
@router.put("/patient/complete-profile/{user_id}")
@router.post("/patient/complete-profile/{user_id}")  # accept POST as fallback for plain form submit
async def complete_profile(user_id: str, request: Request):
    """
    Accepts JSON (recommended) or form-data (multipart/x-www-form-urlencoded).
    Updates patient document. This currently targets patient_collection.
    """
    try:
        content_type = (request.headers.get("content-type") or "").lower()
        if content_type.startswith("application/json"):
            payload = await request.json()
        else:
            form = await request.form()
            payload = {}
            # FormData iteration: handle multiple values and skip files
            # form.multi_items() exists in starlette form parser
            items = form.multi_items() if hasattr(form, "multi_items") else form.items()
            for k, v in items:
                # Skip files (UploadFile)
                if hasattr(v, "filename"):
                    # file upload handled separately if needed
                    continue
                payload[k] = v

        logger.info("complete_profile called user_id=%s payload=%s", user_id, payload)

        # build update dict
        update_fields = {}
        simple_fields = [
            "lastName", "phoneNumber", "gender", "maritalStatus",
            "bloodGroup", "address", "qualification", "specialization",
            "licenseNumber", "shortBio", "profilePhoto"
        ]
        for k in simple_fields:
            v = payload.get(k)
            if v not in (None, ""):
                update_fields[k] = v

        if payload.get("age") not in (None, ""):
            try:
                update_fields["age"] = int(payload.get("age"))
            except Exception:
                update_fields["age"] = payload.get("age")

        if payload.get("experience") not in (None, ""):
            try:
                update_fields["experience"] = int(payload.get("experience"))
            except Exception:
                update_fields["experience"] = payload.get("experience")

        dob = payload.get("dateOfBirth")
        if dob:
            try:
                update_fields["dateOfBirth"] = datetime.fromisoformat(dob)
            except Exception:
                update_fields["dateOfBirth"] = dob

        for arr_field in ["consultationMode", "language"]:
            v = payload.get(arr_field)
            if v:
                if isinstance(v, str):
                    update_fields[arr_field] = [s.strip() for s in v.split(",") if s.strip()]
                elif isinstance(v, list):
                    update_fields[arr_field] = v

        update_fields["isProfileComplete"] = True
        update_fields["updatedAt"] = datetime.utcnow()

        try:
            oid = ObjectId(user_id)
        except Exception:
            logger.error("Invalid ObjectId: %s", user_id)
            raise HTTPException(status_code=400, detail="Invalid user_id")

        # find_one_and_update to return the updated document
        updated = await patient_collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )

        if not updated:
            logger.warning("No document matched for _id: %s", user_id)
            raise HTTPException(status_code=404, detail="User not found")

        # sanitize _id for JSON
        updated["_id"] = str(updated["_id"])
        logger.info("Profile updated for %s -> %s", user_id, updated)
        return {"success": True, "message": "Profile updated successfully", "data": updated}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("complete_profile error")
        raise HTTPException(status_code=500, detail=str(e))
