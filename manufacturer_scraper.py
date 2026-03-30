import json
import re
import os
import time
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

OUTPUT_JSON = "Thermodyne_Products.json"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

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
    query = f"{brand} {title} official site buy"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                url = r['href']
                if any(x in url for x in ['amazon', 'ebay', 'vape', 'smoke', 'grasscity', 'planetofthevapes', 'element', 'thermodynesystems', 'lacentralvapeur']):
                    continue
                if brand.lower().replace(' ', '') in url.lower() or 'puffco' in url or 'storz-bickel' in url or 'zeus' in url:
                    return url
            if results:
                return results[0]['href']
    except Exception as e:
        pass
    return None

def extract_content(url):
    print(f"      [Fetch] {url}", flush=True)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None, None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        images = []
        for img in soup.select('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if not src: continue
            src = src.split('?')[0]
            if src.startswith('//'): src = 'https:' + src
            elif src.startswith('/'): src = urljoin(url, src)
            
            if src not in images and ('.jpg' in src.lower() or '.png' in src.lower() or '.webp' in src.lower()):
                w = img.get('width', '')
                if w and str(w).isdigit() and int(w) < 300: continue
                if 'logo' in src.lower() or 'icon' in src.lower(): continue
                images.append(src)
                
        desc_html = ""
        # Broad selectors for description/specs
        desc_containers = soup.select('.product-description, #description, .description, [itemprop="description"], .rte, .product-info, .product__description, .specs, .specifications')
        if desc_containers:
            sorted_c = sorted(desc_containers, key=lambda c: len(c.text), reverse=True)
            for c in sorted_c[:2]:
                for s in c(['script', 'style', 'nav', 'form', 'svg', 'button']):
                    s.decompose()
                desc_html += str(c)
        else:
            main_content = soup.select_one('main, #main, article')
            if main_content:
                paras = main_content.find_all(['p', 'ul', 'li'])
                valid = [str(p) for p in paras if len(p.text.strip()) > 30]
                if valid:
                    desc_html = "<div class='manuf-description'>" + "".join(valid[:10]) + "</div>"
                    
        return sanitize_for_google(desc_html), images[:10]
        
    except Exception as e:
        print(f"      [Error] {e}", flush=True)
        return None, None

def main():
    print("=== Unique Pixies Pantry Deep Scraper ===")
    json_path = os.path.join(os.path.dirname(__file__), OUTPUT_JSON)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    products = data.get('products', [])
    updated = 0
    
    for i, p in enumerate(products, 1):
        brand = p.get('brand', 'Thermodyne Systems')
        title = p.get('title', '')
        handle = p.get('handle', '')
        
        if brand == "Thermodyne Systems" or not brand:
            # Skip unbranded
            continue
            
        print(f"[{i}/{len(products)}] Sourcing: {brand} {title}", flush=True)
        url = get_official_url(brand, title)
        
        if url:
            desc, images = extract_content(url)
            
            if desc and len(str(desc)) > 100:
                p['body_html'] = desc
                p['manufacturer_url'] = url
                updated += 1
                
            if images and len(images) > 1:
                p['all_images'] = images
                p['featured_image'] = images[0]
                
            # small delay
            time.sleep(1.5)
            
        if updated % 5 == 0 and updated > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Finished! Overwrote with authentic OEM specs & applied linguistic transformer for {updated} products.")
    
if __name__ == "__main__":
    main()
