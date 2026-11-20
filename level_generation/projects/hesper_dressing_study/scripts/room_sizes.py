#!/usr/bin/env python3
"""Room footprint statistics from data/sectors.json (one MM sector is normally one room or corridor run).

Shape classes: corridor = mean width (floor area / long side) < 640 and long side >= 2.5 x mean width;
then by floor area: small < 1 M, room 1-4 M, hall 4-8 M, huge >= 8 M units^2. Writes data/room_sizes.json.
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1] / 'data'


def shape(r):
    long_side = max(r['width'], r['depth'])
    if r['mean_width'] < 640 and long_side >= 2.5 * r['mean_width']:
        return 'corridor'
    a = r['floor_area']
    return 'small' if a < 1e6 else 'room' if a < 4e6 else 'hall' if a < 8e6 else 'huge'


def main():
    rows = [r for r in json.loads((OUT / 'sectors.json').read_text()) if r['floor_area'] > 20000]
    result = {}
    for world in ('mm6', 'mm7', 'mm8'):
        rs = [r for r in rows if r['world'] == world]
        areas = np.array([r['floor_area'] for r in rs])
        classes = Counter(shape(r) for r in rs)
        corridors = [r for r in rs if shape(r) == 'corridor']
        per_class = {}
        for c in ('small', 'room', 'hall', 'huge'):
            cs = [r for r in rs if shape(r) == c]
            if cs:
                per_class[c] = dict(count=len(cs),
                                    median_w_x_d=[float(np.median([max(r['width'], r['depth']) for r in cs])),
                                                  float(np.median([min(r['width'], r['depth']) for r in cs]))],
                                    median_height=float(np.median([r['height'] for r in cs])),
                                    multi_level_share=round(np.mean([r['floor_levels'] > 1 for r in cs]), 2),
                                    with_water_share=round(np.mean([r['fluid_share'] > 0.05 for r in cs]), 2),
                                    median_inner_vertical_faces=float(np.median([r['inner_vertical_faces'] for r in cs])),
                                    no_decoration_share=round(np.mean([r['decoration_count'] == 0 for r in cs]), 2))
        big = sorted(rs, key=lambda r: -r['floor_area'])[:15]
        result[world] = dict(
            sectors=len(rs), area_percentiles_m=(np.percentile(areas, [10, 25, 50, 75, 90, 99]) / 1e6).round(2).tolist(),
            over_2m=int((areas > 2e6).sum()), over_4m=int((areas > 4e6).sum()), over_8m=int((areas > 8e6).sum()),
            maps_with_over_8m=len({r['map'] for r in rs if r['floor_area'] > 8e6}),
            classes=dict(classes), per_class=per_class,
            corridor_width_percentiles=np.percentile([r['mean_width'] for r in corridors], [10, 25, 50, 75, 90]).tolist(),
            corridor_height_median=float(np.median([r['height'] for r in corridors])),
            biggest=[dict(map=r['map'], sector=r['sector'], area_m=round(r['floor_area'] / 1e6, 1),
                          w=r['width'], d=r['depth'], h=r['height'], levels=r['floor_levels'],
                          water=r['fluid_share'], inner_faces=r['inner_vertical_faces'],
                          decos=r['decoration_count'], top=r['top_textures']) for r in big])
    (OUT / 'room_sizes.json').write_text(json.dumps(result, indent=1))
    for w, v in result.items():
        print('==', w, {k: v[k] for k in ('sectors', 'area_percentiles_m', 'over_2m', 'over_4m', 'over_8m',
                                          'maps_with_over_8m', 'classes', 'corridor_width_percentiles',
                                          'corridor_height_median')})
        for c, s in v['per_class'].items():
            print('  ', c, s)
        for b in v['biggest'][:10]:
            print('    ', b)


if __name__ == '__main__':
    main()
