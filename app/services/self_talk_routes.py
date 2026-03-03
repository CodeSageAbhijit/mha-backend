from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
import json
from app.services.llm_service import client
from app.utils.rate_limiter import limiter, RATE_LIMITS
from datetime import datetime
from app.database.mongo import self_talk_collection

router = APIRouter(prefix="/api", tags=["Self Talk"])

class SelfTalkRequest(BaseModel):
    message: str
    context: Optional[str] = "gentle_self_talk"
    userId: Optional[str] = None

class SelfTalkResponse(BaseModel):
    success: bool
    response: str
    emotion_detected: Optional[str] = None
    suggestions: Optional[list] = None
    data: Optional[dict] = None

@router.post("/self-talk", response_model=SelfTalkResponse)
@limiter.limit(RATE_LIMITS.get("default", "10/minute"))  # Rate limit: 10 requests per minute
async def get_self_talk_response(request: Request, req: SelfTalkRequest):
    """
    AI-powered gentle self-talk endpoint
    Uses Groq LLM to provide empathetic, supportive responses
    """
    try:
        if not req.message or not req.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "response": "Please share what's on your mind",
                    "error": "Empty message provided"
                }
            )

        # Create detailed prompt for compassionate response
        prompt = f"""You are a compassionate mental health support companion providing gentle self-talk guidance. 
The user has shared: "{req.message}"

Your role is to:
1. Acknowledge their feelings with empathy
2. Provide gentle, supportive affirmations
3. Offer one practical coping strategy if appropriate
4. Keep responses warm, conversational, and under 100 words

IMPORTANT: 
- Always be supportive and non-judgmental
- Use encouraging tone with emojis occasionally
- Never diagnose or provide medical advice
- Suggest professional help if user mentions crisis/harm

Respond with a JSON object:
{{
  "response": "<Your compassionate response>",
  "emotion_detected": "<primary emotion: anxiety/stress/sadness/overwhelm/joy/etc>",
  "suggestions": ["<coping strategy 1>", "<coping strategy 2>"]
}}

Respond ONLY with valid JSON, no markdown or extra text."""

        # Call Groq LLM
        if not client:
            # Fallback response if LLM not available
            return SelfTalkResponse(
                success=True,
                response="I hear you. It's brave to share your feelings. Remember, you're not alone. 💙 Take a deep breath and be gentle with yourself.",
                emotion_detected="support_needed",
                suggestions=["Practice deep breathing", "Take a short walk", "Reach out to someone you trust"]
            )

        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Higher temperature for more empathetic, varied responses
            max_tokens=300,
            top_p=0.9
        )

        response_text = response.choices[0].message.content.strip()
        
        try:
            # Parse JSON response
            result_data = json.loads(response_text)
            
            # Save to database if userId provided
            if req.userId:
                await self_talk_collection.insert_one({
                    "userId": req.userId,
                    "userMessage": req.message,
                    "aiResponse": result_data.get("response", ""),
                    "emotionDetected": result_data.get("emotion_detected"),
                    "timestamp": datetime.utcnow(),
                    "context": req.context
                })
            
            return SelfTalkResponse(
                success=True,
                response=result_data.get("response", "I'm here to listen. 💙"),
                emotion_detected=result_data.get("emotion_detected"),
                suggestions=result_data.get("suggestions", []),
                data=result_data
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, extract text from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result_data = json.loads(json_match.group())
                    return SelfTalkResponse(
                        success=True,
                        response=result_data.get("response", response_text),
                        emotion_detected=result_data.get("emotion_detected"),
                        suggestions=result_data.get("suggestions", [])
                    )
                except:
                    pass
            
            # Fallback to raw response
            return SelfTalkResponse(
                success=True,
                response=response_text[:500],  # Limit length
                emotion_detected="processing",
                suggestions=[]
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Self-talk error: {str(e)}")
        return SelfTalkResponse(
            success=False,
            response="I'm experiencing a temporary issue. Please try again. 💙 Remember, you're doing your best.",
            emotion_detected="error",
            suggestions=["Try again in a moment"]
        )

@router.get("/self-talk/history/{userId}")
@limiter.limit(RATE_LIMITS.get("default", "10/minute"))
async def get_self_talk_history(userId: str, request: Request):
    """
    Retrieve user's self-talk conversation history
    """
    try:
        conversations = await self_talk_collection.find(
            {"userId": userId}
        ).sort("timestamp", -1).limit(20).to_list(20)

        # Convert ObjectId to string
        for conv in conversations:
            conv["_id"] = str(conv["_id"])

        return {
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": str(e)
            }
        )

@router.delete("/self-talk/{conversationId}")
@limiter.limit(RATE_LIMITS.get("default", "10/minute"))
async def delete_conversation(conversationId: str, request: Request):
    """
    Delete a self-talk conversation (soft delete by user preference)
    """
    try:
        from bson import ObjectId
        
        result = await self_talk_collection.delete_one(
            {"_id": ObjectId(conversationId)}
        )
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "Conversation not found"
                }
            )
        
        return {
            "success": True,
            "message": "Conversation deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": str(e)
            }
        )
