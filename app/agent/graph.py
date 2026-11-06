

import re
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.rag.service import generate_answer


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


class AgentState(TypedDict):
    question: str
    route: str
    answer: str


def route_question(state: AgentState):
    question = state["question"].lower()

    mcp_keywords = [
        "station",
        "charging",
        "available slot",
        "availability",
        "vehicle slot",
        "reservation",
        "booking",
        "book a slot",
        "cancel booking",
        "cancel reservation",
        "complete reservation",
        "complete booking",
    ]

    if any(word in question for word in mcp_keywords):
        return {"route": "mcp"}

    return {"route": "rag"}


def rag_node(state: AgentState):
    result = generate_answer(state["question"])

    return {
        "answer": (
            result["answer"]
            + "\n\nSources: "
            + ", ".join(result["sources"])
        )
    }


def extract_id(pattern, question):
    match = re.search(pattern, question.lower())
    return int(match.group(1)) if match else None


async def mcp_node(state: AgentState):
    question = state["question"]
    lower_question = question.lower()

    # Extract IDs from the user's question.
    station_id = extract_id(
        r"\bstation\s*(?:id\s*)?#?(\d+)\b",
        question,
    )

    reservation_id = extract_id(
        r"\breservation\s*(?:id\s*)?#?(\d+)\b",
        question,
    )

    user_id = extract_id(
        r"\buser\s*(?:id\s*)?#?(\d+)\b",
        question,
    )

    vehicle_id = extract_id(
        r"\bvehicle\s*(?:id\s*)?#?(\d+)\b",
        question,
    )

    # Identify the requested operation.
    if "cancel" in lower_question and (
        "reservation" in lower_question or "booking" in lower_question
    ):
        tool_name = "cancel_reservation"

        if not reservation_id:
            return {
                "answer": "Please provide the reservation ID you want to cancel."
            }

        arguments = {"reservation_id": reservation_id}

    elif (
        ("complete" in lower_question or "finish" in lower_question)
        and ("reservation" in lower_question or "booking" in lower_question)
    ):
        tool_name = "complete_reservation"

        if not reservation_id:
            return {
                "answer": "Please provide the reservation ID you want to complete."
            }

        arguments = {"reservation_id": reservation_id}

    elif (
        "reservation" in lower_question or "booking" in lower_question
    ) and any(word in lower_question for word in ["detail", "information"]):
        tool_name = "get_reservation_details"

        if not reservation_id:
            return {
                "answer": "Please provide a reservation ID."
            }

        arguments = {"reservation_id": reservation_id}

    elif (
        "reservation" in lower_question or "booking" in lower_question
    ) and any(word in lower_question for word in ["show", "list", "my", "all", "get", "view"]):
        tool_name = "get_reservations"

        if "my" in lower_question and not user_id:
            return {
                "answer": "Please provide your user ID so I can retrieve your reservations."
            }

        arguments = {}

        if user_id:
            arguments["user_id"] = user_id

        if station_id:
            arguments["station_id"] = station_id

    elif any(word in lower_question for word in ["book", "create", "reserve"]):
        tool_name = "create_reservation"

        # Extract ISO 8601 timestamps with timezone.
        start_match = re.search(
            r"\bstart(?:_time)?\s*[:=]?\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2}))",
            question,
            re.IGNORECASE,
        )

        end_match = re.search(
            r"\bend(?:_time)?\s*[:=]?\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2}))",
            question,
            re.IGNORECASE,
        )

        missing = []

        if not user_id:
            missing.append("user ID")
        if not vehicle_id:
            missing.append("vehicle ID")
        if not station_id:
            missing.append("station ID")
        if not start_match:
            missing.append("timezone-aware start time")
        if not end_match:
            missing.append("timezone-aware end time")

        if missing:
            return {
                "answer": (
                    "To book your charging slot, please provide: "
                    + ", ".join(missing)
                    + ".\n\n"
                    + "Example:\n"
                    + "Book a reservation for user 3, vehicle 5, "
                    + "station 1, start_time 2026-11-07T10:00:00+05:30, "
                    + "end_time 2026-11-07T11:00:00+05:30"
                )
            }

        arguments = {
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "station_id": station_id,
            "start_time": start_match.group(1),
            "end_time": end_match.group(1),
        }

    elif "slot" in lower_question or "availability" in lower_question:
        tool_name = "check_available_slots"

        if not station_id:
            return {
                "answer": "Please specify a station ID to check available slots."
            }

        arguments = {"station_id": station_id}

    elif "detail" in lower_question:
        tool_name = "get_station_details"

        if not station_id:
            return {
                "answer": "Please specify a station ID to retrieve station details."
            }

        arguments = {"station_id": station_id}

    else:
        tool_name = "get_nearby_stations"
        arguments = {"skip": 0, "limit": 10}

    # Connect to MCP and execute the selected tool.
    async with streamablehttp_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            answer = "\n".join(
                item.text
                for item in result.content
                if hasattr(item, "text")
            )

    return {
        "answer": answer or "No result returned from MCP."
    }


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("router", route_question)
    workflow.add_node("rag", rag_node)
    workflow.add_node("mcp", mcp_node)

    workflow.add_edge(START, "router")

    workflow.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {
            "rag": "rag",
            "mcp": "mcp",
        },
    )

    workflow.add_edge("rag", END)
    workflow.add_edge("mcp", END)

    return workflow.compile()


chargepilot_graph = build_graph()


async def ask_chargepilot(question: str):
    result = await chargepilot_graph.ainvoke({
        "question": question,
        "route": "",
        "answer": "",
    })

    return result
