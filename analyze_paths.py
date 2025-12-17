"""
원본 SVG에서 path 크기 분포 분석
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

# 원본 SVG 읽기
with open("output.svg", 'r', encoding='utf-8') as f:
    content = f.read()

paths = re.findall(r'<path[^>]*d="([^"]+)"[^>]*/>', content)

# 크기별로 분류
sizes = []
for path_d in paths:
    width, height = get_path_dimensions(path_d)
    min_dim = min(width, height)
    sizes.append((min_dim, width, height, path_d[:50]))

# 정렬
sizes.sort(key=lambda x: x[0])

print(f"총 path 개수: {len(sizes)}")
print("\n=== 가장 얇은 path들 (상위 30개) ===")
for i, (min_dim, w, h, d) in enumerate(sizes[:30]):
    print(f"{i+1:3}. min={min_dim:.4f}, 폭={w:.4f}, 높이={h:.4f} | {d}...")

print("\n=== 크기 분포 ===")
ranges = [0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 1.5, 2.0]
for i in range(len(ranges)-1):
    count = sum(1 for s in sizes if ranges[i] <= s[0] < ranges[i+1])
    print(f"{ranges[i]:.2f} ~ {ranges[i+1]:.2f}: {count}개")
count = sum(1 for s in sizes if s[0] >= 2.0)
print(f"2.0 이상: {count}개")

