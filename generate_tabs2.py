file_path = "generate_storefront.py"
with open(file_path, "r") as f:
    code = f.read()

start_marker = "<!-- Product Modal -->"
end_marker = "<!-- Checkout Modal -->"
start_idx = code.find(start_marker)
end_idx = code.find(end_marker)

new_modal_html = """<!-- Product Modal -->
        <div class="modal-overlay" id="modal-overlay">
            <div class="modal" style="max-width: 900px; padding:0; overflow:hidden;">
                <button class="modal-close" id="modal-close" style="position:absolute; right:15px; top:15px; font-size:24px; background:none; border:none; cursor:pointer; z-index:100;">&times;</button>
                <div class="modal-left" style="flex: 1.2; padding: 30px; border-right: 1px solid var(--border); background:#fdfdfd;">
                    <div class="modal-gallery-main">
                        <img src="" alt="Product" class="modal-main-img" id="m-img" style="height: 400px; width: 100%; object-fit: contain;">
                    </div>
                    <div class="modal-gallery-thumbs" id="m-thumbs" style="display: flex; gap: 10px; margin-top: 15px; overflow-x: auto; padding-bottom: 5px;">
                        <!-- Thumbnails injected here -->
                    </div>
                </div>
                <div class="modal-right" style="flex: 1.3; padding: 30px; display:flex; flex-direction:column; max-height:80vh; overflow-y:auto;">
                    <div class="modal-brand" id="m-brand" style="font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin-bottom: 5px;">Brand</div>
                    <h2 class="modal-title" id="m-title" style="margin: 0 0 10px; font-size: 26px;">Product Name</h2>
                    <div class="modal-price" id="m-price" style="font-size: 22px; font-weight: bold; color: var(--gold); margin-bottom: 20px;">$0.00</div>
                    
                    <div class="modal-tabs" style="display: flex; gap: 20px; border-bottom: 1px solid var(--border); margin-bottom: 20px;">
                        <span class="tab-link active" onclick="switchTab('desc', this)" style="cursor: pointer; font-weight: bold; border-bottom: 2px solid var(--gold); padding-bottom:8px; font-size:14px; text-transform:uppercase;">Details</span>
                        <span class="tab-link" onclick="switchTab('specs', this)" style="cursor: pointer; font-weight: bold; padding-bottom:8px; font-size:14px; text-transform:uppercase;">Specs</span>
                        <span class="tab-link" onclick="switchTab('resources', this)" style="cursor: pointer; font-weight: bold; padding-bottom:8px; font-size:14px; text-transform:uppercase;">Resources</span>
                    </div>
                    
                    <div class="tab-content" id="tab-desc" style="display: block; font-size: 14px; line-height: 1.6; color:#444; flex-grow:1; margin-bottom:20px;">
                        <div class="modal-desc" id="m-desc"></div>
                    </div>
                    
                    <div class="tab-content" id="tab-specs" style="display: none; font-size: 14px; line-height: 1.6; color:#444; flex-grow:1; margin-bottom:20px;">
                        <div id="m-specs">No specifications available.</div>
                    </div>
                    
                    <div class="tab-content" id="tab-resources" style="display: none; font-size: 14px; line-height: 1.6; color:#444; flex-grow:1; margin-bottom:20px;">
                        <div id="m-resources">No downloadable resources available.</div>
                    </div>
                    
                    <div class="variant-label" id="v-label" style="font-weight:bold; font-size:12px; text-transform:uppercase; margin-bottom:10px;">Options</div>
                    <div class="swatch-group" id="swatches" style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:20px;"></div>
                    
                    <button class="btn modal-buy-btn" id="add-to-cart-btn" style="width: 100%; padding: 15px; font-size: 16px; margin-top:auto;">Add to Cart</button>
                </div>
            </div>
        </div>
        
        <script>
            function switchTab(tabId, el) {
                document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
                document.querySelectorAll('.tab-link').forEach(t => t.style.borderBottom = 'none');
                document.getElementById('tab-' + tabId).style.display = 'block';
                el.style.borderBottom = '2px solid var(--gold)';
            }
        </script>
        
        """

if start_idx != -1 and end_idx != -1:
    code = code[:start_idx] + new_modal_html + code[end_idx:]

with open(file_path, "w") as f:
    f.write(code)

# JS Patch
js_path = "js/main.js"
with open(js_path, "r") as f:
    js_code = f.read()

js_target = "document.getElementById('m-desc').innerHTML = p.body_html || '';"
if js_target in js_code:
    js_new = """
            document.getElementById('m-desc').innerHTML = p.body_html || 'No details available.';
            document.getElementById('m-specs').innerHTML = (p.specs && p.specs.html) ? p.specs.html : 'No specifications available.';
            
            let resHtml = '';
            if(p.resources && p.resources.length > 0) {
                resHtml = '<ul style="list-style: none; padding: 0; margin: 0;">';
                p.resources.forEach(r => {
                    resHtml += `<li style="margin-bottom: 8px;"><a href="${r.url}" target="_blank" style="color: var(--gold); font-weight: bold; text-decoration: none;">📄 ${r.text}</a></li>`;
                });
                resHtml += '</ul>';
            } else {
                resHtml = 'No downloadable resources available.';
            }
            document.getElementById('m-resources').innerHTML = resHtml;
            
            const thumbsContainer = document.getElementById('m-thumbs');
            thumbsContainer.innerHTML = '';
            if(p.all_images && p.all_images.length > 0) {
                p.all_images.forEach(imgSrc => {
                    const imgEl = document.createElement('img');
                    imgEl.src = imgSrc;
                    imgEl.style = "width: 60px; height: 60px; object-fit: contain; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; display:inline-block;";
                    imgEl.onclick = () => document.getElementById('m-img').src = imgSrc;
                    thumbsContainer.appendChild(imgEl);
                });
            } else {
                const imgEl = document.createElement('img');
                imgEl.src = p.featured_image || '';
                imgEl.style = "width: 60px; height: 60px; object-fit: contain; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; display:inline-block;";
                thumbsContainer.appendChild(imgEl);
            }
"""
    js_code = js_code.replace(js_target, js_new)
    with open(js_path, "w") as f:
        f.write(js_code)
    print("Patched main.js!")
else:
    print("Could not find JS target to patch.")
    
print("Updated generate_storefront.py modal UI.")
