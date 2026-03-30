import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Logging in...")
        await page.goto("https://thermodynesystems.com/wholesaler/us/customer/account/login/")
        await page.fill('input[name="login[username]"]', "admin@pixies-pantry.com")
        await page.fill('input[name="login[password]"]', "New5432")
        print("Waiting for CAPTCHA/Login to complete...")
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(1)
            
        print("Logged in! Going to vapes.html")
        await page.goto("https://thermodynesystems.com/wholesaler/us/vapes.html")
        await page.wait_for_selector('li.item.product')
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        p_item = soup.select_one('li.item.product')
        print(p_item.prettify())
        
        with open("logged_in_item.html", "w") as f:
            f.write(p_item.prettify())
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
