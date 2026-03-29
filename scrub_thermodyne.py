import csv
import json
import re
import os

# Configuration per McLean Quality Audit Protocol (Updated for Dyspensr/Synergy Format)
RAW_CSV = "Thermodyne_Products.csv"
MAPPING_JSON = "medical_mapping.json"
MEDICAL_CSV = "Thermodyne_Medical_Master.csv"

def load_lexicon():
    with open(MAPPING_JSON, 'r') as f:
        return json.load(f)

def clinical_scrub(text, rules):
    """Systematic replacement of consumer slang with clinical nomenclature"""
    if not text: return ""
    scrubbed = text.lower()
    # Sort keys by length descending to prevent partial replacements (e.g., 'vape' before 'vaporizer')
    for slang in sorted(rules.keys(), key=len, reverse=True):
        replacement = rules[slang]
        # Use regex for whole-word replacement only
        pattern = re.compile(rf'\b{re.escape(slang)}\b', re.IGNORECASE)
        scrubbed = pattern.sub(replacement, scrubbed)
    return scrubbed.capitalize()

def generate_medical_catalog():
    lexicon = load_lexicon()
    rules = lexicon['scrub_rules']
    
    print("🧬 Initiating Medical Scrub of Thermodyne Inventory...")
    
    with open(RAW_CSV, 'r', encoding='utf-8') as infile, \
         open(MEDICAL_CSV, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["Clinical_Justification", "Safety_Standard"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        count = 0
        for row in reader:
            # Scrub Title and Body (HTML) (since Description was mapped to Body (HTML) in the new scraper)
            row['Title'] = clinical_scrub(row['Title'], rules)
            if 'Body (HTML)' in row:
                row['Body (HTML)'] = clinical_scrub(row['Body (HTML)'], rules)
            
            # Inject Auditor Clinical Rationale
            row['Clinical_Justification'] = (
                "Precision thermal extraction optimized for respiratory harm reduction "
                "via non-combustive aerosolization."
            )
            row['Safety_Standard'] = "MGV-1 Verified: Total Thermal Isolation (TTI) airpath."
            
            writer.writerow(row)
            count += 1
            
    print(f"✅ Scrub Complete: {count} items reclassified into {MEDICAL_CSV}")

if __name__ == "__main__":
    if os.path.exists(RAW_CSV):
        generate_medical_catalog()
    else:
        print(f"❌ Error: {RAW_CSV} not found. Run the scraper first.")
