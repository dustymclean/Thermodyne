import json
import os
import re
import shutil

import json
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
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace('"', '&quot;').replace("'", "&#39;")
    return text

def build_json_ld(product, url_base):
    safe_title = sanitize_for_google(product['title'])
    safe_desc = sanitize_for_google(product.get('body_html', 'Premium device selected for material quality and performance.'))
    img = product.get('featured_image') or (product.get('all_images')[0] if product.get('all_images') else '')
    price = f"{product.get('min_price', 0):.2f}"
    brand = sanitize_for_google(product.get('brand', 'Premium'))
    
    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": safe_title,
        "image": img,
        "description": safe_desc[:4000],
        "brand": {
            "@type": "Brand",
            "name": brand
        },
        "offers": {
            "@type": "Offer",
            "url": f"{url_base}/#",
            "priceCurrency": "USD",
            "price": price,
            "availability": "https://schema.org/InStock",
            "itemCondition": "https://schema.org/NewCondition"
        }
    }
    if product.get('in_stock_variants') and len(product['in_stock_variants']) > 0:
        offers = []
        for v in product['in_stock_variants']:
            v_price = f"{float(v.get('price', 0)):.2f}"
            offers.append({
                "@type": "Offer",
                "name": sanitize_for_google(f"{product['title']} - {v.get('option1_value', '')}"),
                "priceCurrency": "USD",
                "price": v_price,
                "availability": "https://schema.org/InStock",
                "url": f"{url_base}/#"
            })
        schema["offers"] = offers
    return f'<script type="application/ld+json">{json.dumps(schema)}</script>'

def build_sitemap(url_base, pages):
    import datetime
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        xml += f'  <url>\n    <loc>{url_base}/{page}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
    xml += '</urlset>'
    return xml


JSON_PATH = os.path.expanduser("~/Desktop/Thermodyne_Catalog/Thermodyne_Products.json")
OUTPUT_DIR = os.path.expanduser("~/Desktop/Thermodyne_Catalog")

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def ensure_dirs():
    os.makedirs(os.path.join(OUTPUT_DIR, "css"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "js"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "categories"), exist_ok=True)

def generate_site():
    ensure_dirs()
    pass
    pass
    if not os.path.exists(JSON_PATH):
        print(f"File not found: {JSON_PATH}")
        return
        
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = data.get("products", [])
    
    # Organize products
    brands = {"Thermodyne Systems": [], "Accessories": []}
    categories = {}
    
    for p in products:
        b = p.get("brand")
        if b in brands:
            brands[b].append(p)
            
        ptype = p.get("product_type") or "Accessories"
        if b not in categories:
            categories[b] = {}
        if ptype not in categories[b]:
            categories[b][ptype] = []
        categories[b][ptype].append(p)
        
    print(f"Loaded {len(products)} products.")
    
    # CSS
    css_content = """
    :root { --primary: #111; --gold: #d4af37; --bg: #fff; --muted: #888; --border: #eaeaea; --sidebar-w: 260px; }
    body { font-family: 'Helvetica Neue', Arial, sans-serif; background: var(--bg); color: var(--primary); margin: 0; padding: 0; }
    .sidebar { position: fixed; width: var(--sidebar-w); left: 0; top: 0; bottom: 0; background: #fafafa; border-right: 1px solid var(--border); overflow-y: auto; padding: 30px 20px; box-sizing: border-box; }
    .sidebar-logo { font-size: 22px; font-weight: 800; text-decoration: none; color: #000; display: block; margin-bottom: 5px; }
    .sidebar-tagline { font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin-bottom: 30px; }
    .sidebar-section { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin: 20px 0 10px; color: var(--muted); }
    .sidebar-link { display: block; padding: 6px 0; color: #333; text-decoration: none; font-size: 14px; font-weight: 500; }
    .sidebar-link:hover, .sidebar-link.active { color: var(--gold); }
    .sidebar-link.child { padding-left: 15px; font-size: 13px; color: #555; }
    .sidebar-footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); }
    
    .sidebar-community { margin-top: 30px; padding: 15px; background: #111; color: #fff; border-radius: 8px; }
    .sidebar-community h4 { margin: 0 0 10px; font-size: 12px; color: var(--gold); text-transform: uppercase; }
    .sidebar-community p { font-size: 11px; line-height: 1.4; margin: 0 0 10px; color: #ccc; }
    .sidebar-community a.link { color: #fff; font-size: 11px; text-decoration: underline; display: block; margin-bottom: 10px; }
    
    .main-wrapper { margin-left: var(--sidebar-w); min-height: 100vh; display: flex; flex-direction: column; }
    .main-content { padding: 40px 50px; flex: 1; }
    
    .page-title { font-size: 32px; font-weight: 800; margin: 0 0 10px; }
    .page-subtitle { color: var(--muted); margin-bottom: 40px; }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; }
    .card { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: #fff; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; cursor: pointer; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); border-color: #ddd; }
    .card-img { width: 100%; height: 280px; object-fit: contain; padding: 20px; box-sizing: border-box; background: #fdfdfd; border-bottom: 1px solid var(--border); }
    .card-body { padding: 20px; flex: 1; display: flex; flex-direction: column; }
    .card-brand { font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin-bottom: 5px; }
    .card-title { font-size: 16px; font-weight: 600; margin: 0 0 10px; flex: 1; line-height: 1.4; }
    .card-price { font-size: 18px; font-weight: 700; color: var(--gold); margin-bottom: 15px; }
    
    .btn { display: inline-block; background: #000; color: #fff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 700; text-transform: uppercase; text-align: center; border: none; cursor: pointer; transition: background 0.2s; }
    .btn:hover { background: var(--gold); color: #000; }
    .btn-outline { background: transparent; color: #000; border: 1px solid #000; }
    .btn-outline:hover { background: #000; color: #fff; }
    .btn-danger { background: #ff4444; color: #fff; }
    .btn-danger:hover { background: #cc0000; }
    
    /* Input box for forms */
    .input-box { margin-bottom: 15px; text-align: left; }
    .input-box label { display: block; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 6px; }
    .input-box input { width: 100%; border: 1px solid var(--border); padding: 10px; border-radius: 6px; box-sizing: border-box; font-family: inherit; }
    
    /* Modals & Overlays */
    .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
    .modal-overlay.active { display: flex; }
    .modal { background: #fff; width: 90%; max-width: 1000px; max-height: 90vh; border-radius: 16px; display: flex; overflow: hidden; position: relative; box-shadow: 0 20px 50px rgba(0,0,0,0.2); }
    .modal-close { position: absolute; top: 20px; right: 20px; background: #f0f0f0; border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 20px; cursor: pointer; z-index: 10; display: flex; align-items: center; justify-content: center; }
    .modal-close:hover { background: #e0e0e0; }
    
    /* Product Modal */
    .modal-left { width: 50%; background: #fdfdfd; padding: 40px; border-right: 1px solid var(--border); position: relative; }
    .modal-main-img { width: 100%; height: 400px; object-fit: contain; margin-bottom: 20px; }
    .modal-right { width: 50%; padding: 40px; overflow-y: auto; max-height: 90vh; }
    .modal-brand { font-size: 12px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin-bottom: 5px; }
    .modal-title { font-size: 28px; font-weight: 800; margin: 0 0 15px; }
    .modal-price { font-size: 24px; font-weight: 700; color: var(--gold); margin-bottom: 25px; }
    .modal-desc { font-size: 15px; line-height: 1.6; color: #444; margin-bottom: 30px; }
    .modal-desc p { margin-top: 0; }
    .variant-label { font-size: 12px; font-weight: 800; text-transform: uppercase; margin-bottom: 10px; display: block; }
    .swatch-group { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; }
    .swatch { border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; background: #fff; transition: all 0.2s; }
    .swatch:hover { border-color: #aaa; }
    .swatch.selected { border-color: #000; background: #000; color: #fff; }
    .modal-buy-btn { width: 100%; padding: 15px; font-size: 15px; border-radius: 8px; }
    
    
    /* Footer */
    .site-footer { background-color: #000; color: #fff; padding: 80px 50px 30px; margin-top: 80px; font-family: 'Helvetica Neue', Arial, sans-serif; }
    .footer-content { display: grid; grid-template-columns: 2fr 1fr 1fr 1.5fr; gap: 50px; max-width: 1400px; margin: 0 auto; border-bottom: 1px solid #222; padding-bottom: 60px; }
    .footer-col h3 { color: #fff; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin: 0 0 25px; }
    .footer-col p { color: #888; font-size: 13px; line-height: 1.8; margin: 0 0 10px; }
    .footer-col ul { list-style: none; padding: 0; margin: 0; }
    .footer-col ul li { margin-bottom: 15px; }
    .footer-col ul li a { color: #888; text-decoration: none; font-size: 13px; transition: 0.3s; }
    .footer-col ul li a:hover { color: var(--gold); }
    .newsletter-form { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }
    .newsletter-form input { padding: 15px; background: #111; border: 1px solid #333; color: #fff; border-radius: 6px; outline: none; font-family: inherit; }
    .newsletter-form input:focus { border-color: var(--gold); }
    .newsletter-form button { padding: 15px; background: var(--gold); color: #000; border: none; border-radius: 6px; font-weight: 800; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; transition: 0.3s; font-family: inherit; }
    .newsletter-form button:hover { background: #fff; }
    .footer-bottom { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 30px auto 0; font-size: 11px; color: #666; letter-spacing: 1px; text-transform: uppercase; font-weight: 800; }
    .footer-socials { display: flex; gap: 20px; }
    .footer-socials a { color: #888; text-decoration: none; transition: 0.3s; }
    .footer-socials a:hover { color: var(--gold); }
    
    @media (max-width: 992px) {
        .site-footer { padding: 60px 30px 30px; }
        .footer-content { grid-template-columns: 1fr 1fr; gap: 40px; }
        .footer-bottom { flex-direction: column; gap: 20px; text-align: center; }
    }
    @media (max-width: 600px) {
        .footer-content { grid-template-columns: 1fr; gap: 40px; }
    }

    
    /* Age Gate */

    /* Age Gate */
    .age-gate-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: #000; z-index: 99999; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .age-gate-box { max-width: 480px; width: 100%; text-align: center; }
    .age-gate-logo { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: -1px; margin-bottom: 8px; }
    .age-gate-logo span { color: var(--gold); }
    .age-gate-tagline { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #888; margin-bottom: 50px; }
    .age-gate-heading { font-size: 13px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; color: #888; margin-bottom: 15px; }
    .age-gate-title { font-size: 38px; font-weight: 900; color: #fff; margin: 0 0 20px; line-height: 1.1; }
    .age-gate-subtitle { font-size: 15px; color: #888; line-height: 1.6; margin-bottom: 40px; }
    .age-gate-buttons { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; }
    .age-gate-yes { background: var(--gold); color: #000; border: none; padding: 16px 40px; font-size: 14px; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; border-radius: 8px; cursor: pointer; transition: 0.2s; }
    .age-gate-yes:hover { background: #fff; }
    .age-gate-no { background: transparent; color: #555; border: 1px solid #333; padding: 16px 40px; font-size: 14px; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; border-radius: 8px; cursor: pointer; transition: 0.2s; }
    .age-gate-no:hover { border-color: #555; color: #888; }
    .age-gate-disclaimer { font-size: 11px; color: #444; margin-top: 30px; line-height: 1.6; }

    /* Banner */
    .banner { background: #000; color: #fff; text-align: center; padding: 10px; font-size: 11px; font-weight: 900; letter-spacing: 2px; position: fixed; top: 0; left: 0; right: 0; z-index: 1000; text-transform: uppercase; border-bottom: 2px solid var(--gold); }
    .banner a { color: var(--gold); text-decoration: none; transition: 0.3s; }
    .banner a:hover { color: #fff; }
    .sidebar { top: 36px; /* Offset for banner */ }
    .main-wrapper { margin-top: 36px; /* Offset for banner */ }
    @media (max-width: 900px) { .sidebar { top: 0; } }

    /* Floating Cart */
    .cart-float { position: fixed; bottom: 30px; right: 30px; background: #000; color: #fff; width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; cursor: pointer; box-shadow: 0 10px 25px rgba(0,0,0,0.3); z-index: 900; transition: transform 0.2s; border: 2px solid var(--gold); }
    .cart-float:hover { transform: scale(1.05); }
    .cart-badge { position: absolute; top: -5px; right: -5px; background: red; color: white; font-size: 13px; font-weight: bold; width: 24px; height: 24px; border-radius: 50%; display: none; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    
    /* Cart Modal specific */
    .cart-modal { max-width: 600px; width: 100%; flex-direction: column; padding: 30px; }
    .cart-items-container { overflow-y: auto; max-height: 50vh; margin-top: 20px; margin-bottom: 20px; padding-right: 10px; }
    .cart-item { display: flex; align-items: center; border-bottom: 1px solid var(--border); padding: 15px 0; }
    .cart-item-img { width: 60px; height: 60px; object-fit: contain; background: #fdfdfd; border: 1px solid var(--border); border-radius: 6px; margin-right: 15px; }
    .cart-item-info { flex: 1; }
    .cart-item-title { font-size: 14px; font-weight: bold; margin: 0 0 5px; }
    .cart-item-variant { font-size: 12px; color: var(--muted); margin: 0 0 5px; }
    .cart-item-price { font-size: 14px; font-weight: bold; color: var(--gold); }
    .cart-item-controls { display: flex; align-items: center; gap: 10px; }
    .qty-btn { background: #eee; border: none; width: 28px; height: 28px; border-radius: 4px; cursor: pointer; font-weight: bold; display:flex; align-items:center; justify-content:center; }
    .qty-btn:hover { background: #ddd; }
    .remove-btn { color: red; background: none; border: none; cursor: pointer; font-size: 12px; text-decoration: underline; padding: 5px; }
    .cart-total-row { display: flex; justify-content: space-between; align-items: center; font-size: 20px; font-weight: bold; margin-bottom: 20px; border-top: 2px solid #000; padding-top: 20px; }
    
    @media (max-width: 900px) {
        .sidebar { transform: translateX(-100%); z-index: 100; transition: transform 0.3s; }
        .main-wrapper { margin-left: 0; }
        .modal { flex-direction: column; overflow-y: auto; }
        .modal-left, .modal-right { width: 100%; }
        .modal-left { border-right: none; border-bottom: 1px solid var(--border); padding: 20px; }
        .modal-main-img { height: 300px; }
        .modal-right { max-height: none; padding: 20px; }
        .cart-float { bottom: 20px; right: 20px; }
    }
    """
    with open(os.path.join(OUTPUT_DIR, "css", "style.css"), "w") as f:
        f.write(css_content)
        


    def get_sidebar_html(depth=""):
        html = f"""
        <aside class="sidebar">
            <a href="{depth}index.html" class="sidebar-logo">Pixie's Pantry</a>
            <div class="sidebar-tagline">Medical-Grade Vaporizers</div>
            
            <a href="{depth}index.html" class="sidebar-link">All Products</a>
        """
        
        for brand in ["Thermodyne Systems", "Accessories"]:
            if brand not in categories: continue
            html += f"""
            <div class="sidebar-section">{brand}</div>
            <a href="{depth}{brand.lower().split()[0]}.html" class="sidebar-link">Shop All {brand}</a>
            """
            for cat in sorted(categories.get(brand, {}).keys()):
                if not cat: continue
                html += f'<a href="{depth}categories/{slugify(brand)}-{slugify(cat)}.html" class="sidebar-link child">{cat}</a>'
                
        html += f"""
            <div class="sidebar-community">
                <h4>Power in Numbers</h4>
                <p>Joining our Discord helps us demonstrate community engagement to distributors, unlocking cheaper wholesale prices that we pass directly to you.</p>
                <a href="{depth}community.html" class="link">Learn more</a>
                <a href="https://discord.gg/dm8deA2u" target="_blank" class="btn" style="background: var(--gold); color: #000; padding: 8px; font-size: 11px; width: 100%; box-sizing: border-box;">Join the Mission</a>
            </div>

            <div class="sidebar-footer">
                <a href="{depth}login.html" class="sidebar-link">Log In</a>
                <a href="{depth}signup.html" class="sidebar-link">Sign Up</a>
            </div>
        </aside>
        """
        return html

    def get_modal_html():
        return """
        <!-- Global Cart Button -->
        <div class="cart-float" id="cart-float" title="View Cart">
            🛒<div class="cart-badge" id="cart-badge">0</div>
        </div>
        
        <!-- Cart Slide-out / Modal -->
        <div class="modal-overlay" id="cart-overlay">
            <div class="modal cart-modal">
                <button class="modal-close" id="cart-close">&times;</button>
                <h2 class="modal-title" style="margin-bottom: 5px;">Your Shopping Cart</h2>
                <div class="cart-items-container" id="cart-items-container">
                    <!-- JS injects cart items here -->
                </div>
                <div class="cart-total-row">
                    <span>Total</span>
                    <span id="cart-total">$0.00</span>
                </div>
                <button class="btn" id="proceed-checkout-btn" style="width: 100%; padding: 15px; font-size: 16px;">Proceed to Checkout</button>
            </div>
        </div>

        <!-- Product Modal -->
        <div class="modal-overlay" id="modal-overlay">
            <div class="modal">
                <button class="modal-close" id="modal-close">&times;</button>
                <div class="modal-left">
                    <img src="" alt="Product" class="modal-main-img" id="m-img">
                </div>
                <div class="modal-right">
                    <div class="modal-brand" id="m-brand">Brand</div>
                    <h2 class="modal-title" id="m-title">Product Name</h2>
                    <div class="modal-price" id="m-price">$0.00</div>
                    <div class="modal-desc" id="m-desc"></div>
                    
                    <div class="variant-label" id="v-label">Options</div>
                    <div class="swatch-group" id="swatches"></div>
                    
                    <button class="btn modal-buy-btn" id="add-to-cart-btn">Add to Cart</button>
                </div>
            </div>
        </div>
        
        <!-- Checkout Modal -->
        <div class="modal-overlay" id="checkout-overlay">
            <div class="modal" style="max-width: 500px; flex-direction: column; padding: 40px;">
                <button class="modal-close" id="checkout-close">&times;</button>
                <h2 class="modal-title" style="margin-bottom: 5px;">Secure Checkout</h2>
                <div id="checkout-item-desc" style="margin-bottom: 25px; color: #444;"></div>
                <form id="checkout-form">
                    <div class="input-box"><label>Full Name *</label><input type="text" id="c_name" required></div>
                    <div class="input-box"><label>Email Address *</label><input type="email" id="c_email" required></div>
                    <div style="display: flex; gap: 15px;">
                        <div class="input-box" style="flex: 1;"><label>Phone Number *</label><input type="tel" id="c_phone" required></div>
                        <div class="input-box" style="flex: 1;"><label>Discord Username (Optional)</label><input type="text" id="c_discord" placeholder="e.g. user#1234"></div>
                    </div>
                    <div class="input-box">
                        <label>Shipping Address *</label>
                        <input type="text" id="c_address" placeholder="Street Address" required style="margin-bottom: 10px;">
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="c_city" placeholder="City" required style="flex: 2;">
                            <input type="text" id="c_state" placeholder="State" required style="flex: 1;">
                            <input type="text" id="c_zip" placeholder="ZIP" required style="flex: 1;">
                        </div>
                    </div>
                    <button type="submit" class="btn" style="width: 100%; margin-top: 15px; font-size: 15px; padding: 15px;" id="c_submit">Submit Order</button>
                </form>
                <div id="checkout-feedback" style="margin-top: 15px; font-size: 14px; font-weight: bold; text-align: center; display: none;"></div>
            </div>
        </div>
        """

    def render_page(filename, title, subtitle, product_list, depth=""):
        sidebar = get_sidebar_html(depth)
        modal = get_modal_html()
        
        # Inject data for JS
        products_dict = {p["handle"]: p for p in product_list}
        json_data = json.dumps(products_dict)
        
        grid_html = '<div class="grid" id="product-grid"></div>'
        if not product_list:
            grid_html = '<p>No products found in this category.</p>'
            
        
        # Build JSON-LD
        json_ld_content_for_file = ""
        for p in product_list:
            json_ld_content_for_file += build_json_ld(p, "https://thermodyne.pixiespantryshop.com")
        
        # Write JSON-LD to a separate file
        if json_ld_content_for_file:
            with open(os.path.join(OUTPUT_DIR, "js", "index_ld_json.js"), "w", encoding="utf-8") as f:
                f.write(json_ld_content_for_file)
            json_ld_scripts_tag = f'<script src="{depth}js/index_ld_json.js"></script>'
        else:
            json_ld_scripts_tag = ''

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} | Pixie's Pantry</title>
    <!-- Google Shopping / Merchant Center SEO -->
    <meta name="description" content="{sanitize_for_google(subtitle)}">
    <meta property="og:title" content="{sanitize_for_google(title)} | Pixie's Pantry">
    <meta property="og:description" content="{sanitize_for_google(subtitle)}">
    <meta property="og:type" content="website">
    <link rel="canonical" href="https://thermodyne.pixiespantryshop.com/{filename}">
    {json_ld_scripts_tag}
    <link rel="stylesheet" href="{depth}css/style.css">
</head>
<body>
    <div class="banner">JOIN THE DISCORD FOR EXCLUSIVE WHOLESALE PRICING &nbsp;·&nbsp; <a href="https://discord.gg/dm8deA2u" target="_blank">DISCORD.GG/DM8DEa2U</a></div>
    {sidebar}
    <div class="main-wrapper">
        <main class="main-content">
            <h1 class="page-title">{title}</h1>
            <div class="page-subtitle">{subtitle}</div>
            <div class="sort-filter-controls" style="margin-bottom: 25px; text-align: right;">
                
                <select id="filter-brand" style="padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; margin-right: 10px; font-size: 14px;">
                    <option value="all">All Brands</option>
                    <option value="Accessories">Portable Vaporizers</option>
                    <option value="Thermodyne Systems">Desktop Vaporizers</option>
                </select>
                <select id="filter-category" style="padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; margin-right: 10px; font-size: 14px;">
                    <option value="all">All Categories</option>
                </select>
                <select id="sort-by" style="padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; margin-right: 10px; font-size: 14px;">
                    <option value="default">Sort By</option>
                    <option value="brand-asc">Brand (A-Z)</option>
                    <option value="category-asc">Category (A-Z)</option>
                    <option value="price-asc">Price (Low to High)</option>
                </select>
            </div>
            {grid_html}
        </main>
        
        <footer class="site-footer">
            <div class="footer-content">
                <div class="footer-col">
                    <h3>Pixie's Pantry</h3>
                    <p style="max-width: 300px;">Curating the absolute highest tier of vaporization and glass hardware. Direct wholesale access, vetted specifically for the community. Elevate your ritual.</p>
                </div>
                <div class="footer-col">
                    <h3>Explore</h3>
                    <ul>
                        <li><a href="{depth}index.html">Master Catalog</a></li>
                        <li><a href="javascript:void(0)" onclick="document.getElementById('cart-float').click()">View Cart</a></li>
                        <li><a href="{depth}community.html">Community Pricing</a></li>
                        <li><a href="https://dyspensr.com" target="_blank">Dyspensr Network</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Client Services</h3>
                    <ul>
                        <li><a href="https://discord.gg/dm8deA2u" target="_blank">Discord Support (Fastest)</a></li>
                        <li><a href="mailto:admin@pixies-pantry.com">Email Concierge</a></li>
                        <li><a href="{depth}shipping.html">Shipping & Delivery</a></li>
                        <li><a href="{depth}refunds.html">Returns & Exchanges</a></li>
                        <li><a href="{depth}privacy.html">Privacy & Terms</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Stay Exquisite</h3>
                    <p>Join the inner circle for exclusive drops and wholesale restocks.</p>
                    <form class="newsletter-form" action="https://formspree.io/f/xeoqkzdj" method="POST">
                        <input type="email" name="Newsletter Email" placeholder="Enter your email address" required>
                        <button type="submit">Subscribe</button>
                    </form>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 PIXIE'S PANTRY. ALL RIGHTS RESERVED.</p>
                <div class="footer-socials">
                    <a href="https://discord.gg/dm8deA2u" target="_blank">Discord</a>
                    <a href="#">Instagram</a>
                    <a href="#">Twitter</a>
                </div>
            </div>
        </footer>

    </div>
    {modal}
    <script>window.productsData = {json_data};</script>
    <script src="{depth}js/main.js"></script>
</body>
</html>"""
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            f.write(html)
            
    def render_community_page():
        sidebar = get_sidebar_html()
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Community Power & Pricing | Pixie's Pantry</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="banner">JOIN THE DISCORD FOR EXCLUSIVE WHOLESALE PRICING &nbsp;·&nbsp; <a href="https://discord.gg/dm8deA2u" target="_blank">DISCORD.GG/DM8DEa2U</a></div>
    {sidebar}
    <div class="main-wrapper">
        <main class="main-content" style="max-width: 800px;">
            <h1 class="page-title">Community Power & Pricing</h1>
            <div class="page-subtitle" style="color: var(--gold); font-weight: bold;">Unlock exclusive wholesale rates through community engagement.</div>
            
            <div style="font-size: 16px; line-height: 1.8; color: #333;">
                <p>At Pixie's Pantry, we believe in radical transparency. Here is the secret to the retail industry: <strong>Volume and community engagement dictate wholesale pricing.</strong></p>
                <p>When we approach distributors and manufacturers, they want to know one thing: do we have an active, engaged audience? The larger and more active our Discord community is, the more leverage we have to negotiate aggressive discounts on hardware.</p>
                <h3 style="margin-top: 30px; font-weight: 800;">How It Works</h3>
                <ul style="padding-left: 20px;">
                    <li style="margin-bottom: 10px;"><strong>Join the Discord:</strong> Every member adds weight to our bargaining power.</li>
                    <li style="margin-bottom: 10px;"><strong>We Negotiate:</strong> We show distributors our engagement metrics.</li>
                    <li style="margin-bottom: 10px;"><strong>You Save:</strong> The discounts we secure are passed directly to you on the storefront.</li>
                </ul>
                <p>By simply joining the Discord, you are actively helping lower the cost of premium Thermodyne Systems and Accessories hardware for yourself and everyone else.</p>
                <div style="margin-top: 40px; padding: 30px; background: #fafafa; border: 1px solid var(--border); border-radius: 12px; text-align: center;">
                    <h2 style="margin-top: 0;">Ready to lower prices?</h2>
                    <a href="https://discord.gg/dm8deA2u" target="_blank" class="btn" style="background: var(--gold); color: #000; font-size: 16px; padding: 15px 30px; margin-top: 15px;">Join the Mission on Discord</a>
                </div>
            </div>
        </main>
        
        <footer class="site-footer">
            <div class="footer-content">
                <div class="footer-col">
                    <h3>Pixie's Pantry</h3>
                    <p style="max-width: 300px;">Curating the absolute highest tier of vaporization and glass hardware. Direct wholesale access, vetted specifically for the community. Elevate your ritual.</p>
                </div>
                <div class="footer-col">
                    <h3>Explore</h3>
                    <ul>
                        <li><a href="index.html">Master Catalog</a></li>
                        <li><a href="javascript:void(0)" onclick="document.getElementById('cart-float').click()">View Cart</a></li>
                        <li><a href="community.html">Community Pricing</a></li>
                        <li><a href="https://dyspensr.com" target="_blank">Dyspensr Network</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Client Services</h3>
                    <ul>
                        <li><a href="https://discord.gg/dm8deA2u" target="_blank">Discord Support (Fastest)</a></li>
                        <li><a href="mailto:admin@pixies-pantry.com">Email Concierge</a></li>
                        <li><a href="shipping.html">Shipping & Delivery</a></li>
                        <li><a href="refunds.html">Returns & Exchanges</a></li>
                        <li><a href="privacy.html">Privacy & Terms</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Stay Exquisite</h3>
                    <p>Join the inner circle for exclusive drops and wholesale restocks.</p>
                    <form class="newsletter-form" action="https://formspree.io/f/xeoqkzdj" method="POST">
                        <input type="email" name="Newsletter Email" placeholder="Enter your email address" required>
                        <button type="submit">Subscribe</button>
                    </form>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 PIXIE'S PANTRY. ALL RIGHTS RESERVED.</p>
                <div class="footer-socials">
                    <a href="https://discord.gg/dm8deA2u" target="_blank">Discord</a>
                    <a href="#">Instagram</a>
                    <a href="#">Twitter</a>
                </div>
            </div>
        </footer>

    </div>
</body>
</html>"""
        with open(os.path.join(OUTPUT_DIR, "community.html"), "w", encoding="utf-8") as f:
            f.write(html)

    # Write pages
    print("Generating pages...")
    render_page("index.html", "Shop All", "Discover premium devices from Thermodyne Systems and Accessories.", products)
    render_page("thermodyne.html", "Thermodyne Systems", "Advanced vaporizers and accessories.", brands.get("Thermodyne Systems", []))
    render_page("accessories.html", "Accessories", "Silicone pipes and rigs.", brands.get("Accessories", []))
    
    for brand, cats in categories.items():
        for cat, prods in cats.items():
            if not cat: continue
            render_page(f"categories/{slugify(brand)}-{slugify(cat)}.html", 
                        f"{brand} {cat}", f"Shop all {brand} {cat}.", prods, depth="../")
                        
    # Login / Signup stubs
    auth_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Account | Pixie's Pantry</title>
    <link rel="stylesheet" href="css/style.css">
    <style>
        .auth-container { max-width: 400px; margin: 80px auto; text-align: center; }
        .input-box { margin-bottom: 20px; text-align: left; }
        .input-box label { display: block; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
        .input-box input { width: 100%; border: 1px solid var(--border); padding: 12px; border-radius: 8px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="banner">JOIN THE DISCORD FOR EXCLUSIVE WHOLESALE PRICING &nbsp;·&nbsp; <a href="https://discord.gg/dm8deA2u" target="_blank">DISCORD.GG/DM8DEa2U</a></div>
    {sidebar}
    <div class="main-wrapper">
        <main class="main-content">
            <div class="auth-container">
                <h1 class="page-title">{title}</h1>
                <p class="page-subtitle">FormPress Backend Required</p>
                <div class="input-box"><label>Email</label><input type="email"></div>
                <div class="input-box"><label>Password</label><input type="password"></div>
                <button class="btn" style="width:100%">{title}</button>
            </div>
        </main>
        
        <footer class="site-footer">
            <div class="footer-content">
                <div class="footer-col">
                    <h3>Pixie's Pantry</h3>
                    <p style="max-width: 300px;">Curating the absolute highest tier of vaporization and glass hardware. Direct wholesale access, vetted specifically for the community. Elevate your ritual.</p>
                </div>
                <div class="footer-col">
                    <h3>Explore</h3>
                    <ul>
                        <li><a href="index.html">Master Catalog</a></li>
                        <li><a href="javascript:void(0)" onclick="document.getElementById('cart-float').click()">View Cart</a></li>
                        <li><a href="community.html">Community Pricing</a></li>
                        <li><a href="https://dyspensr.com" target="_blank">Dyspensr Network</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Client Services</h3>
                    <ul>
                        <li><a href="https://discord.gg/dm8deA2u" target="_blank">Discord Support (Fastest)</a></li>
                        <li><a href="mailto:admin@pixies-pantry.com">Email Concierge</a></li>
                        <li><a href="shipping.html">Shipping & Delivery</a></li>
                        <li><a href="refunds.html">Returns & Exchanges</a></li>
                        <li><a href="privacy.html">Privacy & Terms</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Stay Exquisite</h3>
                    <p>Join the inner circle for exclusive drops and wholesale restocks.</p>
                    <form class="newsletter-form" action="https://formspree.io/f/xeoqkzdj" method="POST">
                        <input type="email" name="Newsletter Email" placeholder="Enter your email address" required>
                        <button type="submit">Subscribe</button>
                    </form>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 PIXIE'S PANTRY. ALL RIGHTS RESERVED.</p>
                <div class="footer-socials">
                    <a href="https://discord.gg/dm8deA2u" target="_blank">Discord</a>
                    <a href="#">Instagram</a>
                    <a href="#">Twitter</a>
                </div>
            </div>
        </footer>

    </div>
</body>
</html>"""
    with open(os.path.join(OUTPUT_DIR, "login.html"), "w") as f:
        f.write(auth_html.replace("{sidebar}", get_sidebar_html()).replace("{title}", "Log In"))
    with open(os.path.join(OUTPUT_DIR, "signup.html"), "w") as f:
        f.write(auth_html.replace("{sidebar}", get_sidebar_html()).replace("{title}", "Sign Up"))

    render_community_page()
    
    # Build Sitemap & Robots
    sitemap_pages = ["index.html", "community.html", "login.html", "signup.html"]
    if "thermodyne.html" in os.listdir(OUTPUT_DIR): sitemap_pages.append("thermodyne.html")
    if "accessories.html" in os.listdir(OUTPUT_DIR): sitemap_pages.append("accessories.html")
    if os.path.exists(os.path.join(OUTPUT_DIR, "brands")):
        for f in os.listdir(os.path.join(OUTPUT_DIR, "brands")):
            if f.endswith(".html"): sitemap_pages.append(f"brands/{f}")
    if os.path.exists(os.path.join(OUTPUT_DIR, "categories")):
        for f in os.listdir(os.path.join(OUTPUT_DIR, "categories")):
            if f.endswith(".html"): sitemap_pages.append(f"categories/{f}")
        
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap("https://thermodyne.pixiespantryshop.com", sitemap_pages))
        
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: https://thermodyne.pixiespantryshop.com/sitemap.xml")
        
    print("Storefront generated successfully with SEO/Sitemap!")

if __name__ == "__main__":
    generate_site()
