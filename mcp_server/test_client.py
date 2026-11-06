
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    server_url = "http://127.0.0.1:8001/mcp"

    async with streamablehttp_client(server_url) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            print("\n=== RESERVATION CANCELLATION TEST ===")

            result = await session.call_tool(
                "cancel_reservation",
                arguments={"reservation_id": 1},
            )

            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)

            print("\n=== CANCELLATION TEST COMPLETED ===")


if __name__ == "__main__":
    asyncio.run(main())
