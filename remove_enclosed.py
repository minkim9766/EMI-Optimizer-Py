"""
enclosed_regions.svg에서 표시된 영역을 inverted_output_mask.svg에서 제거
"""

import re


def remove_enclosed_from_inverted(inverted_file, enclosed_file, output_file, background_color="#288f28"):
    """
    inverted_output_mask.svg에서 enclosed_regions.svg에 표시된 영역을 제거
    """

    # inverted_output_mask.svg 읽기
    with open(inverted_file, 'r', encoding='utf-8') as f:
        inverted_content = f.read()

    # enclosed_regions.svg 읽기
    with open(enclosed_file, 'r', encoding='utf-8') as f:
        enclosed_content = f.read()

    # viewBox와 dimensions 추출
    viewbox_match = re.search(r'viewBox="([^"]+)"', inverted_content)
    width_match = re.search(r'width="([^"]+)"', inverted_content)
    height_match = re.search(r'height="([^"]+)"', inverted_content)

    if viewbox_match:
        vb_parts = viewbox_match.group(1).split()
        vb_x, vb_y, vb_width, vb_height = float(vb_parts[0]), float(vb_parts[1]), float(vb_parts[2]), float(vb_parts[3])
    else:
        vb_x, vb_y, vb_width, vb_height = 0, 0, 100, 100

    width = width_match.group(1) if width_match else str(vb_width)
    height = height_match.group(1) if height_match else str(vb_height)

    # inverted_output_mask.svg에서 모든 path와 circle 추출
    paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', inverted_content)
    circles = re.findall(r'<circle[^>]*cx="([^"]+)"[^>]*cy="([^"]+)"[^>]*r="([^"]+)"[^>]*/>', inverted_content)

    # enclosed_regions.svg에서 boundary-interior-mask의 path들 추출
    # fill="white"인 것들이 제거해야 할 영역
    boundary_mask_match = re.search(r'<mask id="boundary-interior-mask">(.*?)</mask>', enclosed_content, re.DOTALL)

    boundary_paths = []
    if boundary_mask_match:
        boundary_mask_content = boundary_mask_match.group(1)
        # 모든 path 태그를 찾아서 d 속성 추출 (fill="white"인 것만, rect 제외)
        path_tags = re.findall(r'<path[^>]+fill="white"[^>]*/>', boundary_mask_content)
        for tag in path_tags:
            d_match = re.search(r'd="([^"]+)"', tag)
            if d_match:
                boundary_paths.append(d_match.group(1))

    print(f"inverted_output_mask.svg - path: {len(paths)}개, circle: {len(circles)}개")
    print(f"enclosed_regions.svg - boundary path: {len(boundary_paths)}개")

    # boundary_paths 디버깅 출력
    print(f"boundary-interior-mask에서 추출된 path 개수: {len(boundary_paths)}")
    if boundary_paths:
        print(f"첫 path d: {boundary_paths[0][:100]}")

    # 새 SVG 생성
    # 방법: inverted_output_mask와 동일하되, boundary_paths 영역을 추가로 가림
    svg_output = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">
<defs>
    <!-- 원본 도형들을 마스크로 정의 -->
    <mask id="inverted-mask">
        <!-- 전체 영역을 흰색으로 (보이게) -->
        <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" fill="white"/>
        
        <!-- 원본 도형들을 검은색으로 (안 보이게 = 마스크에서 제외) -->
'''

    for path_d in paths:
        svg_output += f'        <path d="{path_d}" fill="black"/>\n'

    for cx, cy, r in circles:
        svg_output += f'        <circle cx="{cx}" cy="{cy}" r="{r}" fill="black"/>\n'

    # boundary_paths도 검은색으로 추가 (이 영역도 가림 = 제거)
    svg_output += f'\n        <!-- enclosed_regions에서 제거할 영역 -->\n'
    for path_d in boundary_paths:
        svg_output += f'        <path d="{path_d}" fill="black" fill-rule="evenodd"/>' + "\n"

    svg_output += f'''    </mask>
</defs>

<!-- 마스크를 적용한 배경 사각형 - 원본 도형이 없던 부분만 보임 (enclosed 영역 제외) -->
<rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" 
      fill="{background_color}" mask="url(#inverted-mask)"/>
</svg>'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_output)

    print(f"완료! 출력 파일: {output_file}")


if __name__ == "__main__":
    remove_enclosed_from_inverted(
        "inverted_output_mask.svg",
        "enclosed_regions.svg",
        "inverted_without_enclosed.svg",
        background_color="#288f28"
    )
