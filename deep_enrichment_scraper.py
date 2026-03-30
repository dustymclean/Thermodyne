import asyncio
import csv
import json
import time
import re
import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://thermodynesystems.com/wholesaler/us"
LOGIN_URL = f"{BASE_URL}/customer/account/login/"

async def main():
    print("=== Thermodyne Deep Enrichment Scraper ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"🔍 Navigating to {LOGIN_URL} ...")
        await page.goto(LOGIN_URL)
        await page.fill('input[name="login[username]"]', "admin@pixies-pantry.com")
        await page.fill('input[name="login[password]"]', "New5432")
        
        print("\n" + "="*50)
        print("⚠️ ACTION REQUIRED: Google reCAPTCHA Detected")
        print("1. Please solve the CAPTCHA in the browser window.")
        print("2. Click the 'Sign In' button manually.")
        print("3. The script will automatically resume once logged in.")
        print("="*50 + "\n")
        
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(2)
            
        print(f"✅ Access Granted: Redirected to {page.url}")
        await asyncio.sleep(2)
        
        # Load the existing JSON to enrich
        json_path = os.path.join(os.path.dirname(__file__), "Thermodyne_Products.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        products = data.get('products', [])
        print(f"Preparing to deep-scrape {len(products)} products...")
        
        updated_count = 0
        
        for p_data in products:
            handle = p_data.get('handle')
            if not handle:
                continue
                
            p_url = f"{BASE_URL}/{handle}.html"
            print(f"    -> Scraping Details: {p_url}")
            
            try:
                # Go directly to the product page bypassing grids
                await page.goto(p_url)
                # Wait for either description, or fallback to body load
                try:
                    await page.wait_for_selector('.product.attribute.description', timeout=8000)
                except:
                    await asyncio.sleep(3)
                    
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Verify we aren't redirected to a category grid
                if "vaporizers" in page.url and page.url != p_url and ".html" not in handle:
                    # sometimes handles have hyphens but actual url might be different
                    pass
                
                # 1. Extract Full HTML from .product.attribute.description
                desc_el = soup.select_one('.product.attribute.description .value, #description')
                if desc_el:
                    p_data['body_html'] = str(desc_el)
                    print("       [+] Description found")
                
                # 2. Extract full image galleries from .gallery-placeholder
                images = []
                for img in soup.select('.gallery-placeholder img, .fotorama__img, .product.media img'):
                    src = img.get('src') or img.get('data-original')
                    if src and src not in images and "placeholder" not in src:
                        images.append(src)
                if images:
                    p_data['all_images'] = images
                    p_data['featured_image'] = images[0]
                    print(f"       [+] {len(images)} Gallery Images found")
                    
                # 3. Pull Magento Swatch JSON for Variables
                options = [{"name": "Default", "values": ["Default Title"]}]
                variants = []
                
                sp_config = None
                for script in soup.find_all('script'):
                    if script.string and 'spConfig' in script.string:
                        try:
                            match = re.search(r'"spConfig":\s*(\{.*?\})\s*,', script.string, re.DOTALL)
                            if match:
                                sp_config = json.loads(match.group(1))
                        except:
                            pass
                            
                if sp_config and "attributes" in sp_config:
                    options = []
                    for attr_id, attr_data in sp_config["attributes"].items():
                        opt_name = attr_data.get("label", "Option")
                        opt_values = [v.get("label") for v in attr_data.get("options", [])]
                        options.append({"name": opt_name, "values": opt_values})
                    print(f"       [+] Magento swatch variables found: {', '.join([o['name'] for o in options])}")
                    
                    # Try extracting full variant map if needed
                    # For now, we update the top-level options for the storefront to render
                    
                p_data['options'] = options
                updated_count += 1
                
            except Exception as e:
                print(f"       [!] Failed to scrape {p_url}: {e}")
                
        # Save back to JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Finished! Deep-enriched {updated_count} products.")
        
        await browser.close()
        
        # Re-run generator
        print("Rebuilding storefront...")
        os.system("python3 generate_storefront.py")
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
