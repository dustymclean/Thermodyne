import os
import re

SOURCE = os.path.expanduser("~/Desktop/Synergy_Shop/generate_storefront.py")
DEST = os.path.expanduser("~/Desktop/Thermodyne_Catalog/generate_storefront.py")

with open(SOURCE, "r", encoding="utf-8") as f:
    content = f.read()

# Replacements
content = content.replace("Synergy Innovation", "Thermodyne Systems")
content = content.replace("Synergy", "Thermodyne")
content = content.replace("synergy_products.json", "Thermodyne_Products.json")
content = content.replace("Synergy_Scraper", "Thermodyne_Catalog")
content = content.replace("Synergy_Shop", "Thermodyne_Catalog")
content = content.replace("DaVinci", "Desktop Vaporizers")
content = content.replace("Eyce", "Portable Vaporizers")
content = content.replace("davinci", "desktop")
content = content.replace("eyce", "portable")
content = content.replace("synergyinnovation.com", "thermodyne.pixiespantryshop.com")
content = content.replace("synergy", "thermodyne")

with open(DEST, "w", encoding="utf-8") as f:
    f.write(content)

with open(os.path.expanduser("~/Desktop/Thermodyne_Catalog/CNAME"), "w", encoding="utf-8") as f:
    f.write("thermodyne.pixiespantryshop.com")

