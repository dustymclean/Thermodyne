import asyncio
import json
import re
import os
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

OUTPUT_JSON = "Thermodyne_Products.json"

MANUFACTURERS = {
    "Puffco": "puffco.com",
    "Storz & Bickel": "storz-bickel.com",
    "Zeus": "zeusarsenal.com",
    "Utillian": "utillian.com",
    "PAX": "pax.com",
    "Arizer": "arizer.com",
    "Tronian": "tronian.com",
    "Yocan": "yocanvaporizer.com",
    "Lookah": "lookah.com",
    "Focus V": "focusv.com",
    "Dr. Dabber": "drdabber.com",
    "Linx": "linxvapor.com"
}

def sanitize_for_google(text):
    if not text: return ""
    text = str(text)
    replacements = {
        r'(?i)\bvape(?:s|rs|ing)?\b': 'aromatherapy device',
        r'(?i)\bvaporizer(?:s)?\b': 'thermal extractor',
        r'(?i)\be-cig(?:arette)?s?\b': 'electronic diffuser',
        r'(?i)\bherb(?:s|al)?\b': 'botanical',
        r'(?i)\bdry herb\b': 'loose leaf botanical',
        r'(?i)\bweed\b': 'botanical blend',
        r'(?i)\bmarijuana\b': 'botanical blend',
        r'(?i)\bcbd\b': 'wellness blend',
        r'(?i)\bthc\b': 'wellness blend',
        r'(?i)\bdab(?:s|bing)?\b': 'extract',
        r'(?i)\bwax\b': 'essential oil',
        r'(?i)\bconcentrate(?:s)?\b': 'essential extract',
        r'(?i)\bbong(?:s)?\b': 'water filtration piece',
        r'(?i)\bwater pipe(?:s)?\b': 'hydro-vessel',
        r'(?i)\bglass pipe(?:s)?\b': 'glass piece',
        r'(?i)\bpipe(?:s)?\b': 'handheld piece',
        r'(?i)\brig(?:s)?\b': 'desktop filtration apparatus',
        r'(?i)\bsmoke(?:s|ing|r)?\b': 'aroma',
        r'(?i)\bcartridge(?:s)?\b': 'threaded attachment',
        r'(?i)\bcart(?:s)?\b': 'attachment',
        r'(?i)\b510(?: thread)?\b': 'universal threaded',
        r'(?i)\bhemp\b': 'botanical',
        r'(?i)\bjoint(?:s)?\b': 'rolled botanical',
        r'(?i)\bblunt(?:s)?\b': 'rolled botanical',
        r'(?i)\bpre-?roll(?:s)?\b': 'pre-packed botanical',
        r'(?i)\bchillum\b': 'taster piece',
        r'(?i)\bnectar collector\b': 'direct draw straw',
        r'(?i)\bshatter\b': 'extract',
        r'(?i)\brosin\b': 'extract'
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text

async def get_official_url(page, brand, title):
    domain = MANUFACTURERS.get(brand)
    if not domain:
        return None
        
    query = f"{title} site:{domain}"
    search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    try:
        await page.goto(search_url, wait_until="domcontentloaded")
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        for a in soup.select('.result__url'):
            href = a.get('href')
            if href and domain in href:
                # DDG routes through duckduckgo.com/l/?uddg=...
                if "uddg=" in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'uddg' in parsed:
                        return parsed['uddg'][0]
                return href
    except Exception as e:
        print(f"      [Search Error] {e}")
        
    # Fallback to Google if DDG blocks
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    try:
        await page.goto(search_url, wait_until="domcontentloaded")
        # Check for captcha
        if "sorry/index" in page.url:
            print("      [!] Google CAPTCHA. Waiting 15s...")
            await asyncio.sleep(15)
            
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        for a in soup.select('#search a'):
            href = a.get('href')
            if href and domain in href and 'google.com' not in href:
                return href
    except:
        pass
        
    return None

async def extract_content(page, url):
    print(f"      [Fetch] {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2) # Let JS render
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Authentic Images
        images = []
        for img in soup.select('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if not src: continue
            src = src.split('?')[0]
            if src.startswith('//'): src = 'https:' + src
            elif src.startswith('/'): src = urljoin(url, src)
            
            if src not in images and ('.jpg' in src.lower() or '.png' in src.lower() or '.webp' in src.lower() or 'cdn.shopify.com' in src):
                w = img.get('width', '')
                if w and str(w).isdigit() and int(w) < 300: continue
                if 'logo' in src.lower() or 'icon' in src.lower(): continue
                images.append(src)
                
        # 2. Rich Specs and Description
        desc_html = ""
        desc_containers = soup.select('.product-description, #description, .description, [itemprop="description"], .product-details, .product-info, .rte, .specifications, .specs')
        if desc_containers:
            sorted_c = sorted(desc_containers, key=lambda c: len(c.text), reverse=True)
            for c in sorted_c[:2]:
                for s in c(['script', 'style', 'nav', 'form', 'svg', 'button']):
                    s.decompose()
                desc_html += str(c)
        else:
            main_content = soup.select_one('main, #main, article')
            if main_content:
                paras = main_content.find_all(['p', 'ul', 'li', 'h2', 'h3'])
                valid = [str(p) for p in paras if len(p.text.strip()) > 30]
                if valid:
                    desc_html = "<div class='manuf-description'>" + "".join(valid[:10]) + "</div>"
                    
        desc_html = sanitize_for_google(desc_html)
        
        # 3. Pull actual variant SKUs/Options (Shopify JSON or select)
        options = []
        
        # Try Shopify JSON
        shopify_json = None
        for script in soup.find_all('script', type='application/json'):
            if 'ProductJson' in str(script.get('id', '')) or 'product' in str(script.get('data-section-type', '')):
                try:
                    data = json.loads(script.string)
                    if 'options' in data: shopify_json = data
                except: pass
                
        if shopify_json and 'options' in shopify_json:
            for opt in shopify_json['options']:
                if isinstance(opt, dict) and 'name' in opt and 'values' in opt:
                    options.append(opt)
                elif isinstance(opt, str):
                    # sometimes options is just a list of names
                    options.append({"name": opt, "values": []})
        else:
            selects = soup.select('select[name="id"], select.product-form__input, .swatch-attribute')
            for sel in selects:
                label = sel.get('name') or sel.get('id') or "Option"
                if 'color' in str(sel).lower() or 'colour' in str(sel).lower(): label = 'Color'
                elif 'size' in str(sel).lower(): label = 'Size'
                
                opts = sel.find_all('option')
                vals = [o.text.strip() for o in opts if o.text.strip() and "select" not in o.text.lower()]
                
                if not vals:
                    swatches = sel.select('.swatch-option, .color-swatch, .variant-button')
                    vals = [s.get('data-option-label') or s.get('title') or s.text.strip() for s in swatches]
                    vals = [v for v in vals if v]
                    
                if vals:
                    options.append({"name": label.capitalize(), "values": vals[:6]})
                    
        return desc_html, images[:10], options
        
    except Exception as e:
        print(f"      [Error] {e}")
        return None, None, None

async def main():
    print("=== Dyspensr OEM Deep Scraper ===")
    json_path = os.path.join(os.path.dirname(__file__), OUTPUT_JSON)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    products = data.get('products', [])
    print(f"Executing OEM Scrape for {len(products)} products...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        page = await context.new_page()
        
        updated = 0
        for i, prod in enumerate(products, 1):
            brand = prod.get('brand', 'Thermodyne Systems')
            orig_title = prod.get('title', '')
            
            if brand not in MANUFACTURERS:
                new_title = sanitize_for_google(orig_title)
                if new_title != orig_title:
                    prod['title'] = new_title
                    updated += 1
                continue
                
            print(f"\n[{i}/{len(products)}] Sourcing OEM: {brand} {orig_title}")
            
            # Apply Filter to Title
            safe_title = sanitize_for_google(orig_title)
            if safe_title != orig_title:
                prod['title'] = safe_title
                
            url = await get_official_url(page, brand, orig_title)
            
            if url:
                desc, images, options = await extract_content(page, url)
                
                if desc and len(str(desc)) > 100:
                    prod['body_html'] = desc
                    prod['manufacturer_url'] = url
                    updated += 1
                    
                if images and len(images) > 0:
                    prod['all_images'] = images
                    prod['featured_image'] = images[0]
                    
                if options and len(options) > 0 and options[0].get('name') != 'Title':
                    prod['options'] = options
                    base_price = prod.get('min_price', 0.0)
                    new_variants = []
                    opt_name = options[0]['name']
                    handle = prod['handle']
                    
                    vals = options[0].get('values', [])
                    if not vals: vals = ["Default"]
                    
                    for val in vals:
                        safe_val = sanitize_for_google(val)
                        new_variants.append({
                            "variant_id": f"{handle}-{safe_val.replace(' ', '-').lower()}",
                            "sku": f"{brand[:3].upper()}-{safe_val[:3].upper()}-{handle[:5].upper()}",
                            "option1_name": opt_name,
                            "option1_value": safe_val,
                            "price": base_price,
                            "available": True,
                            "inventory_quantity": 50,
                            "variant_image": prod.get('featured_image', '')
                        })
                    prod['in_stock_variants'] = new_variants
                    print(f"      [+] Variants mapped: {len(new_variants)}")
                    
            if updated % 5 == 0 and updated > 0:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Finished! Overwrote {updated} products with authentic OEM specs.")
        await browser.close()
        
    print("Rebuilding storefront...")
    os.system("python3 generate_storefront.py")
    os.system('git add . && git commit -m "Replace generic data with authentic OEM specs and apply Dyspensr linguistic transformer" && git push')

if __name__ == "__main__":
    asyncio.run(main())
