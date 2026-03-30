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
    print("=== Thermodyne Master Full Scraper ===")
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
            
        print(f"✅ Access Granted: Redirected to {page.url}")
        await asyncio.sleep(2)
        
        # Load existing json to enrich or build from scratch
        json_path = os.path.join(os.path.dirname(__file__), "Thermodyne_Products.json")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {"source": "https://thermodynesystems.com", "total_products": 0, "products": []}
            
        existing_products = {p['handle']: p for p in data.get('products', [])}
        scraped_handles = set()
        
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
                    
                    if handle in scraped_handles:
                        continue
                        
                    # Extract MSRP
                    msrp = 0.0
                    msrp_el = item.select_one('.old-price .price-wrapper')
                    if msrp_el and msrp_el.has_attr('data-price-amount'):
                        msrp = float(msrp_el['data-price-amount'])
                    else:
                        msrp_el_text = item.select_one('.old-price .price')
                        if msrp_el_text: msrp = extract_price(msrp_el_text.text)
                    
                    if msrp == 0.0:
                        price_el = item.select_one('.price-final_price .price-wrapper')
                        if price_el and price_el.has_attr('data-price-amount'):
                            msrp = float(price_el['data-price-amount'])
                        else:
                            price_el_text = item.select_one('.price-final_price .price')
                            if price_el_text: msrp = extract_price(price_el_text.text)
                            
                    # Initialize product object
                    prod = existing_products.get(handle, {
                        "handle": handle, "title": title, "min_price": msrp, "max_price": msrp,
                        "url": cat_href, "brand": "Thermodyne Systems", "tags": ["Hardware"], "product_type": "Hardware"
                    })
                    prod['min_price'] = msrp
                    prod['max_price'] = msrp
                    
                    # Click Resources Modal
                    res_btn = item.select_one('a.detail.html-btn')
                    data_id = res_btn.get('data-id') if res_btn else None
                    
                    desc_html = prod.get('body_html', '')
                    images = prod.get('all_images', [])
                    specs = prod.get('specs', {})
                    resources = prod.get('resources', [])
                    
                    if data_id:
                        print(f"      Clicking Resources for {title}...")
                        try:
                            # Using playwright to click the specific button
                            await page.click(f'a.detail.html-btn[data-id="{data_id}"]')
                            # Wait for modal to appear and load content
                            await page.wait_for_selector('.modal-popup.modal-slide._show, .action-close', timeout=5000)
                            await asyncio.sleep(3) # Wait for ajax content
                            
                            modal_html = await page.content()
                            modal_soup = BeautifulSoup(modal_html, 'html.parser')
                            
                            # Scrape Modal Content
                            # Look for active modal
                            modal_active = modal_soup.select_one('.modal-popup._show')
                            if modal_active:
                                # Extract description text/html
                                desc = modal_active.select_one('.product.attribute.description, .description, .product-description, [data-role="content"]')
                                if desc:
                                    desc_html = str(desc)
                                
                                # Extract images (Photos)
                                imgs = modal_active.select('img')
                                for img in imgs:
                                    src = img.get('src') or img.get('data-original')
                                    if src and src not in images and "placeholder" not in src:
                                        images.append(src)
                                        
                                # Extract specs and sell sheets (links to pdfs/docs)
                                links = modal_active.select('a')
                                for link in links:
                                    href = link.get('href')
                                    text = link.text.strip()
                                    if href and ('.pdf' in href or 'download' in href.lower() or 'sheet' in text.lower()):
                                        if {"text": text, "url": href} not in resources:
                                            resources.append({"text": text, "url": href})
                                            
                                # Extract specs (tables or ul)
                                spec_list = modal_active.select('table, ul.specs')
                                if spec_list:
                                    specs_html = str(spec_list[0])
                                    specs['html'] = specs_html
                                    
                            # Close Modal
                            close_btn = await page.query_selector('.modal-popup._show .action-close')
                            if close_btn:
                                await close_btn.click()
                                await asyncio.sleep(1)
                                
                        except Exception as e:
                            print(f"        -> Failed to extract modal: {e}")
                            # Force close any open modals
                            try:
                                await page.keyboard.press('Escape')
                            except:
                                pass
                                
                    prod['body_html'] = desc_html
                    prod['all_images'] = images
                    prod['specs'] = specs
                    prod['resources'] = resources
                    if images:
                        prod['featured_image'] = images[0]
                    
                    existing_products[handle] = prod
                    scraped_handles.add(handle)
                    
                next_btn = await page.query_selector('.action.next')
                if next_btn and await next_btn.is_visible():
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle")
                    page_num += 1
                else:
                    break
                    
        print(f"\n✅ Finished! Scraped detailed resources for {len(scraped_handles)} products.")
        
        # Save back to JSON
        data['products'] = list(existing_products.values())
        data['total_products'] = len(data['products'])
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Updated JSON with real descriptions, specs, resources, and photos!")
        
        # Also generate CSV
        # ...
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
