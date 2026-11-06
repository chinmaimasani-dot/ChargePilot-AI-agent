from fastapi import APIRouter
from app.address_details.routers.endpoints.address import router as address_router

api_router = APIRouter()
api_router.include_router(address_router)
