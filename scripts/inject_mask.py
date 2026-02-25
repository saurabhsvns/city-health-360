import re

base64_img = ""
with open("b64_icon.txt", "r") as f:
    base64_img = f.read().strip()

# Create the mask div
# We will use text-indigo-200 and bg-current
mask_div = f"""// Partly Cloudy Night (Moon + Cloud)
                        return `<div class="w-12 h-12 bg-indigo-200 mask-cloudy-night" style="-webkit-mask-image: url('data:image/png;base64,{base64_img}'); -webkit-mask-size: contain; -webkit-mask-repeat: no-repeat; mask-image: url('data:image/png;base64,{base64_img}'); mask-size: contain; mask-repeat: no-repeat; mask-position: center;"></div>`;"""

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# The block to replace
target = r"""// Partly Cloudy Night \(Moon \+ Cloud\)\n\s+return `<svg class="w-12 h-12 text-indigo-200.*?sv.*?>`;"""
new_html = re.sub(target, mask_div, html, flags=re.DOTALL)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print("Updated index.html")
