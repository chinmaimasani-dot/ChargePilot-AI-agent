from fastapi import FastAPI

from chargepilot_slot_availability_api.routers.slots_availability import router as slots_router


app = FastAPI(
    title="ChargePilot Slot Availability API",
    description="Manage current two, three, and four wheeler slot counts by charging station.",
    version="1.0.0",
)

app.include_router(slots_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
