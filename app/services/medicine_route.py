from fastapi import FastAPI, APIRouter, HTTPException, Query
import httpx

router = APIRouter(prefix="/api/medicines", tags=["Medicines"])

RXNAV_URL = "https://rxnav.nlm.nih.gov/REST/drugs.json"

@router.get("/search")
async def search_medicine(name: str = Query(..., description="Enter medicine name")):
    """
    Search medicines by name using RxNav getDrugs API.
    Always returns a list (empty if not found).
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(RXNAV_URL, params={"name": name}, timeout=10.0)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="External API error")

        data = resp.json()
        medicines = []

        drug_group = data.get("drugGroup", {})
        for group in drug_group.get("conceptGroup", []) or []:
            for item in group.get("conceptProperties", []) or []:
                medicines.append({
                    "rxcui": item.get("rxcui"),
                    "name": item.get("name"),
                    "synonym": item.get("synonym"),
                    "tty": item.get("tty")
                })

        return {"success": True, "query": name, "count": len(medicines), "medicines": medicines}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="External API request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))
