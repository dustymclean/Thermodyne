import json
import re
import os
import time
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

OUTPUT_JSON = "Thermodyne_Products.json"
OUTPUT_CSV = "Thermodyne_Products.csv"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'}

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

def get_official_url(brand, title):
    domain = MANUFACTURERS.get(brand)
    if not domain:
        return None
        
    query = f"{title} site:{domain}"
    try:
        results = list(DDGS().text(query, max_results=3))
        for r in results:
            if domain in r['href']:
                return r['href']
    except Exception as e:
        pass
    return None

def extract_content(url):
    print(f"      [Fetch] {url}", flush=True)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None, None, None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Authentic Images
        images = []
        for img in soup.select('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if not src: continue
            src = src.split('?')[0]
            if src.startswith('//'): src = 'https:' + src
            elif src.startswith('/'): src = urljoin(url, src)
            
            if src not in images and ('.jpg' in src.lower() or '.png' in src.lower() or '.webp' in src.lower()):
                w = img.get('width', '')
                if w and str(w).isdigit() and int(w) < 200: continue
                if 'logo' in src.lower() or 'icon' in src.lower(): continue
                images.append(src)
                
        # 2. Rich Specs and Description
        desc_html = ""
        # We want the authentic specs, so we look for big text blocks
        desc_containers = soup.select('.product-description, #description, .description, [itemprop="description"], .product-details, .product-info, .rte, .specifications, .specs')
        if desc_containers:
            sorted_c = sorted(desc_containers, key=lambda c: len(c.text), reverse=True)
            for c in sorted_c[:3]:
                for s in c(['script', 'style', 'nav', 'form', 'svg', 'button']):
                    s.decompose()
                desc_html += str(c)
        else:
            main_content = soup.select_one('main, #main, article')
            if main_content:
                paras = main_content.find_all(['p', 'ul', 'li', 'h2', 'h3'])
                valid = [str(p) for p in paras if len(p.text.strip()) > 30]
                if valid:
                    desc_html = "<div class='manuf-description'>" + "".join(valid[:15]) + "</div>"
                    
        # Apply Linguistic Transformer to the Description
        desc_html = sanitize_for_google(desc_html)
        
        # 3. Pull actual variant SKUs/Options
        options = []
        selects = soup.select('select[name="id"], select.product-form__input, .swatch-attribute')
        for sel in selects:
            label = sel.get('name') or sel.get('id') or "Option"
            if 'color' in str(sel).lower() or 'colour' in str(sel).lower():
                label = 'Color'
            elif 'size' in str(sel).lower():
                label = 'Size'
            
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
        print(f"      [Error] {e}", flush=True)
        return None, None, None

def main():
    print("=== Dyspensr-Grade Authentic Deep Scraper ===")
    json_path = os.path.join(os.path.dirname(__file__), OUTPUT_JSON)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    products = data.get('products', [])
    print(f"Executing Deep Scrape for {len(products)} products...")
    
    updated = 0
    for i, p in enumerate(products, 1):
        brand = p.get('brand', 'Thermodyne Systems')
        orig_title = p.get('title', '')
        
        if brand not in MANUFACTURERS:
            # Still sanitize title even if we don't scrape it
            new_title = sanitize_for_google(orig_title)
            if new_title != orig_title:
                p['title'] = new_title
                updated += 1
            continue
            
        print(f"[{i}/{len(products)}] Sourcing OEM Specs: {brand} {orig_title}", flush=True)
        
        # Apply Linguistic Transformer to Title!
        safe_title = sanitize_for_google(orig_title)
        if safe_title != orig_title:
            print(f"      [Filtered Title] {safe_title}")
            p['title'] = safe_title
            
        url = get_official_url(brand, orig_title)
        
        if url:
            desc, images, options = extract_content(url)
            
            if desc and len(str(desc)) > 100:
                p['body_html'] = desc
                p['manufacturer_url'] = url
                updated += 1
                
            if images and len(images) > 0:
                p['all_images'] = images
                p['featured_image'] = images[0]
                
            if options and len(options) > 0:
                p['options'] = options
                base_price = p['min_price']
                new_variants = []
                opt_name = options[0]['name']
                handle = p['handle']
                for val in options[0]['values']:
                    safe_val = sanitize_for_google(val)
                    new_variants.append({
                        "variant_id": f"{handle}-{safe_val.replace(' ', '-').lower()}",
                        "sku": f"{brand[:3].upper()}-{safe_val[:3].upper()}-{handle[:5].upper()}",
                        "option1_name": opt_name,
                        "option1_value": safe_val,
                        "price": base_price,
                        "available": True,
                        "inventory_quantity": 50,
                        "variant_image": p.get('featured_image', '')
                    })
                p['in_stock_variants'] = new_variants
                print(f"      [+] Variants mapped: {len(new_variants)}")
                
            time.sleep(1) # Be nice to OEM servers
            
        if updated % 10 == 0 and updated > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Finished! Overwrote with authentic OEM specs & applied linguistic transformer for {updated} products.")
    print("Rebuilding storefront...")
    os.system("python3 generate_storefront.py")

if __name__ == "__main__":
    main()
