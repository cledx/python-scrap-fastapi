import asyncio
import httpx
from bs4 import BeautifulSoup

async def fetch_httpbin_get() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("https://books.toscrape.com/")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        soup2 = BeautifulSoup(response.text, "html.parser")
        books = soup.select("article.product_pod")
        print(soup.prettify())
        print(soup2.prettify())

        for book in books:
            title = book.select_one("h3 a")["title"]
            price = book.select_one("p.price_color").text
            print(f"{title} - {price}")

if __name__ == "__main__":
    asyncio.run(fetch_httpbin_get())