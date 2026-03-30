import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print("Checking catalog/product/view...")
        resp = await page.goto("https://thermodynesystems.com/wholesaler/us/catalog/product/view/id/2309")
        print("Final URL:", page.url)
        print("Status:", resp.status)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
