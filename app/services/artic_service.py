import httpx

BASE = "https://api.artic.edu/api/v1"

async def get_artwork(external_id: str) -> dict | None:
    url = f"{BASE}/artworks/{external_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
        except httpx.RequestError as e:
            return None

    if r.status_code == 200:
        return (r.json().get("data") or {})
    if r.status_code == 404:
        return None
    if r.status_code == 400:
        return None
    return None
