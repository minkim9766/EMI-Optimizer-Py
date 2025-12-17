import argparse
import re
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw


SVG_NS = "{http://www.w3.org/2000/svg}"


def strip_ns(tag):
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def parse_floats(s):
    if s is None:
        return []
    s = s.replace(",", " ")
    parts = [p for p in s.split() if p]
    out = []
    for p in parts:
        try:
            out.append(float(p))
        except ValueError:
            pass
    return out


def parse_viewbox(root):
    vb = root.get("viewBox") or root.get("viewbox")
    if not vb:
        return None
    nums = parse_floats(vb)
    if len(nums) == 4:
        return nums[0], nums[1], nums[2], nums[3]
    return None


def parse_size(value, fallback):
    if value is None:
        return fallback
    s = str(value).strip()
    m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*([a-zA-Z%]*)\s*$", s)
    if not m:
        return fallback
    num = float(m.group(1))
    unit = m.group(2).lower()
    if unit in ["", "px"]:
        return int(round(num))
    if unit == "pt":
        return int(round(num * 96.0 / 72.0))
    if unit == "mm":
        return int(round(num * 96.0 / 25.4))
    if unit == "cm":
        return int(round(num * 96.0 / 2.54))
    if unit == "in":
        return int(round(num * 96.0))
    return fallback


def get_canvas(root, width, height):
    w = parse_size(root.get("width"), None)
    h = parse_size(root.get("height"), None)

    if width is not None:
        w = width
    if height is not None:
        h = height

    vb = parse_viewbox(root)
    if (w is None or h is None) and vb is not None:
        _, _, vb_w, vb_h = vb
        if w is None and h is None:
            w = int(round(vb_w))
            h = int(round(vb_h))
        elif w is None:
            w = int(round(h * vb_w / vb_h))
        elif h is None:
            h = int(round(w * vb_h / vb_w))

    if w is None:
        w = 1024
    if h is None:
        h = 1024

    if vb is None:
        vb = (0.0, 0.0, float(w), float(h))

    return int(w), int(h), vb


def map_point(x, y, vb, out_w, out_h):
    vb_x, vb_y, vb_w, vb_h = vb
    px = (x - vb_x) / vb_w * out_w
    py = (y - vb_y) / vb_h * out_h
    return px, py


def draw_polygon(draw, points, vb, out_w, out_h, fill=255):
    if len(points) < 3:
        return
    mapped = [map_point(points[i], points[i + 1], vb, out_w, out_h) for i in range(0, len(points), 2)]
    draw.polygon(mapped, fill=fill)


def draw_polyline(draw, points, vb, out_w, out_h, width=1, fill=255):
    if len(points) < 4:
        return
    mapped = [map_point(points[i], points[i + 1], vb, out_w, out_h) for i in range(0, len(points), 2)]
    draw.line(mapped, fill=fill, width=width)


def draw_rect(draw, el, vb, out_w, out_h, fill=255):
    x = float(el.get("x") or 0.0)
    y = float(el.get("y") or 0.0)
    w = float(el.get("width") or 0.0)
    h = float(el.get("height") or 0.0)
    p1 = map_point(x, y, vb, out_w, out_h)
    p2 = map_point(x + w, y + h, vb, out_w, out_h)
    draw.rectangle([p1, p2], fill=fill)


def draw_circle(draw, el, vb, out_w, out_h, fill=255):
    cx = float(el.get("cx") or 0.0)
    cy = float(el.get("cy") or 0.0)
    r = float(el.get("r") or 0.0)
    p1 = map_point(cx - r, cy - r, vb, out_w, out_h)
    p2 = map_point(cx + r, cy + r, vb, out_w, out_h)
    draw.ellipse([p1, p2], fill=fill)


def draw_ellipse(draw, el, vb, out_w, out_h, fill=255):
    cx = float(el.get("cx") or 0.0)
    cy = float(el.get("cy") or 0.0)
    rx = float(el.get("rx") or 0.0)
    ry = float(el.get("ry") or 0.0)
    p1 = map_point(cx - rx, cy - ry, vb, out_w, out_h)
    p2 = map_point(cx + rx, cy + ry, vb, out_w, out_h)
    draw.ellipse([p1, p2], fill=fill)


def draw_line(draw, el, vb, out_w, out_h, width=1, fill=255):
    x1 = float(el.get("x1") or 0.0)
    y1 = float(el.get("y1") or 0.0)
    x2 = float(el.get("x2") or 0.0)
    y2 = float(el.get("y2") or 0.0)
    p1 = map_point(x1, y1, vb, out_w, out_h)
    p2 = map_point(x2, y2, vb, out_w, out_h)
    draw.line([p1, p2], fill=fill, width=width)


def path_tokens(d):
    d = d.replace(",", " ")
    return re.findall(r"[MmLlHhVvZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?", d)


def draw_path_simple(draw, el, vb, out_w, out_h, fill=255):
    d = el.get("d")
    if not d:
        return
    toks = path_tokens(d)
    i = 0
    cmd = None
    x = 0.0
    y = 0.0
    start = None
    pts = []

    def flush_polygon():
        nonlocal pts
        if len(pts) >= 6:
            draw_polygon(draw, pts, vb, out_w, out_h, fill=fill)
        pts = []

    while i < len(toks):
        t = toks[i]
        if re.match(r"^[MmLlHhVvZz]$", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                if start is not None:
                    pts.extend([start[0], start[1]])
                flush_polygon()
                start = None
            continue

        if cmd is None:
            i += 1
            continue

        if cmd in "Mm":
            nx = float(toks[i])
            ny = float(toks[i + 1])
            i += 2
            x, y = nx, ny
            start = (x, y)
            pts.extend([x, y])
            cmd = "L" if cmd == "M" else "l"
            continue

        if cmd in "Ll":
            nx = float(toks[i])
            ny = float(toks[i + 1])
            i += 2
            x, y = nx, ny
            pts.extend([x, y])
            continue

        if cmd in "Hh":
            nx = float(toks[i])
            i += 1
            x = nx
            pts.extend([x, y])
            continue

        if cmd in "Vv":
            ny = float(toks[i])
            i += 1
            y = ny
            pts.extend([x, y])
            continue

        i += 1

    flush_polygon()


def build_mask(svg_path, out_path, width=None, height=None, stroke_width=2, invert=True):
    data = open(svg_path, "rb").read()
    root = ET.fromstring(data)

    out_w, out_h, vb = get_canvas(root, width, height)

    mask = Image.new("L", (out_w, out_h), 0)
    draw = ImageDraw.Draw(mask)

    for el in root.iter():
        tag = strip_ns(el.tag)

        if tag == "polygon":
            pts = parse_floats(el.get("points"))
            draw_polygon(draw, pts, vb, out_w, out_h, fill=255)

        elif tag == "polyline":
            pts = parse_floats(el.get("points"))
            draw_polyline(draw, pts, vb, out_w, out_h, width=stroke_width, fill=255)

        elif tag == "rect":
            draw_rect(draw, el, vb, out_w, out_h, fill=255)

        elif tag == "circle":
            draw_circle(draw, el, vb, out_w, out_h, fill=255)

        elif tag == "ellipse":
            draw_ellipse(draw, el, vb, out_w, out_h, fill=255)

        elif tag == "line":
            draw_line(draw, el, vb, out_w, out_h, width=stroke_width, fill=255)

        elif tag == "path":
            draw_path_simple(draw, el, vb, out_w, out_h, fill=255)

    if invert:
        mask = Image.eval(mask, lambda p: 255 - p)

    mask.save(out_path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("svg")
    p.add_argument("out")
    p.add_argument("--width", type=int, default=None)
    p.add_argument("--height", type=int, default=None)
    p.add_argument("--stroke_width", type=int, default=2)
    p.add_argument("--no_invert", action="store_true")
    args = p.parse_args()

    build_mask(
        svg_path=args.svg,
        out_path=args.out,
        width=args.width,
        height=args.height,
        stroke_width=args.stroke_width,
        invert=(not args.no_invert),
    )


if __name__ == "__main__":
    main()
