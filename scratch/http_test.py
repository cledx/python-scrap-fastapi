import asyncio
import httpx


async def fetch_httpbin_get() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("https://httpbin.org/get")
        response.raise_for_status()
        print(response.json())

if __name__ == "__main__":
    asyncio.run(fetch_httpbin_get())