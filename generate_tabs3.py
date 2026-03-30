import re
js_path = "js/main.js"
with open(js_path, "r") as f:
    js_code = f.read()

js_target = "mDesc.innerHTML = p.body_html || 'No description available.';"
js_new = """mDesc.innerHTML = p.body_html || 'No description available.';
            
            const mSpecs = document.getElementById('m-specs');
            if(mSpecs) mSpecs.innerHTML = (p.specs && p.specs.html) ? p.specs.html : 'No specifications available.';
            
            const mRes = document.getElementById('m-resources');
            if(mRes) {
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
                mRes.innerHTML = resHtml;
            }
            
            const thumbsContainer = document.getElementById('m-thumbs');
            if(thumbsContainer) {
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
            }
"""
js_code = js_code.replace(js_target, js_new)
with open(js_path, "w") as f:
    f.write(js_code)
print("Patched main.js!")
