import json
import os
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

class DashboardHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        if self.path == '/':
            self.path = '/dashboard.html'
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/save_products':
            length = int(self.headers.get('content-length'))
            post_data = self.rfile.read(length)
            products_data = json.loads(post_data)

            # Update JSON file
            with open('Thermodyne_Products.json', 'r+', encoding='utf-8') as f:
                data = json.load(f)
                
                # Merge logic
                product_dict = {p['handle']: p for p in data.get('products', [])}
                for new_p in products_data:
                    handle = new_p['handle']
                    if handle in product_dict:
                        product_dict[handle].update(new_p)
                    else:
                        product_dict[handle] = new_p
                
                data['products'] = list(product_dict.values())
                
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.truncate()
            
            # Trigger storefront rebuild
            print("Rebuilding storefront...")
            subprocess.run(["python3", "generate_storefront.py"])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Storefront rebuilt!"}).encode())

        elif self.path == '/api/create_bundle':
            length = int(self.headers.get('content-length'))
            post_data = self.rfile.read(length)
            bundle_data = json.loads(post_data)
            
            with open('Thermodyne_Products.json', 'r+', encoding='utf-8') as f:
                data = json.load(f)
                
                new_bundle = {
                    "handle": bundle_data['handle'],
                    "brand": "Thermodyne Systems",
                    "title": bundle_data['title'],
                    "vendor": "Thermodyne Systems",
                    "product_type": "Bundle",
                    "tags": ["Bundle"],
                    "body_html": f"<p>This exclusive bundle includes multiple premium items.</p>",
                    "min_price": bundle_data['price'],
                    "max_price": bundle_data['price'],
                    "on_sale": True,
                    "is_bundle": True,
                    "bundle_children": bundle_data['children'],
                    "all_images": [bundle_data.get('featured_image', '')],
                    "featured_image": bundle_data.get('featured_image', ''),
                    "url": "javascript:void(0)",
                    "options": [{"name": "Default", "values": ["Bundle"]}],
                    "in_stock_variants": [{
                        "variant_id": f"{bundle_data['handle']}-bundle",
                        "sku": f"BNDL-{bundle_data['handle'][:6].upper()}",
                        "option1_name": "Default",
                        "option1_value": "Bundle",
                        "price": bundle_data['price'],
                        "available": True,
                        "inventory_quantity": 10,
                        "variant_image": bundle_data.get('featured_image', '')
                    }]
                }
                
                data['products'].insert(0, new_bundle)
                data['total_products'] = len(data['products'])
                
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.truncate()
                
            print("Rebuilding storefront with new bundle...")
            subprocess.run(["python3", "generate_storefront.py"])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

def run():
    print("🚀 Starting Thermodyne CMS Dashboard on http://localhost:8000")
    print("Press Ctrl+C to stop.")
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, DashboardHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
