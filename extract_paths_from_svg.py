import xml.etree.ElementTree as ET
import re

INPUT_SVG = 'cutting_inverted_output_mask.svg'
OUTPUT_SVG = 'extracted_paths.svg'

def extract_all_paths(input_svg, output_svg):
    tree = ET.parse(input_svg)
    root = tree.getroot()

    # 네임스페이스 처리
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', ns['svg'])

    # 새 루트 생성 (원본 속성 복사)
    new_root = ET.Element(root.tag, root.attrib)

    # defs, style 등 복사
    for child in root:
        tag = child.tag
        if tag.startswith('{'):
            tag = tag.split('}', 1)[1]
        if tag in ['defs', 'style']:
            new_root.append(child)

    # 모든 path 추출 (재귀)
    def find_paths(parent):
        for elem in parent:
            tag = elem.tag
            if tag.startswith('{'):
                tag = tag.split('}', 1)[1]
            if tag == 'path':
                # 속성 복사
                new_elem = ET.Element(elem.tag, elem.attrib)
                new_root.append(new_elem)
            if len(elem):
                find_paths(elem)
    find_paths(root)

    # 저장
    new_tree = ET.ElementTree(new_root)
    new_tree.write(output_svg, encoding='utf-8', xml_declaration=True)
    print(f'총 추출된 path 개수: {len(new_root.findall(".//{http://www.w3.org/2000/svg}path"))}')
    print(f'결과 파일: {output_svg}')

if __name__ == '__main__':
    extract_all_paths(INPUT_SVG, OUTPUT_SVG)
    print('SVG path 추출 완료.')

