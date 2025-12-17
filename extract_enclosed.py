"""
반전된 SVG (inverted_output_mask.svg)에서 둘러싸인 부분만 추출하는 스크립트
- 반전 결과에서 보이는 영역(빈 공간) 중, 경계와 연결되지 않은 영역만 추출
- 경계에 닿는 빈 공간은 제거
"""

import re


def parse_path_commands(d):
    """SVG path의 d 속성을 파싱하여 좌표들을 추출"""
    numbers = re.findall(r'-?\d+\.?\d*', d)
    coords = [float(n) for n in numbers]
    return coords


def get_path_bbox(d):
    """path의 bounding box 반환"""
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
    bbox = get_path_bbox(d)
    if bbox is None:
        return (0, 0)

    min_x, min_y, max_x, max_y = bbox
    return (max_x - min_x, max_y - min_y)


def is_closed_path(d):
    """path가 폐곡선인지 확인 (Z로 끝나는지)"""
    return d.strip().upper().endswith('Z')


def is_thin_path(d, threshold=0.5):
    """얇은 path인지 확인"""
    width, height = get_path_dimensions(d)
    return width < threshold or height < threshold


def bbox_touches_boundary(bbox, vb_x, vb_y, vb_width, vb_height, margin=0.5):
    """bbox가 SVG 경계에 닿는지 확인"""
    min_x, min_y, max_x, max_y = bbox

    if min_x <= vb_x + margin:
        return True
    if min_y <= vb_y + margin:
        return True
    if max_x >= vb_x + vb_width - margin:
        return True
    if max_y >= vb_y + vb_height - margin:
        return True

    return False


def extract_enclosed_from_inverted(input_file, output_file, background_color="#288f28"):
    """
    반전된 SVG에서 둘러싸인 영역만 추출

    핵심 로직:
    - 반전 결과에서 "빈 공간"은 원본 도형들 사이의 틈
    - 이 틈이 SVG 경계와 연결되어 있으면 = 외부와 연결됨 → 제거
    - 경계와 연결되지 않은 틈 = 둘러싸인 영역 → 유지

    구현:
    - 경계에 닿는 도형들(boundary_paths)을 찾음
    - 이 도형들 "바깥쪽" 빈 공간은 외부와 연결됨
    - 경계에 닿지 않는 도형들(enclosed_paths) "안쪽" 빈 공간만 둘러싸인 영역
    """

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # viewBox와 dimensions 추출
    viewbox_match = re.search(r'viewBox="([^"]+)"', content)
    width_match = re.search(r'width="([^"]+)"', content)
    height_match = re.search(r'height="([^"]+)"', content)

    if viewbox_match:
        vb_parts = viewbox_match.group(1).split()
        vb_x, vb_y, vb_width, vb_height = float(vb_parts[0]), float(vb_parts[1]), float(vb_parts[2]), float(vb_parts[3])
    else:
        vb_x, vb_y, vb_width, vb_height = 0, 0, 100, 100

    width = width_match.group(1) if width_match else str(vb_width)
    height = height_match.group(1) if height_match else str(vb_height)

    # 마스크 내의 모든 path 추출
    paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', content)
    circles = re.findall(r'<circle[^>]*cx="([^"]+)"[^>]*cy="([^"]+)"[^>]*r="([^"]+)"[^>]*/>', content)

    print(f"총 path 개수: {len(paths)}")
    print(f"총 circle 개수: {len(circles)}")

    # 유효한 path들 (폐곡선, 얇지 않음)
    valid_paths = []
    for path_d in paths:
        if is_closed_path(path_d) and not is_thin_path(path_d, 0.3):
            bbox = get_path_bbox(path_d)
            if bbox:
                valid_paths.append((path_d, bbox))

    print(f"유효한 path 개수: {len(valid_paths)}")

    # 경계에 닿는 path들 찾기 (이것들이 둘러싸는 외곽 도형들)
    boundary_paths = []
    inner_paths = []

    for path_d, bbox in valid_paths:
        if bbox_touches_boundary(bbox, vb_x, vb_y, vb_width, vb_height, margin=0.5):
            boundary_paths.append((path_d, bbox))
        else:
            inner_paths.append((path_d, bbox))

    print(f"경계에 닿는 path (외곽): {len(boundary_paths)}개")
    print(f"경계에 안 닿는 path (내부): {len(inner_paths)}개")

    # SVG 생성
    # 방법: 전체 반전 결과에서, 경계에 닿는 도형들 "내부"의 빈 공간만 표시
    # = 경계 도형들이 감싸고 있는 영역에서 원본 도형들을 제외한 부분

    svg_output = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="{vb_x} {vb_y} {vb_width} {vb_height}">
<defs>
    <!-- 마스크1: 원본 도형들 가리기 (반전) -->
    <mask id="invert-mask">
        <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" fill="white"/>
'''

    for path_d in paths:
        svg_output += f'        <path d="{path_d}" fill="black"/>\n'

    for cx, cy, r in circles:
        svg_output += f'        <circle cx="{cx}" cy="{cy}" r="{r}" fill="black"/>\n'

    svg_output += f'''    </mask>
    
    <!-- 마스크2: 경계에 닿는 도형들의 내부 영역만 선택 -->
    <mask id="boundary-interior-mask">
        <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" fill="black"/>
'''

    # 경계에 닿는 도형들을 흰색으로 (이 도형들 내부가 둘러싸인 영역)
    for path_d, bbox in boundary_paths:
        svg_output += f'        <path d="{path_d}" fill="white"/>\n'

    svg_output += f'''    </mask>
</defs>

<!-- 경계 도형들 내부의 빈 공간만 표시 -->
<g mask="url(#boundary-interior-mask)">
    <rect x="{vb_x}" y="{vb_y}" width="{vb_width}" height="{vb_height}" 
          fill="{background_color}" mask="url(#invert-mask)"/>
</g>
</svg>'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_output)

    print(f"완료! 출력 파일: {output_file}")


if __name__ == "__main__":
    input_file = "inverted_output_mask.svg"
    output_file = "enclosed_regions.svg"

    extract_enclosed_from_inverted(input_file, output_file, background_color="#288f28")

