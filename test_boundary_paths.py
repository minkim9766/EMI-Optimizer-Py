import re

with open('enclosed_regions.svg', 'r', encoding='utf-8') as f:
    content = f.read()

viewbox_match = re.search(r'viewBox="([^"]+)"', content)
width_match = re.search(r'width="([^"]+)"', content)
height_match = re.search(r'height="([^"]+)"', content)

if viewbox_match:
    vb_parts = viewbox_match.group(1).split()
    vb_x, vb_y, vb_width, vb_height = vb_parts
else:
    vb_x, vb_y, vb_width, vb_height = "0", "0", "100", "100"

width = width_match.group(1) if width_match else vb_width
height = height_match.group(1) if height_match else vb_height

boundary_mask_match = re.search(r'<mask id="boundary-interior-mask">(.*?)</mask>', content, re.DOTALL)
boundary_paths = []
if boundary_mask_match:
    boundary_mask_content = boundary_mask_match.group(1)
    path_tags = re.findall(r'<path[^>]+fill="white"[^>]*/>', boundary_mask_content)
    for tag in path_tags:
        d_match = re.search(r'd="([^"]+)"', tag)
        if d_match:
            boundary_paths.append(d_match.group(1))

svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">
<g>
'''
for d in boundary_paths:
    svg += f'  <path d="{d}" fill="red" fill-rule="evenodd"/>' + "\n"
svg += '</g>\n</svg>'

with open('test_boundary_paths.svg', 'w', encoding='utf-8') as f:
    f.write(svg)

