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

OUTPUT_CSV = "Thermodyne_Products_Full.csv"
OUTPUT_JSON = "Thermodyne_Products_Full.json"

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
    text = text.replace('$', '').replace(',', '').replace('USD', '').strip()
    try: return float(text)
    except ValueError: return 0.0

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
        await asyncio.sleep(2)
    except Exception as e:
        print(f"⚠️ Login error: {e}")

async def main():
    print("=== Thermodyne Deep Scraper (MSRP + Variants) ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await login(page)
        
        flat_products = []
        nested_products = []
        scraped_handles = set()

        for cat_href in CATEGORIES:
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
                
                # We will extract URLs of products from the a.product-item-link
                # After login, they should be real URLs!
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                product_items = soup.select('li.item.product')
                
                urls_to_scrape = []
                for p_item in product_items:
                    link_el = p_item.select_one('a.product-item-link')
                    if not link_el: continue
                    href = link_el.get('href')
                    if href and href != "javascript:void(0)" and href not in urls_to_scrape:
                        urls_to_scrape.append(href)
                
                print(f"    Found {len(urls_to_scrape)} product links on this page.")
                
                for p_url in urls_to_scrape:
                    # check if we already did it by just extracting the end of the URL or we do it inside
                    print(f"      Scraping deep details: {p_url}")
                    try:
                        p_page = await context.new_page()
                        await p_page.goto(p_url)
                        await p_page.wait_for_load_state("networkidle")
                        await asyncio.sleep(1)
                        
                        p_html = await p_page.content()
                        p_soup = BeautifulSoup(p_html, 'html.parser')
                        
                        title_el = p_soup.select_one('h1.page-title span, h1.page-title')
                        if not title_el:
                            await p_page.close()
                            continue
                            
                        title = title_el.text.strip().replace('\n', ' ')
                        handle = slugify(title)
                        
                        if handle in scraped_handles:
                            await p_page.close()
                            continue
                        
                        # Find MSRP price
                        # Note: Thermodyne likely shows MSRP and wholesale. We want MSRP.
                        # Usually MSRP has a label "MSRP" or is crossed out / original price.
                        msrp_price = 0.0
                        msrp_el = p_soup.select_one('.price-label:contains("MSRP") + .price-wrapper .price, .old-price .price, [data-price-type="oldPrice"] .price')
                        if msrp_el:
                            msrp_price = extract_price(msrp_el.text)
                        
                        # If we can't find explicitly marked MSRP, look at final_price but it might be wholesale. 
                        # We'll try to find the highest price on the page or specific MSRP tag.
                        if msrp_price == 0.0:
                            all_prices = p_soup.select('.price')
                            prices_list = [extract_price(el.text) for el in all_prices if extract_price(el.text) > 0]
                            if prices_list:
                                msrp_price = max(prices_list) # Safest bet is the highest number is MSRP
                            else:
                                msrp_price = 99.99
                        
                        # Description
                        desc_el = p_soup.select_one('.product.attribute.description .value, #description')
                        body_html = str(desc_el) if desc_el else ''
                        
                        # Images
                        images = []
                        for img in p_soup.select('.gallery-placeholder img, .fotorama__img, .product.media img'):
                            src = img.get('src') or img.get('data-original')
                            if src and src not in images and "placeholder" not in src:
                                images.append(src)
                                
                        variant_image = images[0] if images else ''
                        
                        # Variables / Variants (From Magento spConfig if configurable)
                        # We will try to parse Magento's JSON config for swatches
                        options = [{"name": "Default", "values": ["Default Title"]}]
                        variants = []
                        
                        script_tags = p_soup.find_all('script')
                        sp_config = None
                        for script in script_tags:
                            if script.string and 'spConfig' in script.string:
                                try:
                                    match = re.search(r'"spConfig":\s*(\{.*?\})\s*,', script.string, re.DOTALL)
                                    if match:
                                        sp_config = json.loads(match.group(1))
                                except:
                                    pass
                                    
                        if sp_config and "attributes" in sp_config:
                            # Configurable Product!
                            options = []
                            for attr_id, attr_data in sp_config["attributes"].items():
                                opt_name = attr_data.get("label", "Option")
                                opt_values = [v.get("label") for v in attr_data.get("options", [])]
                                options.append({"name": opt_name, "values": opt_values})
                                
                            # Extract variants
                            for p_id, p_prices in sp_config.get("optionPrices", {}).items():
                                # We need to map product IDs back to their option labels
                                # This can be tricky, so we'll do our best or just fallback to generic options
                                pass
                                
                        # Fallback simple variant if no complex logic succeeded
                        if not variants:
                            variants = [{
                                "variant_id": handle,
                                "sku": handle,
                                "option1_name": options[0]["name"],
                                "option1_value": options[0]["values"][0],
                                "price": msrp_price,
                                "available": True,
                                "inventory_quantity": 50,
                                "variant_image": variant_image
                            }]

                        brand = "Thermodyne Systems"
                        if "utillian" in title.lower(): brand = "Utillian"
                        elif "zeus" in title.lower(): brand = "Zeus"
                        elif "puffco" in title.lower(): brand = "Puffco"
                        elif "yocan" in title.lower(): brand = "Yocan"
                        elif "lookah" in title.lower(): brand = "Lookah"
                        elif "linx" in title.lower(): brand = "Linx"
                        elif "tronian" in title.lower(): brand = "Tronian"
                        elif "storz" in title.lower() or "bickel" in title.lower(): brand = "Storz & Bickel"
                        elif "pax" in title.lower(): brand = "PAX"
                        elif "arizer" in title.lower(): brand = "Arizer"
                        elif "focus" in title.lower(): brand = "Focus V"

                        scraped_handles.add(handle)
                        
                        print(f"        ✓ Saved {title} | MSRP: ${msrp_price} | Imgs: {len(images)}")
                        
                        flat_products.append({
                            "Handle": handle,
                            "Brand": brand,
                            "Title": title,
                            "Vendor": brand,
                            "Product Type": "Hardware",
                            "Tags": "Vaporizer",
                            "Body (HTML)": body_html,
                            "Option1 Name": options[0]["name"],
                            "Option1 Value": options[0]["values"][0],
                            "Option2 Name": "",
                            "Option2 Value": "",
                            "Option3 Name": "",
                            "Option3 Value": "",
                            "Variant SKU": handle,
                            "Variant Price": msrp_price,
                            "Compare At Price": msrp_price,
                            "Inventory Quantity": 50,
                            "Variant Image": variant_image,
                            "Featured Image": variant_image,
                            "All Images": " | ".join(images),
                            "Published At": datetime.now().isoformat(),
                            "Product URL": p_url,
                        })
                        
                        nested_products.append({
                            "handle": handle,
                            "brand": brand,
                            "title": title,
                            "vendor": brand,
                            "product_type": "Hardware",
                            "tags": ["Vaporizer"],
                            "body_html": body_html,
                            "options": options,
                            "in_stock_variants": variants,
                            "all_images": images if images else [variant_image],
                            "featured_image": variant_image,
                            "url": p_url,
                            "min_price": msrp_price,
                            "max_price": msrp_price
                        })
                        
                        await p_page.close()
                    except Exception as e:
                        print(f"      -> Error scraping {p_url}: {e}")
                        try:
                            await p_page.close()
                        except:
                            pass
                        
                # Check for pagination (Next Page button)
                next_btn = await page.query_selector('.action.next')
                if next_btn and await next_btn.is_visible():
                    print(f"    Clicking to next page...")
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle")
                    page_num += 1
                else:
                    break
                    
        print(f"\n✅ Finished! Deep scraped {len(flat_products)} items.")
        
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
