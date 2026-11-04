from fastapi import FastAPI

from app.routers.vehicles import router as vehicles_router

app = FastAPI(
    title="ChargePilot Vehicle API",
    version="1.0.0",
    description="Vehicle management API for the ChargePilot project.",
)

app.include_router(vehicles_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}