from fastapi import APIRouter

router = APIRouter()

@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running and healthy.",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
def health():
    return {"status": "ok"}
