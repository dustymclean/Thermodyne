import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        captured_data = []
        
        async def handle_response(response):
            if "application/json" in response.headers.get("content-type", "") or "text/html" in response.headers.get("content-type", ""):
                try:
                    text = await response.text()
                    if "spConfig" in text or "description" in text or "gallery" in text:
                        captured_data.append({
                            "url": response.url,
                            "type": response.headers.get("content-type"),
                            "length": len(text)
                        })
                        with open(f"intercepted_{len(captured_data)}.txt", "w") as f:
                            f.write(text[:10000]) # just peek
                except:
                    pass
                    
        page.on("response", handle_response)
        
        await page.goto("https://thermodynesystems.com/wholesaler/us/customer/account/login/")
        await page.fill('input[name="login[username]"]', "admin@pixies-pantry.com")
        await page.fill('input[name="login[password]"]', "New5432")
        print("Please log in.")
        
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(1)
            
        print("Logged in! Going to portable vaporizers...")
        await page.goto("https://thermodynesystems.com/wholesaler/us/vaporizers/portable-vaporizers.html")
        await page.wait_for_selector('li.item.product')
        
        print("Clicking Add to Cart...")
        # Get the first add_to_cart button
        btn = await page.query_selector('a.add_to_cart.html-btn')
        if btn:
            await btn.click()
            await asyncio.sleep(3)
        
        print("Clicking Resources...")
        await page.keyboard.press('Escape')
        await asyncio.sleep(1)
        res_btn = await page.query_selector('a.detail.html-btn')
        if res_btn:
            await res_btn.click()
            await asyncio.sleep(3)
            
        print("Captured responses:", len(captured_data))
        for d in captured_data:
            print(d["url"], d["type"])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
