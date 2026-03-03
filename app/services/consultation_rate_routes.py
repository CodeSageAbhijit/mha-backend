from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Optional, List, Union
from app.database.mongo import (
    psychiatrist_call_rates, counselor_call_rates,
    psychiatrist_call_rates, mentor_call_rates, business_coach_call_rates, buddy_call_rates,
    psychiatrist_collection, counselor_collection,
    psychiatrist_collection, mentor_collection, business_coach_collection, buddy_collection
)
from app.utils.auth_guard import get_current_user
from app.models.rate_schemas import ConsultationRates, GetConsultationRatesResponse
from app.config.default_pricing import get_default_pricing, get_all_professional_roles
from bson import ObjectId

async def get_provider_by_id(provider_id: str, provider_type: str) -> Union[dict, None]:
    """Get provider by custom ID or ObjectId."""
    provider_collections = {
        "psychiatrist": psychiatrist_collection,
        "counselor": counselor_collection,
        "mentor": mentor_collection,
        "business_coach": business_coach_collection,
        "buddy": buddy_collection
    }
    
    id_fields = {
        "psychiatrist": "psychiatristId",
        "counselor": "counselorId",
        "mentor": "mentorId",
        "business_coach": "businessCoachId",
        "buddy": "buddyId"
    }
    
    collection = provider_collections.get(provider_type)
    id_field = id_fields.get(provider_type)
    
    if not collection or not id_field:
        return None
    
    # First try custom ID format
    provider = await collection.find_one({id_field: provider_id})
    if provider:
        return provider
        
    # Then try ObjectId if it's a valid format
    try:
        if ObjectId.is_valid(provider_id):
            provider = await collection.find_one({"_id": ObjectId(provider_id)})
            return provider
    except:
        pass
        
    return None

router = APIRouter(prefix="/api/consultation-rates", tags=["ConsultationRates"])

@router.post("/{provider_type}/set")
async def set_consultation_rates(
    provider_type: str,
    payload: ConsultationRates,
    user=Depends(get_current_user)
):
    """Set consultation rates for professional roles (psychiatrist, mentor, counselor, business_coach, buddy).
    
    NOTE: This is for salary-based professionals with NO commission.
    Wallet is visible to them but salary/commission information is not shown in their portal.
    """
    try:
        valid_types = get_all_professional_roles()
        if provider_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider type. Valid types: {', '.join(valid_types)}"
            )

        # Verify user role matches provider type
        if user.get("role") != provider_type:
            raise HTTPException(
                status_code=403,
                detail=f"Only {provider_type}s can set their consultation rates"
            )

        provider_id = user["roleUserId"]
        
        # Map provider types to rate collections
        rate_collections = {
            "psychiatrist": psychiatrist_call_rates,
            "counselor": counselor_call_rates,
            "psychiatrist": psychiatrist_call_rates,
            "mentor": mentor_call_rates,
            "business_coach": business_coach_call_rates,
            "buddy": buddy_call_rates
        }
        
        id_fields = {
            "psychiatrist": "psychiatristId",
            "counselor": "counselorId",
            "mentor": "mentorId",
            "business_coach": "businessCoachId",
            "buddy": "buddyId"
        }
        
        collection = rate_collections.get(provider_type)
        id_field = id_fields.get(provider_type)

        # Verify provider exists and is active
        provider = await get_provider_by_id(provider_id, provider_type)
        
        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"{provider_type.replace('_', ' ').title()} not found"
            )

        if not provider.get("isActive", False):
            raise HTTPException(
                status_code=400,
                detail=f"{provider_type.capitalize()} account is not active"
            )

        # Update or insert rates
        await collection.update_one(
            {id_field: provider_id},
            {
                "$set": {
                    "voiceCallRate": payload.voiceCallRate,
                    "videoCallRate": payload.videoCallRate,
                    "inPerson15Min": payload.inPerson15Min,
                    "inPerson30Min": payload.inPerson30Min,
                    "inPerson60Min": payload.inPerson60Min,
                    "updatedAt": datetime.utcnow(),
                    "providerType": provider_type,
                    id_field: provider_id
                }
            },
            upsert=True
        )

        return {
            "success": True,
            "providerId": provider_id,
            "providerType": provider_type,
            "rates": {
                "videoCallRate": payload.videoCallRate,
                "voiceCallRate": payload.voiceCallRate,
                "inPerson15Min": payload.inPerson15Min,
                "inPerson30Min": payload.inPerson30Min,
                "inPerson60Min": payload.inPerson60Min
            },
            "message": f"Consultation rates updated successfully"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_type}/rates/{provider_id}", response_model=GetConsultationRatesResponse)
async def get_consultation_rates(
    provider_type: str,
    provider_id: str,
    user=Depends(get_current_user)
):
    """Get consultation rates for a specific provider."""
    try:
        if provider_type not in ["psychiatrist", "counselor"]:
            raise HTTPException(status_code=400, detail="Invalid provider type")

        collection = psychiatrist_call_rates if provider_type == "psychiatrist" else counselor_call_rates
        id_field = "psychiatristId" if provider_type == "psychiatrist" else "counselorId"
        
        # Get rates from database
        rates = await collection.find_one({id_field: provider_id})
        
        if not rates:
            raise HTTPException(
                status_code=404,
                detail=f"No rates found for this {provider_type}"
            )

        # Get provider details to check available consultation modes
        provider = await get_provider_by_id(provider_id, provider_type)
        
        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"{provider_type.capitalize()} not found"
            )

        # Get provider's custom ID
        provider_custom_id = provider.get("providerId") or str(provider["_id"])

        consultation_modes = provider.get("consultationMode", "").split(",")
        consultation_modes = [mode.strip() for mode in consultation_modes if mode.strip()]

        return GetConsultationRatesResponse(
            providerId=provider_id,
            providerName=f"{provider.get('firstName', '')} {provider.get('lastName', '')}".strip(),
            specialization=provider.get('specialization'),
            qualification=provider.get('qualification'),
            videoCallRate=rates.get("videoCallRate", 0),
            voiceCallRate=rates.get("voiceCallRate", 0),
            inPerson15Min=rates.get("inPerson15Min", 0),
            inPerson30Min=rates.get("inPerson30Min", 0),
            inPerson60Min=rates.get("inPerson60Min", 0),
            consultationModes=consultation_modes,
            isActive=provider.get("isActive", False),
            experience=provider.get("experienceYears"),
            rating=provider.get("rating", 0.0),
            totalReviews=provider.get("totalReviews", 0),
            updatedAt=rates.get("updatedAt").isoformat()
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_type}/list")
async def list_provider_rates(
    provider_type: str,
    search: Optional[str] = Query(None, description="Search by provider name or specialization"),
    min_experience: Optional[int] = Query(None, description="Minimum years of experience"),
    max_video_rate: Optional[int] = Query(None, description="Maximum video call rate"),
    max_voice_rate: Optional[int] = Query(None, description="Maximum voice call rate"),
    consultation_mode: Optional[str] = Query(None, description="Filter by consultation mode (video, voice, in-person)"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    sort_by: Optional[str] = Query("rating", description="Sort by: rating, experience, video_rate, voice_rate"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user)
):
    """Get consultation rates for all providers of specified type with filtering and sorting."""
    try:
        if provider_type not in ["psychiatrist", "counselor"]:
            raise HTTPException(status_code=400, detail="Invalid provider type")

        collection = psychiatrist_call_rates if provider_type == "psychiatrist" else counselor_call_rates
        provider_collection = psychiatrist_collection if provider_type == "psychiatrist" else counselor_collection
        id_field = "psychiatristId" if provider_type == "psychiatrist" else "counselorId"

        # Build query filters
        provider_filter = {"isActive": True}
        
        # Only add filters if they have non-empty values
        if search and search.strip():
            provider_filter["$or"] = [
                {"firstName": {"$regex": search.strip(), "$options": "i"}},
                {"lastName": {"$regex": search.strip(), "$options": "i"}},
                {"specialization": {"$regex": search.strip(), "$options": "i"}}
            ]
            
        if min_experience is not None and min_experience >= 0:
            provider_filter["experienceYears"] = {"$gte": min_experience}
            
        if specialization and specialization.strip():
            provider_filter["specialization"] = {"$regex": specialization.strip(), "$options": "i"}
            
        if consultation_mode and consultation_mode.strip():
            # Handle multiple consultation modes separated by commas
            modes = [mode.strip() for mode in consultation_mode.split(",") if mode.strip()]
            if modes:
                provider_filter["consultationMode"] = {"$regex": "|".join(modes), "$options": "i"}

        # Get providers matching filters
        providers = await provider_collection.find(provider_filter).to_list(None)
        
        if not providers:
            return {
                "success": True,
                "provider_type": provider_type,
                "total": 0,
                "page": skip // limit + 1,
                "pages": 0,
                "rates": []
            }

        # Get both ObjectId and providerId values
        provider_obj_ids = [str(p["_id"]) for p in providers]
        provider_custom_ids = [p.get(id_field) for p in providers if p.get(id_field)]
        all_provider_ids = provider_obj_ids + provider_custom_ids

        # Get rates for matched providers using either ID type
        rates_filter = {"$or": [
            {id_field: {"$in": all_provider_ids}},
            {id_field: {"$in": [ObjectId(id) for id in provider_obj_ids if ObjectId.is_valid(id)]}}
        ]}
        
        # Only add rate filters if they have valid values
        if max_video_rate is not None and max_video_rate >= 0:
            rates_filter["videoCallRate"] = {"$lte": max_video_rate}
        if max_voice_rate is not None and max_voice_rate >= 0:
            rates_filter["voiceCallRate"] = {"$lte": max_voice_rate}

        rates_list = []
        async for rate in collection.find(rates_filter):
            provider_id = rate.get(id_field)
            # Try to find provider by both custom ID and ObjectId
            provider = next((p for p in providers if str(p["_id"]) == provider_id or p.get(id_field) == provider_id), None)
            
            if provider:
                consultation_modes = provider.get("consultationMode", "").split(",")
                consultation_modes = [mode.strip() for mode in consultation_modes if mode.strip()]
                
                provider_data = {
                    "providerId": provider_id,
                    "providerName": f"{provider.get('firstName', '')} {provider.get('lastName', '')}".strip(),
                    "specialization": provider.get("specialization"),
                    "qualification": provider.get("qualification"),
                    "videoCallRate": rate.get("videoCallRate", 0),
                    "voiceCallRate": rate.get("voiceCallRate", 0),
                    "inPerson15Min": rate.get("inPerson15Min", 0),
                    "inPerson30Min": rate.get("inPerson30Min", 0),
                    "inPerson60Min": rate.get("inPerson60Min", 0),
                    "consultationModes": consultation_modes,
                    "isActive": provider.get("isActive", False),
                    "experience": provider.get("experienceYears", 0),
                    "rating": provider.get("rating", 0.0),
                    "totalReviews": provider.get("totalReviews", 0),
                    "updatedAt": rate.get("updatedAt").isoformat()
                }
                rates_list.append(provider_data)

        # Sort results
        sort_key = {
            "rating": "rating",
            "experience": "experience",
            "video_rate": "videoCallRate",
            "voice_rate": "voiceCallRate"
        }.get(sort_by, "rating")

        reverse = sort_order.lower() == "desc"
        rates_list.sort(key=lambda x: (x.get(sort_key) or 0), reverse=reverse)

        # Paginate results
        paginated_rates = rates_list[skip:skip + limit]

        return {
            "success": True,
            "provider_type": provider_type,
            "total": len(rates_list),
            "page": skip // limit + 1,
            "pages": (len(rates_list) + limit - 1) // limit,
            "rates": paginated_rates
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
