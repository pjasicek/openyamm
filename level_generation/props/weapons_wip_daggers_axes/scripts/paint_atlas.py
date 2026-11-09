"""Pack six exact orthographic guides for one prop; split its generated albedo/metal-mask atlas losslessly."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
VIEWS = ['front', 'back', 'left', 'right', 'top', 'bottom']


def prep(name):
    entry = json.loads((PROJECT / 'designs.json').read_text())[name]
    folder = PROJECT / 'codex_tex' / name
    sheet = Image.new('RGBA', (1024, 1536))
    for i, view in enumerate(VIEWS):
        guide = Image.open(folder / f'guide_{view}.png').convert('RGBA')
        assert guide.size == (512, 512) and guide.getchannel('A').getbbox()
        sheet.alpha_composite(guide, (i % 2 * 512, i // 2 * 512))
    sheet.save(folder / 'guide_atlas.png')
    master = PROJECT / 'meshy' / name / 'references_hd' / '00_three_quarter.png'
    shutil.copyfile(master, folder / 'design_reference.png')
    prompt = f'''Use case: precise-object-edit. Asset type: ONE six-view albedo texture-source atlas of the SAME prop.
Image 1 is the exact grey 3D mesh guide atlas and is the edit target. Image 2 is its HD material/identity reference.
Paint directly over image 1, retaining EXACT canvas aspect 1024 wide by 1536 tall and the exact two-column,
three-row arrangement. Six equal square cells. Row 1: front, back. Row 2: left, right. Row 3: top, bottom.
CRITICAL: row 1 contains tiny END-ON cross-sections, not full weapon side views. Keep those end views tiny and
strongly foreshortened. Row 2 contains long nearly EDGE-ON side views: retain the thin blade edge, with thicker
grip/guard/socket. Row 3 alone shows the full decorated broad face and reverse. Never replace a row-1 or row-2
guide by another upright broad-face weapon.
Keep every guide view's silhouette, position, size, angle, cavities and parts EXACTLY unchanged. Do not move,
rotate, enlarge, shrink or redesign anything. Each cell shows the same mesh from the specified side.
Subject identity: {entry['identity']}
Surface materials: {entry['materials']}
This is a PBR BASE-COLOUR source: flat shadowless illumination, NO cast shadows, ambient occlusion, reflections,
metallic hot spots, lighting gradients, rim light or shiny white highlights. Paint real intrinsic surface colour,
fine wear, grain and ornament. Shapes and recesses come from the mesh; do not bake illumination into them.
No background, floor, scene, text, labels, separators or added objects. Outside every silhouette is genuine
transparency. Do not paint labels or stray marks in the cell margins. Materials must agree across all six views.'''
    (folder / 'paint_atlas_prompt.txt').write_text(prompt + '\n')
    metal = f"""Use case: precise-object-edit. Technical material-classification mask of ONE six-view weapon atlas.
Image 1 is the painted atlas of {entry['title']} and is the edit target. Preserve the exact canvas, all six views,
their silhouettes, positions, scales and openings. Outside each object must be truly transparent.
Classify every opaque surface with one flat solid colour: PURE WHITE for all actual METAL (steel, iron, silver,
gold, bronze, brass, metal binding and metal ornament); PURE BLACK for WOOD, LEATHER, CLOTH and painted ENAMEL;
PURE GREEN #00ff00 for GEMS, PEARLS and CRYSTAL; PURE BLUE #0000ff for IVORY or BONE.
Blackened iron is WHITE because it is metal. A gold/black handle spiral has WHITE gold and BLACK leather.
Subject materials: {entry['materials']}
No grey, gradients, lighting, highlights, outlines, labels or added shapes. No opaque background. Every nonmetal
object pixel remains opaque black, green or blue as appropriate, and holes remain transparent. Keep all six views
in the identical two-column three-row arrangement. This is material data for metallic and roughness maps.
"""
    (folder / 'metal_atlas_prompt.txt').write_text(metal + '\n')
    print(folder / 'guide_atlas.png')


def split(name, source, kind):
    assert kind in ('paint', 'metal')
    folder = PROJECT / 'codex_tex' / name
    source = Path(source)
    sheet = Image.open(source).convert('RGBA')
    assert abs(sheet.width / sheet.height - 2 / 3) < .04, (sheet.size, 'wrong atlas aspect')
    assert sheet.getchannel('A').getextrema()[0] == 0, 'Atlas has no transparent background'
    destination = folder / f'{kind}_atlas_v1.png'
    if source.resolve() != destination.resolve():
        shutil.copyfile(source, destination)
    # Generated rows can drift across the nominal grid; crop each separated silhouette band without resampling.
    bands = {}
    for column in range(2):
        half = sheet.crop((round(column * sheet.width / 2), 0,
                           round((column + 1) * sheet.width / 2), sheet.height))
        occupied = (np.asarray(half)[..., 3] > 128).any(axis=1)
        changes = np.diff(np.r_[False, occupied, False].astype(int))
        starts, ends = np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)
        assert len(starts) == len(ends) == 3, (name, kind, column, starts, ends)
        bands[column] = list(zip(starts, ends))
    cells = {}
    for i, view in enumerate(VIEWS):
        x, y = i % 2, i // 2
        start, end = bands[x][y]
        box = (round(x * sheet.width / 2), max(int(start) - 6, 0),
               round((x + 1) * sheet.width / 2), min(int(end) + 6, sheet.height))
        cell = sheet.crop(box)
        assert cell.getchannel('A').getbbox(), (name, view, 'empty view')
        cell.save(folder / f'{kind}_{view}.png')
        cells[view] = {'crop': box, 'size': cell.size}
    receipt = {'tool': 'built-in imagegen', 'source': str(source), 'saved': str(destination),
               'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'kind': kind,
               'prompt': str(folder / f'{kind}_atlas_prompt.txt'), 'cells': cells,
               'guide_sha256': hashlib.sha256((folder / 'guide_atlas.png').read_bytes()).hexdigest()}
    (folder / f'{kind}_generation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(name, kind, sheet.size, 'six nonempty transparent cells')


if __name__ == '__main__':
    command, name, *rest = sys.argv[1:]
    {'prep': prep, 'split': split}[command](name, *rest)
