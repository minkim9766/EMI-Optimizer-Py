"""
SVG에서 얇은 요소들을 제거하는 스크립트
- Path의 bounding box를 계산하여 너무 얇은 요소들을 필터링
"""

import re
import math


def parse_path_commands(d):
    """SVG path의 d 속성을 파싱하여 좌표들을 추출"""
    # 숫자들 추출 (음수, 소수점 포함)
    numbers = re.findall(r'-?\d+\.?\d*', d)
    coords = [float(n) for n in numbers]
    return coords


def get_path_bounding_box(d):
    """Path의 bounding box (min_x, min_y, max_x, max_y) 계산"""
    coords = parse_path_commands(d)
    if len(coords) < 2:
        return None

    # x, y 좌표 분리 (짝수 인덱스는 x, 홀수 인덱스는 y)
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
    """
    Path가 너무 얇은지 확인
    min_dimension: 최소 폭/높이 (이보다 작으면 얇은 것으로 판단)
    """
    width, height = get_path_dimensions(d)

    # 폭이나 높이가 최소 치수보다 작으면 얇은 것으로 판단
    # 단, 둘 다 0인 경우(점)도 제거
    if width < min_dimension or height < min_dimension:
        return True

    return False


def filter_thin_paths(input_file, output_file, min_dimension=0.5):
    """
    SVG 파일에서 얇은 path들을 제거

    Args:
        input_file: 입력 SVG 파일
        output_file: 출력 SVG 파일
        min_dimension: 최소 폭/높이 기준 (기본값 0.5)
    """

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # mask 태그 내의 path들만 필터링
    mask_match = re.search(r'(<mask[^>]*>)(.*?)(</mask>)', content, re.DOTALL)

    if not mask_match:
        print("마스크를 찾을 수 없습니다.")
        return

    mask_start = mask_match.group(1)
    mask_content = mask_match.group(2)
    mask_end = mask_match.group(3)

    # rect는 유지하고, path만 필터링
    rect_match = re.search(r'<rect[^>]*/>', mask_content)
    rect_element = rect_match.group(0) if rect_match else ""

    # 모든 path 추출
    paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', mask_content)

    filtered_count = 0
    kept_count = 0
    filtered_paths = []

    for path_d in paths:
        width, height = get_path_dimensions(path_d)

        if is_thin_path(path_d, min_dimension):
            filtered_count += 1
            # print(f"제거됨: 폭={width:.4f}, 높이={height:.4f}")
        else:
            kept_count += 1
            filtered_paths.append(f'        <path d="{path_d}" fill="black"/>')

    # 새로운 마스크 내용 생성
    new_mask_content = f'''
        <!-- 전체 영역을 흰색으로 (보이게) -->
        {rect_element}
        
        <!-- 원본 도형들을 검은색으로 (안 보이게 = 마스크에서 제외) -->
        <!-- 얇은 요소 제거됨: {filtered_count}개, 유지됨: {kept_count}개 -->
'''
    new_mask_content += '\n'.join(filtered_paths) + '\n    '

    # 원본 content에서 마스크 부분 교체
    new_content = content[:mask_match.start()] + mask_start + new_mask_content + mask_end + content[mask_match.end():]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"완료!")
    print(f"- 제거된 얇은 요소: {filtered_count}개")
    print(f"- 유지된 요소: {kept_count}개")
    print(f"- 최소 치수 기준: {min_dimension}")
    print(f"- 출력 파일: {output_file}")


if __name__ == "__main__":
    input_file = "inverted_output_mask.svg"
    output_file = "inverted_output_mask_filtered.svg"

    # 최소 치수를 0.5로 설정 (이보다 폭이나 높이가 작은 요소 제거)
    # 값을 높이면 더 많은 요소가 제거됨
    min_dimension = 0.5

    print(f"얇은 요소 필터링 중...")
    print(f"- 입력 파일: {input_file}")
    print(f"- 최소 폭/높이 기준: {min_dimension}")
    print()

    filter_thin_paths(input_file, output_file, min_dimension)

