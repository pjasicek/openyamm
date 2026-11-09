"""Prepare all eight native front attack poses with one shared crop, never per-frame fits."""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
ROOT = D.parent
sys.path.insert(0, str(ROOT))
import process

for folder in ['references', 'prompts', 'raw', 'review']:
    (D / folder).mkdir(exist_ok=True)
source = json.loads((ROOT / 'sources.json').read_text())
steps = source['bindings']['25']['actions']['attack']['views']['0']
names = [step['frame'] for step in steps]
assert len(names) == len(set(names)) == 8
natives = [process.queue.native(ROOT, name) for name in names]
boxes = [im.getchannel('A').getbbox() for im in natives]
crop = [min(b[0] for b in boxes)-6, min(b[1] for b in boxes)-6,
        max(b[2] for b in boxes)+6, max(b[3] for b in boxes)+6]
w, h = crop[2]-crop[0], crop[3]-crop[1]
sheet = Image.new('RGBA', (3*w, 3*h), (255, 0, 255, 255))
layout = []
for i, (name, im) in enumerate(zip(names, natives)):
    x, y = (i % 3)*w, (i // 3)*h
    tile = im.crop(crop)
    sheet.alpha_composite(tile, (x, y))
    reconstructed = Image.new('RGBA', im.size)
    reconstructed.paste(tile, (crop[0], crop[1]))
    assert reconstructed.convert('RGBa').tobytes() == im.convert('RGBa').tobytes()
    layout.append({'frame': name, 'cell_xywh': [x, y, w, h], 'native_bbox': boxes[i]})
sheet.convert('RGB').save(D / 'references/native_front_attack_3x3.png')
report = {
    'scope': 'Front attack trial only; does not replace accepted family checkpoints.',
    'frames': names, 'source_records': {n: source['sources'][n] for n in names},
    'native_steps': steps, 'native_playback': source['bindings']['25']['actions']['attack']['playback'],
    'native_logical_canvas': [256, 256], 'native_pivot': [128, 256],
    'shared_crop_xyxy': crop, 'cell_size_native': [w, h], 'columns': 3, 'rows': 3,
    'layout': layout, 'empty_cells': [8], 'reference_pixels_per_native_pixel': 1,
    'layout_candidates': [{'columns': c, 'rows': r, 'capacity': c*r, 'native_size': [c*w, r*h],
                           'exact_2x_size': [2*c*w, 2*r*h]} for c,r in [(4,2),(3,3),(3,2),(2,3),(2,4)]],
    'selection_reason': '3x3 contains all eight poses in one square request. One empty cell. '
                        'Shared sword-inclusive crop retains movement and source anchoring.',
    'state': 'prepared',
}
(D / 'source_layout.json').write_text(json.dumps(report, indent=2)+'\n')
prompt = '''Use case: native game sprite restoration. Restore the ENTIRE eight-frame front-facing attack animation of the same MM8 Dark Elf Warrior in ONE coherent high-resolution sprite sheet.
Input 1 is the exact native pixel artwork and layout authority. It is a 3-column by 3-row square grid with EIGHT occupied cells, read left-to-right then top-to-bottom: m432aa0, m432ab0, m432ac0 / m432ad0, m432ae0, m432af0 / m432ag0, m432ah0, EMPTY. The bottom-right ninth cell must remain entirely flat magenta. Do not add a ninth character, extra poses, labels or grid lines.
All source frames were cropped using the SAME 232x232 native-coordinate rectangle for the WHOLE sequence, including every sword extremity and a six-pixel safety margin. Preserve that exact common scale, each figure's position within its cell, foot ground level, native body lean and hand/weapon positions. Do not independently center, zoom or stretch figures. Do not move or normalize the sword angles. Every blade tip must remain inside its own cell. Keep the square sheet and equal square cells.
Input 2 is the accepted detailed standing character design and material reference ONLY. Do not copy its pose or head angle over input 1. Restore the exact native animation poses. In particular, retain each native face direction and the different sword foreshortening in the middle row; these are successive frames of one front-view animation, not different viewing directions.
Preserve the adult male dark elf's dark reddish-brown skin, swept-back silver-white hair, pointed ears, near-black fitted armor and gloves, rounded gold-studded shoulder plates, green sleeve bands, muted teal central chest disk WHEN VISIBLE, dark fitted trousers and plated black boots with restrained gold fasteners. One long narrow steel sword with a gold hilt per pose. Arms obscure the chest disk in the first two poses; do not invent extra visible chest/shoulder disks there. No additional ornaments, equipment, glowing eyes or anatomy.
Refine hair strands, face, hands, armor seams and material shading consistently across ALL eight frames together. Preserve the native dark tonal weight and color palette. Render real new detail at 3072x3072 if possible, at least 2048x2048; do not merely interpolate the pixel art or enlarge the empty background. Keep the compact framing of the native reference. Flat pure magenta RGB 255,0,255 background, no shadows, gradients, halos, text or borders. No palette variants.
'''
(D / 'prompts/front_attack_3x3_v1.txt').write_text(prompt)
print(json.dumps({'crop': crop, 'reference': sheet.size, 'poses': names,
                  'timings_ms': [s['duration_ms'] for s in steps], 'playback': report['native_playback']}))
