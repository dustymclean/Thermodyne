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
            try:
                if response.status == 200 and ("json" in response.headers.get("content-type", "") or "text/html" in response.headers.get("content-type", "")):
                    text = await response.text()
                    if "spConfig" in text or "gallery" in text or "description" in text:
                        captured_data.append({
                            "url": response.url,
                            "type": response.headers.get("content-type"),
                            "text": text[:2000] # store preview
                        })
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
        
        print("Force-clicking Resources on the first product...")
        # Get data-id
        btn_id = await page.evaluate("document.querySelector('a.detail.html-btn').getAttribute('data-id')")
        
        if btn_id:
            # Click Resources
            await page.evaluate(f"document.querySelector('a.detail.html-btn[data-id=\"{btn_id}\"]').click()")
            await asyncio.sleep(4)
            
            # Close it properly
            await page.evaluate("document.querySelectorAll('.action-close').forEach(b => b.click())")
            await asyncio.sleep(1)
            await page.evaluate("document.querySelectorAll('.modals-overlay, .modals-wrapper').forEach(e => e.remove())")
            
            # Click Add to Cart
            print("Force-clicking Add to Cart...")
            await page.evaluate(f"document.querySelector('a.add_to_cart.html-btn[data-id=\"{btn_id}\"]').click()")
            await asyncio.sleep(4)
            
        print(f"Captured {len(captured_data)} payloads.")
        for i, d in enumerate(captured_data):
            print(f"[{i}] {d['url']} ({d['type']})")
            with open(f"intercept_{i}.txt", "w") as f:
                f.write(d['text'])
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
