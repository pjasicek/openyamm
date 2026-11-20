"""Lay out generated minimap concepts with editable region/anchor labels in SVG.

The raster art is generated separately. This module composes atlas pages and viewport previews;
it does not paint, repair or synthesize the underlying images.
"""

from PIL import Image

from build_world_layout import HERE, LAYOUT, svgHeader, svgText, writeSvg


CONCEPTS = HERE / 'concepts'
SKY_FILE = CONCEPTS / 'sky_minimap_v2.png'
PLANES_FILE = CONCEPTS / 'elemental_minimaps_v1.png'


def previewViewport(path, imagePath, viewBox, imageSize):
    x, y, width, height = viewBox
    iw, ih = imageSize
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'xmlns:xlink="http://www.w3.org/1999/xlink" width="384" height="384" '
             f'viewBox="{x} {y} {width} {height}">',
             f'<image width="{iw}" height="{ih}" xlink:href="{imagePath}"/>']
    # Rasterize this viewport for embedding: SVG-as-image mode cannot load nested external images reliably.
    writeSvg(str(path.relative_to(HERE).with_suffix('')), parts, 384, 384)


def conceptsReady():
    for path in [SKY_FILE, PLANES_FILE]:
        if not path.is_file():
            raise FileNotFoundError(f'Generate and review the minimap concept before building the atlas: {path}')


def viewportPreviews(manifest):
    conceptsReady()
    with Image.open(SKY_FILE) as im:
        sw, sh = im.size
    with Image.open(PLANES_FILE) as im:
        pw, ph = im.size
    assert abs(sw/sh - 1.5) < .01, 'Sky concept must preserve the 3:2 world footprint'
    assert pw == ph, 'Elemental concept sheet must contain four equal square panels'
    planeIndex = {'fire': 0, 'air': 1, 'earth': 2, 'water': 3}
    for item in manifest:
        item['sourcePreview'] = item['preview']
        if item['layer'] == 'sky':
            region = next(r for r in LAYOUT['regions'] if item['id'] == 'sky_'+r['id'])
            target = CONCEPTS / (item['id']+'.svg')
            previewViewport(target, SKY_FILE.name,
                            (region['column']*sw/3, region['row']*sh/2, sw/3, sh/2), (sw, sh))
        elif item['layer'] == 'plane':
            index = planeIndex[item['id'].split('_')[1]]
            target = CONCEPTS / (item['id']+'.svg')
            previewViewport(target, PLANES_FILE.name,
                            ((index%2)*pw/2, (index//2)*ph/2, pw/2, ph/2), (pw, ph))
        else:
            continue
        item['preview'] = str(target.with_suffix('.png').relative_to(HERE))
        item['editablePreview'] = str(target.relative_to(HERE))
        item['previewKind'] = 'generated_minimap_concept'
    return manifest


def renderConceptSheets():
    conceptsReady()
    width, height = 1616, 1204
    parts = svgHeader(width, height)
    parts += [svgText(40, 37, 'DARKSIDE OF XEEN — SKYROAD MINIMAP CONCEPT', 24),
              svgText(40, 65, 'MM8 Plane of Air / MM7 Celeste visual references · six corresponding regions', 15, '#b9c4c8'),
              '<g transform="translate(40 90)">',
              f'<image xlink:href="concepts/{SKY_FILE.name}" width="1536" height="1024"/>']
    for region in LAYOUT['regions']:
        x, y = region['column']*512, region['row']*512
        parts += [f'<rect x="{x}" y="{y}" width="512" height="512" fill="none" '
                  'stroke="#dfc785" stroke-width="1.5" opacity=".75"/>',
                  f'<rect x="{x+12}" y="{y+12}" width="80" height="28" fill="#111820" opacity=".85"/>',
                  svgText(x+22, y+32, 'Sky '+region['id'].upper(), 16)]
    parts += ['</g>', svgText(40, 1145, 'Proposed architectural/cloud treatment over the source route arrangement; exact native geometry is still to be authored.', 13, '#b9c4c8'),
              svgText(40, 1171, 'Open gaps remain meaningful. Source schematics and directed transitions are retained separately for topology review.', 13, '#b9c4c8')]
    writeSvg('sky_map', parts, width, height)

    parts = svgHeader(1380, 1490)
    parts += [svgText(40, 37, 'MM5 — ELEMENTAL PLANE MINIMAP CONCEPTS', 24),
              svgText(40, 65, 'Authored relief and landmark settings around original event anchors', 15, '#b9c4c8'),
              '<image x="40" y="90" width="1300" height="1300" xlink:href="concepts/elemental_minimaps_v1.png"/>']
    for index, name in enumerate(['Fire', 'Air', 'Earth', 'Water']):
        x, y = 40+(index%2)*650, 90+(index//2)*650
        parts += [f'<rect x="{x}" y="{y}" width="650" height="650" fill="none" stroke="#dfc785" stroke-width="1.5"/>',
                  f'<rect x="{x+12}" y="{y+12}" width="115" height="32" fill="#111820" opacity=".9"/>',
                  svgText(x+24, y+35, name.upper(), 19)]
    parts += [svgText(40, 1422, 'The original planes have nearly uniform terrain; these landforms/platforms are proposed adaptation, not extracted geometry.', 13, '#b9c4c8'),
              svgText(40, 1450, 'Arrival, sleeper, trial, statue and exit anchors guide the composition. Hazard and traversal rules still need design review.', 13, '#b9c4c8')]
    writeSvg('elemental_planes', parts, 1380, 1490)
