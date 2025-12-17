"""
SVG 이미지 반전 스크립트
- 보이는 부분(도형이 있는 부분)을 제거하고
- 안 보이는 부분(빈 공간)을 드러나도록 함

방법: SVG 마스크를 사용하여 전체 영역에서 기존 도형들을 빼냄
"""

import re
from xml.etree import ElementTree as ET
import sys


def invert_svg(input_file, output_file, background_color="#ffffff", inverted_color="#000000"):
    """
    SVG 파일을 반전시킵니다.

    Args:
        input_file: 입력 SVG 파일 경로
        output_file: 출력 SVG 파일 경로
        background_color: 반전된 영역의 색상 (기본: 흰색)
        inverted_color: 원래 도형이 있던 영역의 색상 (기본: 검은색 - 투명하게 만들어짐)
    """

    # SVG 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # viewBox와 width/height 추출
    viewbox_match = re.search(r'viewBox="([^"]+)"', content)
    width_match = re.search(r'width="([^"]+)"', content)
    height_match = re.search(r'height="([^"]+)"', content)

    if viewbox_match:
        viewbox = viewbox_match.group(1)
        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = float(vb_parts[0]), float(vb_parts[1]), float(vb_parts[2]), float(vb_parts[3])
    else:
        vb_x, vb_y = 0, 0
        vb_width = float(width_match.group(1).replace('mm', '').replace('px', '')) if width_match else 100
        vb_height = float(height_match.group(1).replace('mm', '').replace('px', '')) if height_match else 100

    width = width_match.group(1) if width_match else str(vb_width)
    height = height_match.group(1) if height_match else str(vb_height)

    # 모든 path 요소와 circle, rect 등의 도형 요소 추출
    paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', content)
    circles = re.findall(r'<circle[^>]*cx="([^"]+)"[^>]*cy="([^"]+)"[^>]*r="([^"]+)"[^>]*/>', content)

    # use 요소에서 참조하는 도형도 처리
    uses = re.findall(r'<use[^>]*xlink:href="#([^"]+)"[^>]*x="([^"]+)"[^>]*y="([^"]+)"[^>]*/>', content)

    # defs에서 정의된 도형들 추출
    defs_circles = {}
    defs_match = re.search(r'<defs>(.*?)</defs>', content, re.DOTALL)
    if defs_match:
        defs_content = defs_match.group(1)
        # g 요소 안의 circle 추출
        g_patterns = re.findall(r'<g id="([^"]+)">\s*<circle[^>]*cx="([^"]+)"[^>]*cy="([^"]+)"[^>]*r="([^"]+)"[^>]*/>\s*</g>', defs_content)
        for g_id, cx, cy, r in g_patterns:
            defs_circles[g_id] = (float(cx), float(cy), float(r))

    # 반전된 SVG 생성
    inverted_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">
<defs>
    <!-- 원본 도형들을 마스크로 정의 -->
    <mask id="inverted-mask">
        <!-- 전체 영역을 흰색으로 (보이게) -->
        <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" fill="white"/>
        
        <!-- 원본 도형들을 검은색으로 (안 보이게 = 마스크에서 제외) -->
'''

    # Path 요소들을 마스크에 추가
    for path_d in paths:
        inverted_svg += f'        <path d="{path_d}" fill="black"/>\n'

    # Circle 요소들을 마스크에 추가
    for cx, cy, r in circles:
        if float(r) > 0:  # 반지름이 0보다 큰 경우만
            inverted_svg += f'        <circle cx="{cx}" cy="{cy}" r="{r}" fill="black"/>\n'

    # Use 요소에서 참조된 도형들을 마스크에 추가
    for ref_id, x, y in uses:
        if ref_id in defs_circles:
            cx, cy, r = defs_circles[ref_id]
            if r > 0:
                actual_cx = cx + float(x)
                actual_cy = cy + float(y)
                inverted_svg += f'        <circle cx="{actual_cx}" cy="{actual_cy}" r="{r}" fill="black"/>\n'

    inverted_svg += f'''    </mask>
</defs>

<!-- 마스크를 적용한 배경 사각형 - 원본 도형이 없던 부분만 보임 -->
<rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" 
      fill="{background_color}" mask="url(#inverted-mask)"/>
</svg>'''

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(inverted_svg)

    print(f"반전된 SVG가 '{output_file}'에 저장되었습니다.")
    print(f"- 원본에서 도형이 있던 부분: 투명 (빈 공간)")
    print(f"- 원본에서 빈 공간이었던 부분: {background_color} 색상으로 채워짐")


def invert_svg_simple(input_file, output_file, fill_color="#000000"):
    """
    더 간단한 방법: clipPath를 사용하여 SVG 반전
    원본 도형 영역을 잘라내어 배경만 남김
    """

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # viewBox와 dimensions 추출
    viewbox_match = re.search(r'viewBox="([^"]+)"', content)
    width_match = re.search(r'width="([^"]+)"', content)
    height_match = re.search(r'height="([^"]+)"', content)

    if viewbox_match:
        viewbox = viewbox_match.group(1)
        vb_parts = viewbox.split()
        vb_x, vb_y, vb_width, vb_height = float(vb_parts[0]), float(vb_parts[1]), float(vb_parts[2]), float(vb_parts[3])
    else:
        vb_x, vb_y = 0, 0
        vb_width = float(width_match.group(1).replace('mm', '').replace('px', '')) if width_match else 100
        vb_height = float(height_match.group(1).replace('mm', '').replace('px', '')) if height_match else 100

    width = width_match.group(1) if width_match else str(vb_width)
    height = height_match.group(1) if height_match else str(vb_height)

    # 모든 도형 요소 추출
    paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', content)
    circles_full = re.findall(r'<circle[^>]+/>', content)

    # 외곽 사각형과 모든 도형을 하나의 path로 결합 (fill-rule: evenodd 사용)
    # 외곽 사각형 (시계방향)
    outer_rect = f"M{vb_x},{vb_y} L{vb_x + vb_width},{vb_y} L{vb_x + vb_width},{vb_y + vb_height} L{vb_x},{vb_y + vb_height} Z"

    # 모든 path를 결합
    all_paths = [outer_rect] + paths
    combined_path = " ".join(all_paths)

    inverted_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">
<!-- 반전된 SVG: fill-rule="evenodd"를 사용하여 외곽 사각형에서 내부 도형들을 뺌 -->
<path d="{combined_path}" fill="{fill_color}" fill-rule="evenodd"/>
</svg>'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(inverted_svg)

    print(f"반전된 SVG가 '{output_file}'에 저장되었습니다. (fill-rule: evenodd 방식)")


if __name__ == "__main__":
    input_file = "output.svg"
    output_file_mask = "inverted_output_mask.svg"  # 마스크 방식
    output_file_evenodd = "inverted_output_evenodd.svg"  # evenodd 방식

    print("=" * 50)
    print("SVG 반전 (마스크 방식)")
    print("=" * 50)
    invert_svg(input_file, output_file_mask, background_color="#288f28")

    print("\n" + "=" * 50)
    print("SVG 반전 (fill-rule: evenodd 방식)")
    print("=" * 50)
    invert_svg_simple(input_file, output_file_evenodd, fill_color="#288f28")

    print("\n두 가지 방식의 결과물이 생성되었습니다:")
    print(f"1. {output_file_mask} - 마스크를 사용한 반전 (원본 도형 영역이 투명)")
    print(f"2. {output_file_evenodd} - evenodd fill-rule을 사용한 반전 (더 간단하고 호환성 좋음)")

