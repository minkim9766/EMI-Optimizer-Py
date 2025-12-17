import re

with open('enclosed_regions.svg', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File length: {len(content)}")

match = re.search(r'<mask id="boundary-interior-mask">(.*?)</mask>', content, re.DOTALL)
if match:
    mask_content = match.group(1)
    print(f"Mask content length: {len(mask_content)}")

    path_tags = re.findall(r'<path[^>]+fill="white"[^>]*/>', mask_content)
    print(f"Found {len(path_tags)} paths with fill=white")

    if path_tags:
        print("First tag:", path_tags[0][:150])

        # d 속성 추출 테스트
        d_match = re.search(r'd="([^"]+)"', path_tags[0])
        if d_match:
            print("First d:", d_match.group(1)[:100])
else:
    print("No boundary-interior-mask found")

    # 어디까지 매칭되는지 확인
    if 'boundary-interior-mask' in content:
        print("'boundary-interior-mask' exists in file")
    else:
        print("'boundary-interior-mask' NOT in file")

