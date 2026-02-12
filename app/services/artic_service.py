import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_artwork(external_id: str) -> dict | None:
    url = f"{settings.artic_api_base_url}/artworks/{external_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch artwork {external_id} from ArtIC API: {e}")
            return None

    if r.status_code == 200:
        return (r.json().get("data") or {})
    if r.status_code == 404:
        return None
    if r.status_code == 400:
        return None
    return None
