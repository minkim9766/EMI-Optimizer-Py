from __future__ import annotations
from pygerber.gerberx3.api.v2 import GerberFile
from xml.dom import minidom
from svg.path import parse_path
from svg.path.path import Line


# GerberFile.from_file('./assets/Seven segment display gerber/processed/B_Cu.gbr').parse().render_svg("output.svg")

doc = minidom.parse('output.svg')  # parseString also exists
path_strings = [path.getAttribute('d') for path
                in doc.getElementsByTagName('path')]
doc.unlink()

for path_string in path_strings:
    path = parse_path(path_string)
    for e in path:
        if isinstance(e, Line):
            x0 = e.start.real
            y0 = e.start.imag
            x1 = e.end.real
            y1 = e.end.imag
            print("(%.2f, %.2f) - (%.2f, %.2f)" % (x0, y0, x1, y1))