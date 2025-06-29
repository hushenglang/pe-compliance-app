from fastapi import APIRouter

router = APIRouter(
    prefix="/api/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "financial-compliance-api"} 