#!/usr/bin/env python3
"""Compare QA PNGs with their measured footer boundary; never alters references."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
data = json.loads((a.directory / 'final-metrics.json').read_text())
report = []
for page, metrics in data.items():
    for i in range(0, len(metrics['raw']), 2):
        ref, live = metrics['raw'][i:i+2]
        width = ref['width']
        bottom = int(next(n['y'] for n in ref['nodes'] if n['s'] == '.l-footer:0'))
        imgs = [Image.open(a.directory / f'final-{page}-{name}-{width}.png').convert('RGB') for name in ['v01', 'live']]
        channels = ImageChops.difference(imgs[0].crop((0, 0, imgs[0].width, bottom)), imgs[1].crop((0, 0, imgs[1].width, bottom))).split()
        d = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        regions = {'header': d.crop((0, 0, d.width, 50)), 'body': d.crop((0, 50, d.width, bottom))}
        stats = {}
        for label, values in regions.items():
            hist = values.histogram()
            bbox = values.point(lambda x: 255 if x > 3 else 0).getbbox()
            if bbox and label == 'body':
                bbox = (bbox[0], bbox[1] + 50, bbox[2], bbox[3] + 50)
            stats[label] = {'nonzero': sum(hist[1:]), 'over3': sum(hist[4:]), 'max': values.getextrema()[1], 'bboxOver3': bbox}
        report.append({'page': page, 'width': width, 'bottom': bottom, **stats})
print(json.dumps(report, indent=2))
