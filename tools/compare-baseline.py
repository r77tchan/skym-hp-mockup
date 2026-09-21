#!/usr/bin/env python3
"""Compare full-page baseline PNGs, including header and footer. Prints JSON."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('directory', type=Path)
p.add_argument('--version', default='draft', help='draft (per-page config) or frozen version')
a = p.parse_args()
cfg = json.loads((Path(__file__).parent / 'live-baseline.json').read_text())
report = []
for page, info in cfg['pages'].items():
    version = info['draft'] if a.version == 'draft' else a.version
    for width in [375, 400, 820, 1280, 1455]:
        paths = [a.directory / f'final-{page}-{name}-{width}.png' for name in [version, 'live']]
        ref, live = [Image.open(path).convert('RGB') for path in paths]
        assert ref.size == live.size, (page, width, ref.size, live.size)
        channels = ImageChops.difference(ref, live).split()
        delta = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        hist = delta.histogram()
        report.append({'page': page, 'width': width, 'size': ref.size,
                       'nonzero': sum(hist[1:]), 'over3': sum(hist[4:]),
                       'max': delta.getextrema()[1],
                       'bboxOver3': delta.point(lambda x: 255 if x > 3 else 0).getbbox()})
print(json.dumps(report, indent=2))
