import asyncio
import csv
import json
import time
import re
import os
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://thermodynesystems.com"
LOGIN_URL = f"{BASE_URL}/wholesaler/us/customer/account/login/"
EMAIL = "admin@pixies-pantry.com"
PASSWORD = "New5432"

OUTPUT_CSV = "Thermodyne_Products.csv"
OUTPUT_JSON = "Thermodyne_Products.json"

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def extract_price(text):
    if not text: return 0.0
    text = text.replace('$', '').replace(',', '').strip()
    try: return float(text)
    except ValueError: return 0.0

async def main():
    print("=== Thermodyne Systems Click-Based Scraper ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("1. Authenticating (Manual CAPTCHA Check)...")
        await page.goto(LOGIN_URL)
        await page.fill('input[name="login[username]"]', EMAIL)
        await page.fill('input[name="login[password]"]', PASSWORD)
        
        print("\n⚠️ ACTION REQUIRED: Google reCAPTCHA Detected")
        print("Please solve the CAPTCHA in the browser window and manually click 'Sign In'.")
        print("The script will automatically resume once logged in.\n")
        
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(2)
            
        print(f"✅ Access Granted: Redirected to {page.url}")
        
        # We need to find all category links via the top navigation menu
        print("2. Extracting Top Navigation Categories via Clicks...")
        nav_elements = await page.query_selector_all('nav.navigation ul.ui-menu li.level0 > a')
        nav_hrefs = []
        for nav in nav_elements:
            href = await nav.get_attribute('href')
            if href and BASE_URL in href and href not in nav_hrefs:
                nav_hrefs.append(href)
                
        print(f"Found {len(nav_hrefs)} top-level categories.")
        
        flat_products = []
        nested_products = []
        scraped_handles = set()

        for cat_href in nav_hrefs:
            print(f"\n -> Clicking Category: {cat_href}")
            try:
                await page.goto(cat_href)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"    Failed to load category: {e}")
                continue

            page_num = 1
            while True:
                print(f"    Scanning Grid (Page {page_num})...")
                # Wait for products to load
                await page.wait_for_selector('.product-item-info', state='attached', timeout=5000)
                
                # Get all product elements on this page
                products = await page.query_selector_all('.product-item-info a.product-item-link, .product-item-photo')
                
                product_hrefs = []
                for p in products:
                    href = await p.get_attribute('href')
                    if href and href not in product_hrefs:
                        product_hrefs.append(href)
                        
                print(f"    Found {len(product_hrefs)} products to click on this page.")
                
                for phref in product_hrefs:
                    try:
                        # Open product in a new tab via middle-click to preserve grid pagination
                        async with context.expect_page() as new_page_info:
                            el = await page.query_selector(f'a[href="{phref}"]')
                            if el:
                                await el.click(modifiers=["Meta"] if os.uname().sysname == 'Darwin' else ["Control"])
                            else:
                                continue
                                
                        new_page = await new_page_info.value
                        await new_page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)  # Delay to not get blocked
                        
                        html = await new_page.content()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        title_el = soup.select_one('h1.page-title span, h1.page-title')
                        title = title_el.text.strip().replace('\n', ' ') if title_el else "Unknown"
                        handle = slugify(title)
                        
                        if handle in scraped_handles:
                            await new_page.close()
                            continue
                        scraped_handles.add(handle)
                        
                        sku_el = soup.select_one('.product.attribute.sku .value, .sku .value, div[itemprop="sku"]')
                        sku = sku_el.text.strip().replace('\n', '') if sku_el else ''
                        
                        price_el = soup.select_one('.price-wrapper .price, .special-price .price, .normal-price .price')
                        price = extract_price(price_el.text) if price_el else 0.0
                        
                        desc_el = soup.select_one('.product.attribute.description .value, #description')
                        body_html = str(desc_el) if desc_el else ''
                        
                        images = []
                        for img in soup.select('.gallery-placeholder img, .fotorama__img'):
                            src = img.get('src')
                            if src and src not in images: images.append(src)
                                
                        variant_image = images[0] if images else ''
                        
                        stock_el = soup.select_one('.stock.available')
                        in_stock = bool(stock_el)
                        inventory_qty = 10 if in_stock else 0
                        
                        brand_el = soup.select_one('.product.attribute.brand .value')
                        brand = brand_el.text.strip() if brand_el else "Thermodyne Systems"
                        
                        print(f"      Scraped: {title} (${price})")
                        
                        if in_stock:
                            flat_products.append({
                                "Handle": handle,
                                "Brand": brand,
                                "Title": title,
                                "Vendor": brand,
                                "Product Type": "Hardware",
                                "Tags": "Vaporizer",
                                "Body (HTML)": body_html,
                                "Option1 Name": "Default",
                                "Option1 Value": "Default Title",
                                "Option2 Name": "",
                                "Option2 Value": "",
                                "Option3 Name": "",
                                "Option3 Value": "",
                                "Variant SKU": sku,
                                "Variant Price": price,
                                "Compare At Price": price,
                                "Inventory Quantity": inventory_qty,
                                "Variant Image": variant_image,
                                "Featured Image": variant_image,
                                "All Images": " | ".join(images),
                                "Published At": datetime.now().isoformat(),
                                "Product URL": phref,
                            })
                            
                            nested_products.append({
                                "handle": handle,
                                "brand": brand,
                                "title": title,
                                "vendor": brand,
                                "product_type": "Hardware",
                                "tags": ["Vaporizer"],
                                "body_html": body_html,
                                "options": [{"name": "Default", "values": ["Default Title"]}],
                                "in_stock_variants": [{
                                    "variant_id": sku,
                                    "sku": sku,
                                    "option1_name": "Default",
                                    "option1_value": "Default Title",
                                    "price": price,
                                    "available": True,
                                    "inventory_quantity": inventory_qty,
                                    "variant_image": variant_image
                                }],
                                "all_images": images,
                                "featured_image": variant_image,
                                "url": phref,
                                "min_price": price,
                                "max_price": price
                            })
                        
                        await new_page.close()
                    except Exception as e:
                        print(f"      Error on {phref}: {e}")
                        
                # Check for pagination (Next Page button)
                next_btn = await page.query_selector('.action.next')
                if next_btn and await next_btn.is_visible():
                    print(f"    Clicking to next page...")
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle")
                    page_num += 1
                else:
                    break
                    
        print(f"\n✅ Finished! Scraped {len(flat_products)} in-stock items.")
        
        CSV_FIELDS = [
            "Handle", "Brand", "Title", "Vendor", "Product Type", "Tags",
            "Body (HTML)", "Option1 Name", "Option1 Value",
            "Option2 Name", "Option2 Value", "Option3 Name", "Option3 Value",
            "Variant SKU", "Variant Price", "Compare At Price",
            "Inventory Quantity", "Variant Image", "Featured Image", "All Images",
            "Published At", "Product URL",
        ]
        
        csv_path = os.path.join(os.path.dirname(__file__), OUTPUT_CSV)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(flat_products)
        print(f"✅ CSV Saved: {csv_path}")
        
        json_path = os.path.join(os.path.dirname(__file__), OUTPUT_JSON)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "source": BASE_URL,
                "total_products": len(nested_products),
                "products": nested_products
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON Saved: {json_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
