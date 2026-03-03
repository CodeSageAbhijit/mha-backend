import os
import json
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Initialize Groq client only if API key is available
client = None
try:
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully with mixtral-8x7b-32768 model")
    else:
        print("⚠️ GROQ_API_KEY not found. LLM features will be disabled.")
except ImportError as ie:
    print(f"⚠️ Required package not installed ({ie}). Install with: pip install groq")
except Exception as e:
    print(f"⚠️ Failed to initialize Groq client: {e}. LLM features will be disabled.")

async def analyze_assessment(data: dict) -> dict:
    """
    Send assessment answers to Groq LLM and return structured analysis
    """
    if not client:
        # Return default analysis if Groq client is not available
        return {
            "anxiety": 0.5,
            "depression": 0.5,
            "stress": 0.5,
            "emotional_health": 0.5,
            "summary": "Assessment completed. Please consult with a healthcare professional for detailed analysis."
        }
    answers_text = "\n".join(
        [f"Q: {a['question']} | Selected: {a['selectedAnswer']}" for a in data["answers"]]
    )

    prompt = f"""You are an expert mental health assessment analyzer. Analyze the following user responses and provide scores.

Assessment Category: {data['category']}

User Responses:
{answers_text}

Provide your analysis in the following JSON format:
{{
  "anxiety": <number between 0 and 1>,
  "depression": <number between 0 and 1>,
  "stress": <number between 0 and 1>,
  "emotional_health": <number between 0 and 1>,
  "summary": "<2-3 line personalized summary>"
}}

Respond ONLY with the JSON object, no additional text."""

    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extract JSON from response
        response_text = response.choices[0].message.content.strip()
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If JSON parsing fails, extract the JSON from the response
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback if parsing still fails
        return {
            "anxiety": 0.5,
            "depression": 0.5,
            "stress": 0.5,
            "emotional_health": 0.5,
            "summary": "Assessment completed. Detailed analysis unavailable at this moment."
        }
