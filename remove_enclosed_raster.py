import cairosvg
from PIL import Image
import numpy as np
import io

def svg_to_png_bytes(svg_path, scale=10):
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_data = f.read()
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'), scale=scale)
    return png_bytes

def mask_enclosed(inverted_svg, enclosed_svg, output_png, output_svg=None, scale=10):
    # SVG -> PNG 변환
    inv_png = svg_to_png_bytes(inverted_svg, scale)
    enc_png = svg_to_png_bytes(enclosed_svg, scale)
    inv_img = Image.open(io.BytesIO(inv_png)).convert('RGBA')
    enc_img = Image.open(io.BytesIO(enc_png)).convert('L')  # 흑백 마스크

    inv_arr = np.array(inv_img)
    enc_arr = np.array(enc_img)

    # 마스킹: enclosed가 밝은(흰색) 부분은 완전히 투명하게
    mask = enc_arr < 128  # enclosed가 검정(유지)인 부분만 True
    inv_arr[~mask, :3] = 0    # RGB를 0으로 초기화 (투명화된 부분이 초록색 등으로 보이지 않게)
    inv_arr[~mask, 3] = 0     # 알파 0으로

    result_img = Image.fromarray(inv_arr)
    result_img.save(output_png)
    print(f"PNG 저장: {output_png}")

    if output_svg:
        # PNG를 base64로 SVG에 래핑
        import base64
        with open(output_png, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        with open(inverted_svg, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        import re
        vb_match = re.search(r'viewBox="([^"]+)"', svg_content)
        width_match = re.search(r'width="([^"]+)"', svg_content)
        height_match = re.search(r'height="([^"]+)"', svg_content)
        if vb_match:
            vb = vb_match.group(1)
        else:
            vb = '0 0 100 100'
        width = width_match.group(1) if width_match else '100'
        height = height_match.group(1) if height_match else '100'
        svg_out = f'''<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{vb}">\n  <image href="data:image/png;base64,{b64}" width="{width}" height="{height}"/>\n</svg>'''
        with open(output_svg, 'w', encoding='utf-8') as f:
            f.write(svg_out)
        print(f"SVG(래스터) 저장: {output_svg}")

if __name__ == "__main__":
    mask_enclosed(
        'inverted_output_mask.svg',
        'enclosed_regions.svg',
        'inverted_without_enclosed_raster.png',
        'inverted_without_enclosed_raster.svg',
        scale=10
    )
