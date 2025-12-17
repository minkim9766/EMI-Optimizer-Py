import xml.etree.ElementTree as ET
import re
import math

def parse_path_points(d):
    # M x1,y1 L x2,y2 L x3,y3 L x4,y4 Z 형태만 파싱
    # 쉼표/공백 구분, 소수점 등 모두 허용
    d = d.replace(',', ' ')
    nums = re.findall(r'[-+]?[0-9]*\.?[0-9]+', d)
    if len(nums) < 8:
        return None
    # 4쌍의 (x, y) 좌표
    points = [(float(nums[i]), float(nums[i+1])) for i in range(0, 8, 2)]
    return points

def is_thin_rectangle_path(d, height=0.4064, tol=0.01):
    points = parse_path_points(d)
    if not points or len(points) != 4:
        return False
    def dist(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])
    # 네 변의 길이 중 하나라도 height±tol 이내면 삭제
    edges = [dist(points[i], points[(i+1)%4]) for i in range(4)]
    for edge in edges:
        if abs(edge - height) < tol:
            return True
    return False

def normalize_d(d):
    # 쉼표를 공백으로, 여러 공백을 하나로, 소수점 6자리로 통일
    d = d.replace(',', ' ')
    d = re.sub(r'\s+', ' ', d)
    # 숫자만 소수점 6자리로 변환
    def repl(m):
        return f"{float(m.group(0)):.6f}"
    d = re.sub(r"[0-9]+\.[0-9]+", repl, d)
    return d.strip()

# 입력 SVG 파일과 출력 SVG 파일 경로
input_svg = 'cutting_inverted_output_mask.svg'
output_svg = 'cutted_inverted_output_mask.svg'

# 삭제하고 싶은 path의 d 속성 값 리스트 (정확히 일치해야 삭제)
REMOVE_PATH_D = [
    "M 87.78240000,22.06726000 L 87.78240000,22.47366000 L 60.72810000,22.47366000 L 60.72810000,22.06726000 Z"
]
REMOVE_PATH_D_NORM = [normalize_d(d) for d in REMOVE_PATH_D]

def is_height_406px(height_str):
    # '0.406', '0.406px', '0.4060', '0.406000', '0.406 px' 등 다양한 경우 처리
    if height_str is None:
        return False
    # 숫자만 추출 (단위, 공백 등 제거)
    match = re.search(r"([0-9.]+)", height_str)
    if match:
        try:
            return abs(float(match.group(1)) - 0.406) < 1e-3
        except ValueError:
            return False
    return False

def split_svg_objects(input_path, output_path):
    tree = ET.parse(input_path)
    root = tree.getroot()

    # SVG 네임스페이스 처리
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', ns['svg'])

    # 새로운 루트 생성 (원본의 속성 복사)
    new_root = ET.Element(root.tag, root.attrib)

    # 스타일, defs 등 중요한 하위 요소 복사
    for child in root:
        tag = child.tag
        if tag.startswith('{'):
            tag = tag.split('}', 1)[1]
        if tag in ['defs', 'style']:
            new_root.append(child)

    removed_rects = []
    kept_rects = []
    removed_paths = []
    kept_paths = []
    def expand_rect(elem, expand=0.152):
        x = float(elem.attrib.get('x', '0')) - expand
        y = float(elem.attrib.get('y', '0')) - expand
        width = float(elem.attrib.get('width', '0')) + 2*expand
        height = float(elem.attrib.get('height', '0')) + 2*expand
        elem.attrib['x'] = str(x)
        elem.attrib['y'] = str(y)
        elem.attrib['width'] = str(width)
        elem.attrib['height'] = str(height)

    def expand_points(points, expand=0.152):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        # bounding box 확장
        min_x -= expand
        max_x += expand
        min_y -= expand
        max_y += expand
        # 각 점이 원래 bounding box에서 어디에 있었는지에 따라 확장
        expanded = []
        for x, y in points:
            new_x = min_x if abs(x - min(xs)) < 1e-6 else max_x
            new_y = min_y if abs(y - min(ys)) < 1e-6 else max_y
            expanded.append((new_x, new_y))
        return expanded

    def points_to_path_d(points):
        return 'M ' + ' L '.join(f'{x:.8f},{y:.8f}' for x, y in points) + ' Z'

    def expand_polygon_points(points, expand=0.152):
        # polygon/polyline도 bounding box 확장
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_x -= expand
        max_x += expand
        min_y -= expand
        max_y += expand
        expanded = []
        for x, y in points:
            new_x = min_x if abs(x - min(xs)) < 1e-6 else max_x
            new_y = min_y if abs(y - min(ys)) < 1e-6 else max_y
            expanded.append((new_x, new_y))
        return expanded

    def parse_polygon_points(points_str):
        # 'x1,y1 x2,y2 ...' 또는 'x1,y1,x2,y2,...'
        points = []
        for pair in re.findall(r'[-+]?[0-9]*\.?[0-9]+,[-+]?[0-9]*\.?[0-9]+', points_str):
            x, y = map(float, pair.split(','))
            points.append((x, y))
        return points

    def stretch_y_points(points, factor=3.0):
        ys = [p[1] for p in points]
        cy = sum(ys) / len(ys)
        return [(x, cy + (y - cy) * factor) for x, y in points]

    def stretch_rect_y(elem, factor=3.0):
        y = float(elem.attrib.get('y', '0'))
        height = float(elem.attrib.get('height', '0'))
        cy = y + height / 2
        new_height = height * factor
        new_y = cy - new_height / 2
        elem.attrib['y'] = str(new_y)
        elem.attrib['height'] = str(new_height)

    # 모든 path, polygon, polyline, rect를 그룹 내부까지 재귀적으로 추출
    def extract_shapes(parent):
        for elem in parent:
            tag = elem.tag
            if tag.startswith('{'):
                tag = tag.split('}', 1)[1]
            # rect의 height가 0.406px(오차 허용)이면 건너뜀
            if tag == 'rect':
                height_val = elem.attrib.get('height')
                if is_height_406px(height_val):
                    removed_rects.append(height_val)
                    continue
                else:
                    kept_rects.append(height_val)
            # path의 d 속성이 삭제 대상이면 건너뜀
            if tag == 'path':
                d_val = elem.attrib.get('d', '').strip()
                d_norm = normalize_d(d_val)
                if d_norm in REMOVE_PATH_D_NORM or is_thin_rectangle_path(d_val, height=0.4064, tol=0.01):
                    removed_paths.append(d_val)
                    continue
                else:
                    kept_paths.append(d_val)
            if tag in ['path', 'polygon', 'polyline', 'rect']:
                # 속성 복사
                new_elem = ET.Element(elem.tag, elem.attrib)
                new_root.append(new_elem)
            # 그룹 내부도 재귀적으로 탐색
            if len(elem):
                extract_shapes(elem)
    extract_shapes(root)

    # 트리 저장
    new_tree = ET.ElementTree(new_root)
    new_tree.write(output_path, encoding='utf-8', xml_declaration=True)

    print(f"제거된 rect height 값: {removed_rects}")
    print(f"남은 rect height 값: {kept_rects}")
    print(f"제거된 rect 개수: {len(removed_rects)}")
    print(f"남은 rect 개수: {len(kept_rects)}")
    print(f"제거된 얇은 사각형 path d 값: {removed_paths}")
    print(f"제거된 얇은 사각형 path 개수: {len(removed_paths)}")

if __name__ == '__main__':
    split_svg_objects(input_svg, output_svg)
    print(f'분리된 객체로 저장 완료: {output_svg}')
