import os
import re

file_path = "js/main.js"
with open(file_path, "r") as f:
    code = f.read()

# I will inject the 'on_sale' badge logic into the product card renderer.
card_target = """<div class="card" onclick="openModal('${p.handle}')">"""
card_new = """<div class="card" onclick="openModal('${p.handle}')" style="position: relative;">
                        ${p.on_sale ? '<div style="position: absolute; top: 10px; left: 10px; background: red; color: white; padding: 4px 8px; font-size: 10px; font-weight: 800; border-radius: 4px; text-transform: uppercase; z-index: 10;">Sale</div>' : ''}"""

code = code.replace(card_target, card_new)

# I also need to update the table rendering in the dashboard.html so it properly binds the inputs.
# Wait, I already wrote dashboard.html. But the render function inside dashboard.html needs to have the inner HTML fixed.

with open(file_path, "w") as f:
    f.write(code)

print("Patched main.js to show Sale badges!")
