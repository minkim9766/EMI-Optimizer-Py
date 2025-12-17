"""
SVG 반전 + 얇은 요소 제거 스크립트
- 원본 SVG에서 얇은 요소들을 제거한 후 반전
- 이렇게 하면 반전된 결과에서 얇은 선들이 사라짐
"""

import re


def parse_path_commands(d):
    """SVG path의 d 속성을 파싱하여 좌표들을 추출"""
    numbers = re.findall(r'-?\d+\.?\d*', d)
    coords = [float(n) for n in numbers]
    return coords


def get_path_bounding_box(d):
    """Path의 bounding box (min_x, min_y, max_x, max_y) 계산"""
    coords = parse_path_commands(d)
    if len(coords) < 2:
        return None

    x_coords = coords[0::2]
    y_coords = coords[1::2]

    if not x_coords or not y_coords:
        return None

    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def get_path_dimensions(d):
    """Path의 폭과 높이 계산"""
    bbox = get_path_bounding_box(d)
    if bbox is None:
        return (0, 0)

    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y
    return (width, height)


def is_thin_path(d, min_dimension=0.5):
    """Path가 너무 얇은지 확인"""
    width, height = get_path_dimensions(d)
    if width < min_dimension or height < min_dimension:
        return True
    return False


def invert_svg_filtered(input_file, output_file, background_color="#288f28", min_dimension=0.5):
    """
    SVG 파일을 반전시키면서 얇은 요소들은 제외
    (반전 결과에서 얇은 선들이 사라짐)
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

    # 모든 path 요소 추출
    paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', content)

    # use 요소에서 참조하는 도형도 처리
    uses = re.findall(r'<use[^>]*xlink:href="#([^"]+)"[^>]*x="([^"]+)"[^>]*y="([^"]+)"[^>]*/>', content)

    # defs에서 정의된 도형들 추출
    defs_circles = {}
    defs_match = re.search(r'<defs>(.*?)</defs>', content, re.DOTALL)
    if defs_match:
        defs_content = defs_match.group(1)
        g_patterns = re.findall(r'<g id="([^"]+)">\s*<circle[^>]*cx="([^"]+)"[^>]*cy="([^"]+)"[^>]*r="([^"]+)"[^>]*/>\s*</g>', defs_content)
        for g_id, cx, cy, r in g_patterns:
            defs_circles[g_id] = (float(cx), float(cy), float(r))

    # 필터링 통계
    kept_count = 0
    filtered_count = 0

    # 반전된 SVG 생성
    inverted_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">
<defs>
    <mask id="inverted-mask">
        <!-- 전체 영역을 흰색으로 (보이게) -->
        <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" fill="white"/>
        
        <!-- 원본 도형들을 검은색으로 (안 보이게) -->
        <!-- 얇은 요소는 마스크에 포함하지 않음 = 반전 결과에서 보이지 않음 -->
'''

    # Path 요소들 중 얇지 않은 것만 마스크에 추가
    for path_d in paths:
        if is_thin_path(path_d, min_dimension):
            filtered_count += 1
            # 얇은 요소는 마스크에 추가하지 않음 → 반전 결과에서 안 보임
        else:
            kept_count += 1
            inverted_svg += f'        <path d="{path_d}" fill="black"/>\n'

    # Circle 요소들 (use 요소에서 참조된 것들)
    for ref_id, x, y in uses:
        if ref_id in defs_circles:
            cx, cy, r = defs_circles[ref_id]
            if r > 0:
                actual_cx = cx + float(x)
                actual_cy = cy + float(y)
                # 원은 반지름의 2배가 크기
                if r * 2 >= min_dimension:
                    inverted_svg += f'        <circle cx="{actual_cx}" cy="{actual_cy}" r="{r}" fill="black"/>\n'

    inverted_svg += f'''    </mask>
</defs>

<!-- 마스크를 적용한 배경 사각형 -->
<!-- 유지된 요소: {kept_count}개, 제거된 얇은 요소: {filtered_count}개 -->
<rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" 
      fill="{background_color}" mask="url(#inverted-mask)"/>
</svg>'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(inverted_svg)

    print(f"완료!")
    print(f"- 유지된 요소: {kept_count}개")
    print(f"- 제거된 얇은 요소: {filtered_count}개")
    print(f"- 최소 치수 기준: {min_dimension}")
    print(f"- 출력 파일: {output_file}")


if __name__ == "__main__":
    input_file = "output.svg"
    output_file = "inverted_output_clean.svg"

    # 최소 치수 설정 (이보다 폭이나 높이가 작은 요소는 반전 결과에서 제거됨)
    min_dimension = 0.5

    print(f"SVG 반전 + 얇은 요소 제거 중...")
    print(f"- 입력 파일: {input_file}")
    print(f"- 최소 폭/높이 기준: {min_dimension}")
    print()

    invert_svg_filtered(input_file, output_file, background_color="#288f28", min_dimension=min_dimension)

