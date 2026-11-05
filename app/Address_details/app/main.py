from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="ChargePilot Address Details API",
    description="CRUD APIs for EV charging station address details.",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "ChargePilot Address Details API"}
