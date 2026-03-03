import httpx
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import requests
from starlette.requests import Request

router = APIRouter(prefix="/api/address", tags=["Address"])

BASE_URL = "https://countriesnow.space/api/v0.1/countries/positions"

# Helper: retry wrapper
async def fetch_with_retry(method: str, url: str, json: dict | None = None, retries: int = 3, timeout: float = 30.0):
    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.lower() == "get":
                    resp = await client.get(url)
                else:
                    resp = await client.post(url, json=json)

                resp.raise_for_status()
                return resp.json()

        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            if attempt == retries:
                return {"error": f"Request timed out after {retries} attempts"}
            await asyncio.sleep(2 ** attempt)  # exponential backoff
        except httpx.HTTPStatusError as e:
            return {"error": f"External API error {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


@router.get("/countries")
async def get_countries():
    async with httpx.AsyncClient() as client:
        resp = await client.get(BASE_URL)
        if resp.status_code != 200:
            return JSONResponse(
                status_code=resp.status_code,
                content={"success": False, "message": "Failed to fetch countries"}
            )
        data = resp.json()
        countries = [item["name"] for item in data.get("data", [])]
        return {"success": True, "country": countries}

API_URL = "https://countriesnow.space/api/v0.1/countries/cities"

