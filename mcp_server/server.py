
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_BASE_URL = os.getenv(
    "CHARGEPILOT_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

mcp = FastMCP("ChargePilot MCP Server")
TIMEOUT = 15.0


def call_api(
    method: str,
    endpoint: str,
    params: dict | None = None,
    payload: dict | None = None,
) -> str:
    """Call an existing ChargePilot FastAPI endpoint."""

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.request(
                method=method,
                url=f"{API_BASE_URL}{endpoint}",
                params=params,
                json=payload,
            )

            response.raise_for_status()

            return json.dumps(
                response.json(),
                indent=2,
                default=str,
            )

    except httpx.HTTPStatusError as exc:
        return json.dumps({
            "error": "ChargePilot API returned an error",
            "status_code": exc.response.status_code,
            "details": exc.response.text[:500],
        })

    except httpx.RequestError as exc:
        return json.dumps({
            "error": "Could not connect to ChargePilot API",
            "details": str(exc),
        })


# --------------------------------------------------
# CHARGING STATION TOOLS
# --------------------------------------------------

@mcp.tool()
def get_nearby_stations(skip: int = 0, limit: int = 10) -> str:
    """Retrieve charging stations with pagination."""

    if skip < 0 or limit < 1 or limit > 100:
        return json.dumps({"error": "Invalid pagination values."})

    return call_api(
        "GET",
        "/api/v1/stations",
        params={"skip": skip, "limit": limit},
    )


@mcp.tool()
def get_station_details(station_id: int) -> str:
    """Retrieve details for a specific charging station."""

    if station_id < 1:
        return json.dumps({"error": "Invalid station ID."})

    return call_api(
        "GET",
        f"/api/v1/stations/{station_id}",
    )


@mcp.tool()
def check_available_slots(station_id: int) -> str:
    """Check available vehicle slots at a charging station."""

    if station_id < 1:
        return json.dumps({"error": "Invalid station ID."})

    return call_api(
        "GET",
        f"/api/v1/slots-availability/station/{station_id}",
    )


# --------------------------------------------------
# RESERVATION TOOLS
# --------------------------------------------------

@mcp.tool()
def create_reservation(
    user_id: int,
    vehicle_id: int,
    station_id: int,
    start_time: str,
    end_time: str,
) -> str:
    """
    Book a charging station slot.

    Times must be ISO 8601 datetime strings.
    Example: 2026-11-07T10:00:00+05:30
    """

    if min(user_id, vehicle_id, station_id) < 1:
        return json.dumps({"error": "IDs must be greater than zero."})

    try:
        from datetime import datetime

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        if start.tzinfo is None or end.tzinfo is None:
            return json.dumps({
                "error": "Please provide timezone-aware ISO 8601 times."
            })

        if end <= start:
            return json.dumps({
                "error": "End time must be later than start time."
            })

    except ValueError:
        return json.dumps({
            "error": "Invalid datetime. Use ISO 8601 format."
        })

    return call_api(
        "POST",
        "/api/v1/reservations/",
        payload={
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "station_id": station_id,
            "start_time": start_time,
            "end_time": end_time,
        },
    )


@mcp.tool()
def get_reservations(
    user_id: int | None = None,
    station_id: int | None = None,
) -> str:
    """Retrieve reservations, optionally filtered by user or station."""

    if user_id is not None and user_id < 1:
        return json.dumps({"error": "Invalid user ID."})

    if station_id is not None and station_id < 1:
        return json.dumps({"error": "Invalid station ID."})

    params = {}

    if user_id is not None:
        params["user_id"] = user_id

    if station_id is not None:
        params["station_id"] = station_id

    return call_api(
        "GET",
        "/api/v1/reservations/",
        params=params,
    )


@mcp.tool()
def get_reservation_details(reservation_id: int) -> str:
    """Retrieve details of a specific reservation."""

    if reservation_id < 1:
        return json.dumps({"error": "Invalid reservation ID."})

    return call_api(
        "GET",
        f"/api/v1/reservations/{reservation_id}",
    )


@mcp.tool()
def cancel_reservation(reservation_id: int) -> str:
    """Cancel an existing confirmed reservation."""

    if reservation_id < 1:
        return json.dumps({"error": "Invalid reservation ID."})

    return call_api(
        "PATCH",
        f"/api/v1/reservations/{reservation_id}/cancel",
    )


@mcp.tool()
def complete_reservation(reservation_id: int) -> str:
    """Mark a confirmed reservation as completed."""

    if reservation_id < 1:
        return json.dumps({"error": "Invalid reservation ID."})

    return call_api(
        "PATCH",
        f"/api/v1/reservations/{reservation_id}/complete",
    )


if __name__ == "__main__":
    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = 8001
    mcp.run(transport="streamable-http")
