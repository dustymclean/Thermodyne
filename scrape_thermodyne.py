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

CATEGORIES = [
    f"{BASE_URL}/wholesaler/us/vapes.html",
    f"{BASE_URL}/wholesaler/us/vaporizers.html",
    f"{BASE_URL}/wholesaler/us/wax-vaporizers.html"
]

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def extract_price(text):
    if not text:
        return 0.0
    text = text.replace('$', '').replace(',', '').strip()
    try:
        return float(text)
    except ValueError:
        return 0.0

async def login(page):
    print("🔍 Connecting to Thermodyne Portal...")
    await page.goto(LOGIN_URL)
    
    try:
        await page.wait_for_selector('input[name="login[username]"]', timeout=10000)
        await page.fill('input[name="login[username]"]', EMAIL)
        await page.fill('input[name="login[password]"]', PASSWORD)
        
        print("\n" + "="*50)
        print("⚠️ ACTION REQUIRED: Google reCAPTCHA Detected")
        print("1. Please solve the CAPTCHA in the browser window.")
        print("2. Click the 'Sign In' button manually.")
        print("3. The script will automatically resume once logged in.")
        print("="*50 + "\n")
        
        # Wait until the URL changes indicating successful login
        while "login" in page.url or "inqueryPost" in page.url:
            await asyncio.sleep(2)
            
        print(f"✅ Access Granted: Redirected to {page.url}")
    except Exception as e:
        print(f"⚠️ Login error: {e}")

async def scrape_category(page, cat_url):
    product_urls = []
    page_num = 1
    
    while True:
        url = f"{cat_url}?p={page_num}"
        print(f"📄 Scraping category page {page_num}: {url}")
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.select('.product-item-info a.product-item-link, .product-item-photo')
        new_links = 0
        for item in items:
            href = item.get('href')
            if href and href not in product_urls:
                product_urls.append(href)
                new_links += 1
                
        if new_links == 0:
            break
            
        # Check if there's a next page
        next_btn = soup.select_one('.action.next')
        if not next_btn:
            break
            
        page_num += 1
        
    return product_urls

async def scrape_product(page, p_url):
    await page.goto(p_url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)
    
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    title_el = soup.select_one('h1.page-title span, h1.page-title')
    title = title_el.text.strip() if title_el else "Unknown Product"
    handle = slugify(title)
    
    # Try multiple SKU selectors
    sku_el = soup.select_one('.product.attribute.sku .value, .sku .value, div[itemprop="sku"]')
    sku = sku_el.text.strip() if sku_el else ''
    
    # Price
    price_el = soup.select_one('.price-wrapper .price, .special-price .price, .normal-price .price')
    price = extract_price(price_el.text) if price_el else 0.0
    
    # Description / HTML Body
    desc_el = soup.select_one('.product.attribute.description .value, #description')
    body_html = str(desc_el) if desc_el else ''
    
    # Images
    images = []
    for img in soup.select('.gallery-placeholder img, .fotorama__img'):
        src = img.get('src')
        if src and src not in images:
            images.append(src)
            
    variant_image = images[0] if images else ''
    
    # Stock status
    stock_el = soup.select_one('.stock.available')
    in_stock = bool(stock_el)
    inventory_qty = 10 if in_stock else 0  # Dummy stock if available, as Magento might hide exact qty
    
    # Vendor/Brand (usually in attributes)
    brand_el = soup.select_one('.product.attribute.brand .value')
    brand = brand_el.text.strip() if brand_el else "Thermodyne Systems"
    
    flat_data = {
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
        "Product URL": p_url,
    }

    nested_data = {
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
            "available": in_stock,
            "inventory_quantity": inventory_qty,
            "variant_image": variant_image
        }],
        "all_images": images,
        "featured_image": variant_image,
        "url": p_url,
        "min_price": price,
        "max_price": price
    }
    
    return flat_data, nested_data if in_stock else None

async def main():
    print("=== Thermodyne Master Catalog Scraper ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await login(page)
        
        all_product_urls = []
        for cat_url in CATEGORIES:
            urls = await scrape_category(page, cat_url)
            print(f"   -> Found {len(urls)} products in {cat_url}")
            for u in urls:
                if u not in all_product_urls:
                    all_product_urls.append(u)
                    
        print(f"\nTotal unique products to scrape: {len(all_product_urls)}")
        
        flat_products = []
        nested_products = []
        
        for i, url in enumerate(all_product_urls, 1):
            print(f"   [{i}/{len(all_product_urls)}] Scraping: {url}")
            try:
                res = await scrape_product(page, url)
                if res and res[1]:  # If in stock
                    flat_products.append(res[0])
                    nested_products.append(res[1])
                else:
                    print(f"      -> Out of stock, skipped.")
            except Exception as e:
                print(f"      -> Error: {e}")
                
        if not flat_products:
            print("❌ No products were scraped or all were out of stock.")
            await browser.close()
            return
            
        print("\nWriting outputs...")
        
        # Save CSV
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
        print(f"✅ CSV Saved: {csv_path} ({len(flat_products)} rows)")
        
        # Save JSON
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
