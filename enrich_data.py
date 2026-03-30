import json
import csv
import os

OUTPUT_JSON = "Thermodyne_Products.json"
OUTPUT_CSV = "Thermodyne_Products.csv"

def categorize(title, url):
    title_lower = title.lower()
    url_lower = url.lower() if url else ""
    
    # Brand extraction
    brand = "Thermodyne Systems"
    if "utillian" in title_lower: brand = "Utillian"
    elif "zeus" in title_lower: brand = "Zeus"
    elif "puffco" in title_lower: brand = "Puffco"
    elif "yocan" in title_lower: brand = "Yocan"
    elif "lookah" in title_lower: brand = "Lookah"
    elif "linx" in title_lower: brand = "Linx"
    elif "tronian" in title_lower: brand = "Tronian"
    elif "focus v" in title_lower: brand = "Focus V"
    elif "storz" in title_lower or "bickel" in title_lower or "volcano" in title_lower: brand = "Storz & Bickel"
    elif "pax" in title_lower: brand = "PAX"
    elif "arizer" in title_lower: brand = "Arizer"
    elif "dr. dabber" in title_lower: brand = "Dr. Dabber"
    elif "kandy" in title_lower: brand = "KandyPens"
    elif "g pen" in title_lower or "grenco" in title_lower: brand = "G Pen"
    elif "vivant" in title_lower: brand = "Vivant"
    elif "boundless" in title_lower: brand = "Boundless"
    elif "smok" in title_lower: brand = "SMOK"
    elif "milatron" in title_lower: brand = "Milatron"
    elif "litl" in title_lower: brand = "LITL"

    # Category extraction
    product_type = "Hardware"
    
    if "glass" in title_lower or "bubbler" in title_lower or "coil" in title_lower or "atomizer" in title_lower or "mouthpiece" in title_lower or "charger" in title_lower or "case" in title_lower or "screen" in title_lower or "accessory" in title_lower or "accessories" in url_lower or "part" in title_lower or "-parts" in url_lower or "replacement" in title_lower or "cleaning" in title_lower or "care kit" in title_lower or "hub" in title_lower or "adapter" in title_lower:
        product_type = "Parts & Accessories"
    elif "desktop" in title_lower or "volcano" in title_lower or "desktop-vaporizers" in url_lower:
        product_type = "Desktop Vaporizers"
    elif "wax" in title_lower or "wax-vaporizers" in url_lower or "dab" in title_lower or "rig" in title_lower or "concentrate" in title_lower:
        if "pen" in title_lower or "wax-pens" in url_lower:
            product_type = "Wax Pens"
        elif "rig" in title_lower or "electric-dab-rigs" in url_lower or "omegatron" in title_lower:
            product_type = "E-Rigs"
        else:
            product_type = "Wax Vaporizers"
    elif "cartridge" in title_lower or "510" in title_lower or "thread" in title_lower or "battery" in title_lower or "510-thread-batteries" in url_lower or "nutron" in title_lower or "pitron" in title_lower or "autospinner" in title_lower or "cart" in title_lower:
        product_type = "510 Batteries & Carts"
    elif "vaporizer" in title_lower or "vaporizers" in url_lower or "dry herb" in title_lower:
        product_type = "Dry Herb Vaporizers"
    
    if product_type == "Hardware":
        if "vape" in title_lower:
            product_type = "Vapes"

    return brand, product_type

def main():
    base_dir = os.path.expanduser("~/Desktop/Thermodyne_Catalog")
    json_path = os.path.join(base_dir, OUTPUT_JSON)
    csv_path = os.path.join(base_dir, OUTPUT_CSV)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for item in data.get("products", []):
        title = item.get("title", "")
        url = item.get("url", "")
        brand, ptype = categorize(title, url)
        
        item["brand"] = brand
        item["vendor"] = brand
        item["product_type"] = ptype
        if ptype not in item["tags"]:
            item["tags"].append(ptype)
            
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    # Process CSV
    csv_rows = []
    headers = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            title = row.get("Title", "")
            url = row.get("Product URL", "")
            brand, ptype = categorize(title, url)
            
            row["Brand"] = brand
            row["Vendor"] = brand
            row["Product Type"] = ptype
            tags = [t.strip() for t in row.get("Tags", "").split(",")]
            if ptype not in tags:
                tags.append(ptype)
            row["Tags"] = ", ".join(tags)
            csv_rows.append(row)
            
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_rows)
        
    print("Categorization complete.")

if __name__ == "__main__":
    main()
