import asyncio
import csv
import json
import time
import re
import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

LOGIN_URL = "https://thermodynesystems.com/wholesaler/us/customer/account/login/"

CATEGORIES = [
    "https://thermodynesystems.com/wholesaler/us/vaporizers/portable-vaporizers.html",
    "https://thermodynesystems.com/wholesaler/us/vaporizers.html",
    "https://thermodynesystems.com/wholesaler/us/vaporizers/desktop-vaporizers.html",
    "https://thermodynesystems.com/wholesaler/us/vaporizers/zeus-accessories.html",
    "https://thermodynesystems.com/wholesaler/us/vaporizers/vaporizer-parts.html",
    "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/wax-pens.html",
    "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/electric-dab-rigs.html",
    "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/vapor-cup.html",
    "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/wax-pen-parts.html",
    "https://thermodynesystems.com/wholesaler/us/vapes.html",
    "https://thermodynesystems.com/wholesaler/us/vapes/510-thread-batteries.html",
    "https://thermodynesystems.com/wholesaler/us/vapes/vape-cartridges-and-parts.html"
]

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def extract_price(text):
    if not text: return 0.0
    text = text.replace('$', '').replace(',', '').replace('USD', '').replace(' ', '').strip()
    try: return float(text)
    except ValueError: return 0.0

async def main():
    print("=== Thermodyne MSRP Scraper ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔍 Connecting to Thermodyne Portal...")
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
        
        msrp_map = {}
        
        for cat_href in CATEGORIES:
            print(f"\n -> Scanning Category: {cat_href}")
            try:
                await page.goto(cat_href)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"    Failed to load category: {e}")
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
                    print("    No products found or timeout.")
                    break
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('li.item.product')
                
                print(f"    Found {len(products)} products on page {page_num}.")
                
                for item in products:
                    name_el = item.select_one('.product-item-name')
                    if not name_el: continue
                    title = name_el.text.strip().replace('\n', ' ')
                    handle = slugify(title)
                    
                    # Extract MSRP
                    msrp = 0.0
                    msrp_el = item.select_one('.old-price .price-wrapper')
                    if msrp_el and msrp_el.has_attr('data-price-amount'):
                        msrp = float(msrp_el['data-price-amount'])
                    else:
                        msrp_el_text = item.select_one('.old-price .price')
                        if msrp_el_text: msrp = extract_price(msrp_el_text.text)
                    
                    # Fallback to normal price if no old-price (sometimes MSRP is the only price)
                    if msrp == 0.0:
                        price_el = item.select_one('.price-final_price .price-wrapper')
                        if price_el and price_el.has_attr('data-price-amount'):
                            msrp = float(price_el['data-price-amount'])
                        else:
                            price_el_text = item.select_one('.price-final_price .price')
                            if price_el_text: msrp = extract_price(price_el_text.text)
                            
                    if handle not in msrp_map or msrp > msrp_map[handle]:
                        msrp_map[handle] = msrp
                        
                next_btn = await page.query_selector('.action.next')
                if next_btn and await next_btn.is_visible():
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle")
                    page_num += 1
                else:
                    break
                    
        print(f"\n✅ Finished! Found MSRP for {len(msrp_map)} unique products.")
        
        # Now update the JSON and CSV
        json_path = os.path.join(os.path.dirname(__file__), "Thermodyne_Products.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        updated_count = 0
        for p in data['products']:
            handle = p['handle']
            if handle in msrp_map and msrp_map[handle] > 0:
                msrp = msrp_map[handle]
                # Update prices
                p['min_price'] = msrp
                p['max_price'] = msrp
                for variant in p.get('in_stock_variants', []):
                    # We might have added slight premiums for colors
                    base_old = p.get('min_price', msrp)
                    diff = variant['price'] - base_old
                    diff = diff if diff > 0 else 0
                    variant['price'] = msrp + diff
                updated_count += 1
                
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Updated {updated_count} products in JSON with correct MSRP.")
        
        csv_path = os.path.join(os.path.dirname(__file__), "Thermodyne_Products.csv")
        csv_rows = []
        headers = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                handle = row.get("Handle", "")
                if handle in msrp_map and msrp_map[handle] > 0:
                    msrp = msrp_map[handle]
                    row["Variant Price"] = msrp
                    row["Compare At Price"] = msrp
                csv_rows.append(row)
                
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(csv_rows)
            
        print("Updated CSV with correct MSRP.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
