"""Source-owned southern chapterhouse seating and two unequal planted pockets.

The central approach and snapped fork stay open. Lesson furniture remains indoors.
All stone courses and bench feet reach the actual native terrain triangles.
"""
import json
import math

from author_props import ground_at


PLANTS = [
    [-2470, -710], [-2390, -650], [-2470, -570], [-2380, -475], [-2480, -450],
    [-1950, -570], [-1830, -565], [-1680, -580], [-1910, -450], [-1780, -450],
    [-1660, -450], [-1750, -570],
]
APPROACH = [-2300, -1120, -2050, 154]
BENCH = [-2480, -200]
# Partial, unequal edging, not two fenced rectangles. Coordinates are world XY.
EDGES = [
    [-2540, -786, -2424, -762], [-2418, -786, -2336, -762],
    [-2550, -750, -2526, -634], [-2550, -628, -2526, -512],
    [-2000, -664, -1852, -640], [-1846, -664, -1710, -640],
    [-1704, -664, -1596, -640], [-1590, -630, -1566, -522],
]


def author_court(author, spec, project):
    height = (project/'landscape/heightmap.raw').read_bytes()
    chapter = next(b for b in spec['buildings'] if b['id']=='monks_s')
    palette = {**spec['palettes']['working_props'], 'stone': spec['palettes'][chapter['palette']]['stone']}
    records = []
    for name, origin, kind in [('chapter_court_bench', BENCH, 'bench'),
                               ('chapter_court_edging', [-2058, -624], 'edging')]:
        pad = math.ceil(ground_at(height, origin)/32)*32
        prop = {'id': name, 'semanticId': 'mm5:castleview/'+name, 'owner': 'monks_s',
                'title': 'Chapterhouse garden '+kind, 'frontOrigin': origin,
                'frontOutward': [0, -1], 'frontTangent': [1, 0], 'padHeight': pad,
                'palette': 'working_props', 'behavior': 'inert architectural scenery',
                'materialKeys': palette,
                'radius': 150 if kind == 'bench' else 520,
                'purpose': 'Shared outdoor quiet court; preserve direct southern door approach',
                'solidFootprints': [], 'groundSupports': []}
        panels = []

        def box(bounds, material='wood', fitted=False):
            x0, y0, z0, x1, y1, z1 = bounds
            polygon = [[origin[0]+x, origin[1]+y] for x, y in
                       [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
            samples = [ground_at(height, point) for point in polygon]
            if fitted:
                z0 = min(samples)-pad-16
                prop['groundSupports'].append({'footprint': polygon, 'groundRange': [min(samples), max(samples)],
                                               'bottom': pad+z0, 'top': pad+z1})
                prop['solidFootprints'].append(polygon)
            author.box(panels, [x0, y0, z0, x1, y1, z1], palette[material])

        if kind == 'bench':
            for y in [-32, -9, 14]:
                box([-144, y, 64, 144, y+20, 80])
            for x in [-108, 84]:
                box([x, -26, 0, x+24, 30, 64], fitted=True)
                box([x, 22, 64, x+24, 38, 160])
            box([-144, 26, 110, 144, 42, 138])
            prop['solidFootprints'] = [[[origin[0]+x, origin[1]+y] for x, y in
                                        [(-144, -32), (144, -32), (144, 42), (-144, 42)]]]
        else:
            for x0, y0, x1, y1 in EDGES:
                top = max(ground_at(height, [x, y]) for x in [x0, x1] for y in [y0, y1])+24
                box([x0-origin[0], y0-origin[1], 0, x1-origin[0], y1-origin[1], top-pad],
                    'stone', fitted=True)
        author.model(name, panels, prop)
        author.semantic['props'].append(prop)
        records.append(prop)
    (project/'implementation/chapter_court.json').write_text(json.dumps({
        'owner': 'monks_s', 'plantPositions': PLANTS, 'clearApproach': APPROACH,
        'props': records, 'status': 'Authored source; native visual acceptance pending',
        'design': 'One south-facing bench, five western and seven eastern plants, low partial stone edging. '
                  'Both road branches and the direct chapterhouse approach remain unfurnished.',
    }, indent=2)+'\n')
