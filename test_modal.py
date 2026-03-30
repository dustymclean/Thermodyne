import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://thermodynesystems.com/wholesaler/us/customer/account/login/")
        await page.fill('input[name="login[username]"]', "admin@pixies-pantry.com")
        await page.fill('input[name="login[password]"]', "New5432")
        print("Waiting to log in...")
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(1)
            
        print("Logged in! Going to vapes.html")
        await page.goto("https://thermodynesystems.com/wholesaler/us/vapes.html")
        await page.wait_for_selector('li.item.product')
        
        # Click the first "Resources" button
        print("Clicking resources button...")
        await page.click('li.item.product a.detail.html-btn')
        
        print("Waiting for modal...")
        await asyncio.sleep(3)
        
        html = await page.content()
        with open("modal_state.html", "w") as f:
            f.write(html)
            
        print("Saved modal state.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
