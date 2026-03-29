import csv
import os

# Configuration per Vanguard Storefront Engine Architecture
INPUT_CSV = "Thermodyne_Medical_Master.csv"
OUTPUT_DIR = "catalog"

# HTML Template with Sidebar Search and Filter logic
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Thermodyne Systems | Medical-Grade Hardware</title>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <header>
        <h1>Thermodyne Systems: MGV-1 Certified Inventory</h1>
    </header>
    
    <div class="container" style="display: flex;">
        <aside class="sidebar-left" style="width: 20%; padding: 20px;">
            <h3>Inventory Search</h3>
            <input type="text" id="productSearch" placeholder="Search clinical hardware...">
            
            <h3>Clinical Categories</h3>
            <ul id="categoryList">
                <li><a href="#">Active Electronic TEDs</a></li>
                <li><a href="#">Hydro-Filtration Vessels</a></li>
                <li><a href="#">Botanical Homogenizers</a></li>
            </ul>
        </aside>

        <main class="product-grid" style="width: 60%; padding: 20px;">
            <div id="products">
                {product_cards}
            </div>
        </main>

        <aside class="sidebar-right" style="width: 20%; padding: 20px;">
            <h3>Filter Results</h3>
            <h4>Material Standard</h4>
            <label><input type="checkbox"> Borosilicate 3.3</label><br>
            <label><input type="checkbox"> Medical-Grade Silicone</label><br>
            
            <h4>Price Range</h4>
            <select>
                <option>All Tiers</option>
                <option>Tier 1 (Gold Standard)</option>
                <option>Tier 2 (Materially Pure)</option>
            </select>
        </aside>
    </div>

    <script src="../js/main.js"></script>
</body>
</html>
"""

def build_product_card(row):
    """Generates a technical data sheet card for each item"""
    price = row.get('Variant Price', row.get('MSRP', '0.00'))
    description = row.get('Body (HTML)', row.get('Description', ''))
    
    # Try multiple keys to remain compatible with old/new format
    inv_qty = row.get('Inventory Quantity', '0')
    inv_status = row.get('Inventory_Status', 'In Stock' if int(float(inv_qty)) > 0 else 'Out of Stock')
    
    return f'''
    <div class="product-card">
        <h2>{row['Title']}</h2>
        <p><strong>Brand:</strong> {row['Brand']}</p>
        <p><strong>Price:</strong> ${price}</p>
        <p class="status">{inv_status}</p>
        <div class="specs">
            <p>{description}</p>
            <p class="audit-note"><strong>Auditor Note:</strong> {row.get('Safety_Standard', 'N/A')}</p>
        </div>
        <button>View Technical Vetting Sheet</button>
    </div>
    '''

def generate_site():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    product_cards = ""
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check for in-stock via new or old columns
            inv_qty = row.get('Inventory Quantity', '0')
            inv_status = row.get('Inventory_Status', 'In Stock' if int(float(inv_qty)) > 0 else 'Out of Stock')
            
            if inv_status == "In Stock":
                product_cards += build_product_card(row)
                
    final_html = HTML_TEMPLATE.format(product_cards=product_cards)
    
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding='utf-8') as f:
        f.write(final_html)
    print(f"✅ Storefront Built: {OUTPUT_DIR}/index.html")

if __name__ == "__main__":
    generate_site()
