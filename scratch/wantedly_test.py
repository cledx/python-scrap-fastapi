import asyncio

from scraper.wantedly import scrape_wantedly


async def main() -> None:
    listings = await scrape_wantedly()
    for row in listings[:3]:
        print(row)


if __name__ == "__main__":
    asyncio.run(main())
