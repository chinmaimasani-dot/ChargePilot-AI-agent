
from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.routers.users import router as users_router
from app.routers.vehicles import router as vehicles_router
from app.slot_availability.routers import router as slots_availability_router
from app.charging_stations.models import Address, ChargingStation
from app.charging_stations.routers.charging_stations import (
    router as charging_stations_router,)
from app.address_details.routers.address import api_router as address_router
from app.address_details.models import address

app = FastAPI(
    title="ChargePilot AI API",
    version="1.0.0",
    description="Vehicle and Charging Station Management APIs.",
)

# User APIs
app.include_router(users_router)

# Vehicle APIs
app.include_router(vehicles_router)

# Vehicle APIs
app.include_router(address_router)

# Charging Station APIs
app.include_router(charging_stations_router)
# Slot Availability APIs
app.include_router(slots_availability_router)

# GenAI Chat APIs (Member 4)
app.include_router(chat_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

