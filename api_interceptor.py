import asyncio
import json
import os
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

LOGIN_URL = "https://thermodynesystems.com/wholesaler/us/customer/account/login/"
CATEGORIES = [
    "https://thermodynesystems.com/wholesaler/us/vaporizers/portable-vaporizers.html",
    "https://thermodynesystems.com/wholesaler/us/vaporizers.html",
    "https://thermodynesystems.com/wholesaler/us/vaporizers/desktop-vaporizers.html",
    "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/wax-pens.html",
    "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/electric-dab-rigs.html",
    "https://thermodynesystems.com/wholesaler/us/vapes/510-thread-batteries.html",
    "https://thermodynesystems.com/wholesaler/us/vapes/vape-cartridges-and-parts.html"
]

def slugify(text):
    text = str(text).lower().strip()
    return re.sub(r'[\s_-]+', '-', re.sub(r'[^\w\s-]', '', text))

async def main():
    print("=== Thermodyne API Interceptor ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
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
            
        print("✅ Logged in! Intercepting internal payloads...")
        json_path = os.path.join(os.path.dirname(__file__), "Thermodyne_Products.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        existing_products = {p['handle']: p for p in data.get('products', [])}
        scraped_handles = set()
        
        for cat_href in CATEGORIES:
            print(f"\n -> Scanning grid for API IDs in: {cat_href}")
            try:
                await page.goto(cat_href)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                continue

            try:
                limiter = await page.query_selector('select#limiter')
                if limiter:
                    await page.select_option('select#limiter', 'all')
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
            except:
                pass

            page_num = 1
            while True:
                try:
                    await page.wait_for_selector('li.item.product', state='attached', timeout=5000)
                except:
                    break
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('li.item.product')
                
                print(f"    Page {page_num}: Found {len(products)} products to intercept.")
                
                for item in products:
                    name_el = item.select_one('.product-item-name')
                    if not name_el: continue
                    title = name_el.text.strip().replace('\n', ' ')
                    handle = slugify(title)
                    
                    if handle in scraped_handles:
                        continue
                        
                    res_btn = item.select_one('a.detail.html-btn')
                    data_id = res_btn.get('data-id') if res_btn else None
                    
                    prod = existing_products.get(handle)
                    if not prod:
                        continue
                        
                    if data_id:
                        ajax_url = f"https://thermodynesystems.com/wholesaler/us/productdetailpopup/Content/?id={data_id}"
                        print(f"      Intercepting Payload -> {title}")
                        
                        try:
                            # Fetch the JSON payload using the session cookies
                            # Create a new page so we don't navigate away from the grid
                            api_page = await context.new_page()
                            resp = await api_page.goto(ajax_url)
                            payload_text = await resp.text()
                            
                            try:
                                payload_json = json.loads(payload_text)
                                html_output = payload_json.get('output', '')
                                modal_soup = BeautifulSoup(html_output, 'html.parser')
                                
                                # Extract real description
                                desc = modal_soup.select_one('.description, .product-description, [data-role="content"], .product.attribute.description .value')
                                if desc:
                                    prod['body_html'] = str(desc)
                                    
                                # Extract full high-res galleries
                                images = prod.get('all_images', [])
                                for img in modal_soup.select('img'):
                                    src = img.get('src') or img.get('data-original')
                                    if src and src not in images and "placeholder" not in src:
                                        images.append(src)
                                prod['all_images'] = images
                                
                                # Extract resources
                                resources = prod.get('resources', [])
                                for link in modal_soup.select('a'):
                                    href = link.get('href')
                                    text = link.text.strip()
                                    if href and ('.pdf' in href or 'download' in href.lower() or 'sheet' in text.lower()):
                                        if {"text": text, "url": href} not in resources:
                                            resources.append({"text": text, "url": href})
                                prod['resources'] = resources
                                
                                # Find spConfig or swatch logic for SKUs and Variables!
                                sp_config = None
                                for script in modal_soup.find_all('script'):
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
                                    prod['options'] = options
                                    
                            except json.JSONDecodeError:
                                print(f"        -> Not valid JSON payload")
                                
                            await api_page.close()
                        except Exception as e:
                            print(f"        -> Intercept Failed: {e}")
                            try:
                                await api_page.close()
                            except:
                                pass
                                
                    existing_products[handle] = prod
                    scraped_handles.add(handle)
                    
                next_btn = await page.query_selector('.action.next')
                if next_btn and await next_btn.is_visible():
                    await page.evaluate("document.querySelector('.action.next').click()")
                    await page.wait_for_load_state("networkidle")
                    page_num += 1
                else:
                    break
                    
        print(f"\n✅ Finished API Interception! Deeply enriched {len(scraped_handles)} items.")
        
        data['products'] = list(existing_products.values())
        data['total_products'] = len(data['products'])
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        await browser.close()
        
        print("Rebuilding storefront with new payload data...")
        os.system("python3 generate_storefront.py")
        print("Storefront rebuild complete.")

if __name__ == "__main__":
    asyncio.run(main())
