"""
inverted_output_mask.svg에서 얇은 선들만 제거하는 스크립트
- 얇은 요소들을 마스크에 추가하여 반전 결과에서 안 보이게 함
"""

import re


def parse_path_commands(d):
    """SVG path의 d 속성을 파싱하여 좌표들을 추출"""
    numbers = re.findall(r'-?\d+\.?\d*', d)
    coords = [float(n) for n in numbers]
    return coords


def get_path_dimensions(d):
    """Path의 폭과 높이 계산"""
    coords = parse_path_commands(d)
    if len(coords) < 2:
        return (0, 0)

    x_coords = coords[0::2]
    y_coords = coords[1::2]

    if not x_coords or not y_coords:
        return (0, 0)

    width = max(x_coords) - min(x_coords)
    height = max(y_coords) - min(y_coords)
    return (width, height)


def is_thin_path(d, min_dimension=0.5):
    """Path가 너무 얇은지 확인"""
    width, height = get_path_dimensions(d)
    if width < min_dimension or height < min_dimension:
        return True
    return False


def remove_thin_from_inverted(input_file, output_file, min_dimension=0.5):
    """
    반전된 SVG에서 얇은 선들을 제거
    방법: 원본 SVG에서 얇은 요소들을 찾아서 마스크에 추가
    """

    # 원본 SVG 읽기
    with open("output.svg", 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 반전된 SVG 읽기
    with open(input_file, 'r', encoding='utf-8') as f:
        inverted_content = f.read()

    # 원본에서 모든 path 추출
    original_paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', original_content)

    # 얇은 path들 찾기
    thin_paths = []
    for path_d in original_paths:
        if is_thin_path(path_d, min_dimension):
            thin_paths.append(path_d)

    print(f"원본에서 찾은 얇은 요소: {len(thin_paths)}개")

    # 반전된 SVG의 마스크에 얇은 요소들 추가
    # 마스크에 검은색으로 추가하면 그 부분이 안 보이게 됨

    # </mask> 태그 찾기
    mask_end_pos = inverted_content.find('    </mask>')

    if mask_end_pos == -1:
        print("마스크를 찾을 수 없습니다.")
        return

    # 얇은 요소들을 마스크에 추가할 문자열 생성
    thin_paths_str = "\n        <!-- 얇은 요소들 (반전 결과에서 제거됨) -->\n"
    for path_d in thin_paths:
        thin_paths_str += f'        <path d="{path_d}" fill="black"/>\n'

    # 마스크 끝 바로 앞에 삽입
    new_content = inverted_content[:mask_end_pos] + thin_paths_str + inverted_content[mask_end_pos:]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"완료!")
    print(f"- 제거된 얇은 요소: {len(thin_paths)}개")
    print(f"- 최소 치수 기준: {min_dimension}")
    print(f"- 출력 파일: {output_file}")


if __name__ == "__main__":
    input_file = "inverted_output_mask.svg"
    output_file = "inverted_output_mask_clean.svg"

    # 최소 치수 설정 (더 큰 값 = 더 많이 제거)
    min_dimension = 1.5

    print(f"반전된 SVG에서 얇은 선 제거 중...")
    print(f"- 입력 파일: {input_file}")
    print(f"- 최소 폭/높이 기준: {min_dimension}")
    print()

    remove_thin_from_inverted(input_file, output_file, min_dimension)

