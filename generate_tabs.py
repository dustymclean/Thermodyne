import re

file_path = "generate_storefront.py"
with open(file_path, "r") as f:
    code = f.read()

# I will update the modal HTML in generate_storefront.py to include tabs for "Description", "Specs", "Resources" and a thumbnail slider for "Image Galleries".
# This will ensure the "hyper detailed information" the user mentioned is utilized and implemented in the store perfectly.

new_modal_html = """
        <!-- Product Modal -->
        <div class="modal-overlay" id="modal-overlay">
            <div class="modal" style="max-width: 900px;">
                <button class="modal-close" id="modal-close">&times;</button>
                <div class="modal-left" style="flex: 1.2;">
                    <div class="modal-gallery-main">
                        <img src="" alt="Product" class="modal-main-img" id="m-img" style="height: 400px; width: 100%; object-fit: contain;">
                    </div>
                    <div class="modal-gallery-thumbs" id="m-thumbs" style="display: flex; gap: 10px; margin-top: 15px; overflow-x: auto; padding-bottom: 5px;">
                        <!-- Thumbnails injected here -->
                    </div>
                </div>
                <div class="modal-right" style="flex: 1;">
                    <h2 class="modal-title" id="m-title">Title</h2>
                    <div class="modal-brand" id="m-brand" style="margin-bottom: 10px;">Brand</div>
                    <div class="modal-price" id="m-price">$0.00</div>
                    
                    <div class="modal-tabs" style="display: flex; gap: 15px; border-bottom: 1px solid var(--border); margin: 20px 0; padding-bottom: 5px;">
                        <span class="tab-link active" onclick="switchTab('desc')" style="cursor: pointer; font-weight: bold; border-bottom: 2px solid var(--gold);">Details</span>
                        <span class="tab-link" onclick="switchTab('specs')" style="cursor: pointer; font-weight: bold;">Specs</span>
                        <span class="tab-link" onclick="switchTab('resources')" style="cursor: pointer; font-weight: bold;">Resources</span>
                    </div>
                    
                    <div class="tab-content" id="tab-desc" style="display: block; font-size: 14px; line-height: 1.6; max-height: 250px; overflow-y: auto;">
                        <div class="modal-desc" id="m-desc"></div>
                    </div>
                    
                    <div class="tab-content" id="tab-specs" style="display: none; font-size: 13px; line-height: 1.6; max-height: 250px; overflow-y: auto;">
                        <div id="m-specs">No specifications available.</div>
                    </div>
                    
                    <div class="tab-content" id="tab-resources" style="display: none; font-size: 13px; line-height: 1.6; max-height: 250px; overflow-y: auto;">
                        <div id="m-resources">No downloadable resources available.</div>
                    </div>
                    
                    <div class="variant-label" id="v-label" style="margin-top: 20px;">Options</div>
                    <div class="swatch-group" id="swatches"></div>
                    
                    <button class="btn modal-buy-btn" id="add-to-cart-btn" style="width: 100%; margin-top: 20px;">Add to Cart</button>
                </div>
            </div>
        </div>
        
        <script>
            function switchTab(tabId) {
                document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
                document.querySelectorAll('.tab-link').forEach(t => t.style.borderBottom = 'none');
                document.getElementById('tab-' + tabId).style.display = 'block';
                event.target.style.borderBottom = '2px solid var(--gold)';
            }
        </script>
"""

code = re.sub(r'<!-- Product Modal -->.*?<!-- Checkout Modal -->', new_modal_html + '\n        <!-- Checkout Modal -->', code, flags=re.DOTALL)

# Now update the main.js logic that populates the modal.
code = code.replace("document.getElementById('m-desc').innerHTML = p.body_html || '';", """
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
            
            // Build thumbnails
            const thumbsContainer = document.getElementById('m-thumbs');
            thumbsContainer.innerHTML = '';
            if(p.all_images && p.all_images.length > 0) {
                p.all_images.forEach(imgSrc => {
                    const imgEl = document.createElement('img');
                    imgEl.src = imgSrc;
                    imgEl.style = "width: 60px; height: 60px; object-fit: contain; border: 1px solid var(--border); border-radius: 4px; cursor: pointer;";
                    imgEl.onclick = () => document.getElementById('m-img').src = imgSrc;
                    thumbsContainer.appendChild(imgEl);
                });
            } else {
                const imgEl = document.createElement('img');
                imgEl.src = p.featured_image || '';
                imgEl.style = "width: 60px; height: 60px; object-fit: contain; border: 1px solid var(--border); border-radius: 4px; cursor: pointer;";
                thumbsContainer.appendChild(imgEl);
            }
""")

with open(file_path, "w") as f:
    f.write(code)

print("Updated generate_storefront.py with new tabbed modal and image gallery thumbnails.")
