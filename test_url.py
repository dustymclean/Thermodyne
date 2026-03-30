import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        resp = await page.goto("https://thermodynesystems.com/wholesaler/us/tronian-omegatron.html")
        print("URL:", page.url)
        print("Status:", resp.status)
        
        # Test if description exists
        desc = await page.query_selector('.product.attribute.description')
        print("Description exists?", bool(desc))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
