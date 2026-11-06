
from fastapi import FastAPI
from app.rag.router import router as rag_router
from app.routers.users import router as users_router
from app.routers.vehicles import router as vehicles_router
from app.slot_availability.routers import router as slots_availability_router
from app.charging_stations.models import Address, ChargingStation
from app.reservations.routers.reservation import router as reservations_router
from app.charging_stations.routers.charging_stations import (
    router as charging_stations_router,
)

app = FastAPI(
    title="ChargePilot AI API",
    version="1.0.0",
    description="Vehicle and Charging Station Management APIs.",
)

# User APIs
app.include_router(users_router)

# Vehicle APIs
app.include_router(vehicles_router)
app.include_router(rag_router)
# Charging Station APIs
app.include_router(charging_stations_router)
# Slot Availability APIs
app.include_router(slots_availability_router)
app.include_router(reservations_router)
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

