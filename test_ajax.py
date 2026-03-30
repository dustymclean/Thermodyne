import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://thermodynesystems.com/wholesaler/us/customer/account/login/")
        await page.fill('input[name="login[username]"]', "admin@pixies-pantry.com")
        await page.fill('input[name="login[password]"]', "New5432")
        await page.click('button#send2')
        
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(1)
            
        print("Logged in!")
        # Instead of clicking around, we just hit the AJAX endpoint directly with the cookies!
        # Product ID 2309 (Tronian Omegatron) or 2995
        ajax_url = "https://thermodynesystems.com/wholesaler/us/productdetailpopup/Content/?id=2309"
        
        print(f"Fetching AJAX: {ajax_url}")
        resp = await page.goto(ajax_url)
        text = await resp.text()
        
        with open("ajax_payload.txt", "w") as f:
            f.write(text)
            
        print("Done. Saved to ajax_payload.txt")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
