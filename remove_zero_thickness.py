"""
반전된 SVG에서 얇은 선들(틈)을 제거
방법: 얇은 path들에만 stroke를 추가하여 약간 두껍게 만들어 틈을 메움
"""

import re


def parse_path_commands(d):
    numbers = re.findall(r'-?\d+\.?\d*', d)
    coords = [float(n) for n in numbers]
    return coords


def get_path_dimensions(d):
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


def is_thin_path(d, threshold=0.5):
    """임계값보다 얇은 path인지 확인"""
    width, height = get_path_dimensions(d)
    return width < threshold or height < threshold


def add_stroke_to_thin_paths(input_file, output_file, threshold=0.5, stroke_width=0.3):
    """
    얇은 path들에만 stroke를 추가하여 틈을 메움
    """

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    thin_count = 0

    def replace_thin_path(match):
        nonlocal thin_count
        d = match.group(1)

        if is_thin_path(d, threshold):
            thin_count += 1
            # 얇은 path에만 stroke 추가
            return f'<path d="{d}" fill="black" stroke="black" stroke-width="{stroke_width}"/>'
        else:
            # 다른 path는 그대로
            return match.group(0)

    new_content = re.sub(
        r'<path d="([^"]+)" fill="black"/>',
        replace_thin_path,
        content
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"완료!")
    print(f"- stroke 추가된 얇은 path: {thin_count}개")
    print(f"- 임계값: {threshold}")
    print(f"- stroke-width: {stroke_width}")
    print(f"- 출력 파일: {output_file}")


if __name__ == "__main__":
    # 얇은 path에만 stroke 추가
    threshold = 0.5  # 폭이나 높이가 0.5 미만인 것
    stroke_width = 0.5

    add_stroke_to_thin_paths(
        "inverted_output_mask.svg",
        "inverted_output_mask_final.svg",
        threshold,
        stroke_width
    )

