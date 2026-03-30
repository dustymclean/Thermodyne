import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://thermodynesystems.com/wholesaler/us/customer/account/login/")
        await page.fill('input[name="login[username]"]', "admin@pixies-pantry.com")
        await page.fill('input[name="login[password]"]', "New5432")
        print("Please solve the CAPTCHA and login!")
        
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(1)
            
        print("Logged in! Going to vapes.html")
        await page.goto("https://thermodynesystems.com/wholesaler/us/vapes.html")
        await page.wait_for_selector('li.item.product')
        
        print("Clicking resources button...")
        await page.click('li.item.product a.detail.html-btn')
        await asyncio.sleep(5)
        
        with open("modal_resources.html", "w") as f:
            f.write(await page.content())
            
        print("Closing resources modal...")
        await page.keyboard.press('Escape')
        await asyncio.sleep(2)
        
        print("Clicking Add to Cart button...")
        await page.click('li.item.product a.add_to_cart.html-btn')
        await asyncio.sleep(5)
        
        with open("modal_cart.html", "w") as f:
            f.write(await page.content())
            
        print("Done saving modals.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
