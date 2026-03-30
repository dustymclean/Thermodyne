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

OUTPUT_CSV = "Thermodyne_Products.csv"
OUTPUT_JSON = "Thermodyne_Products.json"

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def extract_price(text):
    if not text: return 0.0
    text = text.replace('$', '').replace(',', '').replace('USD', '').strip()
    try: return float(text)
    except ValueError: return 0.0

async def main():
    print("=== Thermodyne Systems Grid Scraper ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("Extracting Top Navigation Categories via Grid...")
        nav_hrefs = [
            "https://thermodynesystems.com/wholesaler/us/vapes.html",
            "https://thermodynesystems.com/wholesaler/us/vapes/510-thread-batteries.html",
            "https://thermodynesystems.com/wholesaler/us/vapes/vape-cartridges-and-parts.html",
            "https://thermodynesystems.com/wholesaler/us/vaporizers.html",
            "https://thermodynesystems.com/wholesaler/us/vaporizers/desktop-vaporizers.html",
            "https://thermodynesystems.com/wholesaler/us/vaporizers/portable-vaporizers.html",
            "https://thermodynesystems.com/wholesaler/us/vaporizers/vaporizer-parts.html",
            "https://thermodynesystems.com/wholesaler/us/vaporizers/zeus-accessories.html",
            "https://thermodynesystems.com/wholesaler/us/wax-vaporizers.html",
            "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/electric-dab-rigs.html",
            "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/vapor-cup.html",
            "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/wax-pen-parts.html",
            "https://thermodynesystems.com/wholesaler/us/wax-vaporizers/wax-pens.html"
        ]
        
        flat_products = []
        nested_products = []
        scraped_handles = set()

        for cat_href in nav_hrefs:
            print(f"\n -> Scanning Category: {cat_href}")
            try:
                await page.goto(cat_href)
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"    Failed to load category: {e}")
                continue

            # change show to all if possible
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
                print(f"    Scanning Grid (Page {page_num})...")
                try:
                    await page.wait_for_selector('li.item.product', state='attached', timeout=5000)
                except:
                    print("    No products found or timeout.")
                    break
                
                # Get all product elements on this page
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('li.item.product')
                
                print(f"    Found {len(products)} products on this page.")
                
                for p in products:
                    name_el = p.select_one('.product-item-name')
                    if not name_el: continue
                    title = name_el.text.strip().replace('\n', ' ')
                    handle = slugify(title)
                    
                    if handle in scraped_handles:
                        continue
                        
                    price_el = p.select_one('.price')
                    price = extract_price(price_el.text) if price_el else 0.0
                    
                    img_el = p.select_one('img.product-image-photo')
                    img_src = img_el.get('data-original') or img_el.get('src') if img_el else ''
                    
                    # check availability
                    unavailable = p.select_one('.stock.unavailable')
                    in_stock = not bool(unavailable)
                    inventory_qty = 10 if in_stock else 0
                    
                    if not in_stock:
                        continue
                        
                    scraped_handles.add(handle)
                    
                    # infer brand from title
                    brand = "Thermodyne Systems"
                    if "utillian" in title.lower(): brand = "Utillian"
                    elif "zeus" in title.lower(): brand = "Zeus"
                    elif "puffco" in title.lower(): brand = "Puffco"
                    elif "yocan" in title.lower(): brand = "Yocan"
                    elif "lookah" in title.lower(): brand = "Lookah"
                    elif "linx" in title.lower(): brand = "Linx"
                    elif "tronian" in title.lower(): brand = "Tronian"
                    
                    print(f"      Scraped: {title} (${price})")
                    
                    flat_products.append({
                        "Handle": handle,
                        "Brand": brand,
                        "Title": title,
                        "Vendor": brand,
                        "Product Type": "Hardware",
                        "Tags": "Vaporizer",
                        "Body (HTML)": "",
                        "Option1 Name": "Default",
                        "Option1 Value": "Default Title",
                        "Option2 Name": "",
                        "Option2 Value": "",
                        "Option3 Name": "",
                        "Option3 Value": "",
                        "Variant SKU": handle,
                        "Variant Price": price,
                        "Compare At Price": price,
                        "Inventory Quantity": inventory_qty,
                        "Variant Image": img_src,
                        "Featured Image": img_src,
                        "All Images": img_src,
                        "Published At": datetime.now().isoformat(),
                        "Product URL": cat_href,
                    })
                    
                    nested_products.append({
                        "handle": handle,
                        "brand": brand,
                        "title": title,
                        "vendor": brand,
                        "product_type": "Hardware",
                        "tags": ["Vaporizer"],
                        "body_html": "",
                        "options": [{"name": "Default", "values": ["Default Title"]}],
                        "in_stock_variants": [{
                            "variant_id": handle,
                            "sku": handle,
                            "option1_name": "Default",
                            "option1_value": "Default Title",
                            "price": price,
                            "available": True,
                            "inventory_quantity": inventory_qty,
                            "variant_image": img_src
                        }],
                        "all_images": [img_src] if img_src else [],
                        "featured_image": img_src,
                        "url": cat_href,
                        "min_price": price,
                        "max_price": price
                    })
                        
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
