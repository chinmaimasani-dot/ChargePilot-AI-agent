
import asyncio

from app.agent.graph import ask_chargepilot


async def main():
    print("=" * 60)
    print("       CHARGEPILOT AI - INTELLIGENT AGENT")
    print("=" * 60)

    questions = [
        "What is the purpose of ChargePilot AI?",
        "Show all charging stations",
        "Check available slots at station 1",
        "Show details of station 2",
        "Show all reservations for user 3",
        "Show details of reservation 2",
        "Cancel reservation 1",
    ]

    for question in questions:
        print(f"\nUSER QUESTION: {question}")
        print("-" * 60)

        try:
            result = await ask_chargepilot(question)
            print("AI RESPONSE:")
            print(result["answer"])

        except Exception as exc:
            print("ERROR:", str(exc))


if __name__ == "__main__":
    asyncio.run(main())
