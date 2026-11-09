"""Inventory native m162 inputs and prepare pose-authority grids; no AI generation."""
from pathlib import Path
import hashlib
import json
import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ASSETS = REPO / 'assets_dev'
CANVAS = (256, 256)
PALETTES = [163, 164, 165]
VIEWS = ['front', 'front_oblique', 'profile', 'rear_oblique', 'back']

def native(name, palette=163):
    index = np.array(Image.open(ASSETS / f'worlds/mm7/sprites/{name}.bmp'))
    rgb = np.frombuffer((ASSETS / f'worlds/mm7/textures/pal{palette:03}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    return Image.fromarray(np.dstack((rgb[index], np.where(index == 0, 0, 255).astype(np.uint8))))

def run():
    for directory in ['references', 'prompts', 'raw', 'native', 'review']:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    groups = {n: yaml.safe_load((ASSETS / f'engine/rendering/sprite_frames/monsters/{n}.yml').read_text())
              for n in ['m163', 'm164', 'm165']}
    used = {name for group in groups['m163']['sprites'] for frame in group['frames']
            for name in ([frame['texture_name']] if 'Image1' in frame['flags']
                         else [frame['texture_name']+str(v) for v in range(5)])}
    files = sorted((ASSETS / 'worlds/mm7/sprites').glob('m162*.bmp'))
    sources = {}
    for file in files:
        im = native(file.stem)
        im.save(ROOT / f'native/{file.stem}.png')
        sources[file.stem] = {'path': str(file.relative_to(REPO)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                              'size': list(im.size), 'visible_bounds': im.getbbox(), 'native_offset': [0,0], 'referenced': file.stem in used}
    batches = {'standing': {'frames': [f'm162sa{v}' for v in range(5)], 'columns': 3}}
    for code, action, letters in [('a', 'attack', 'abcdefgh'), ('n', 'hit', 'abcde'), ('w', 'walk', 'abcdefgh')]:
        for view in range(5):
            batches[f'{action}_{view}'] = {'frames': [f'm162{code}{letter}{view}' for letter in letters],
                'columns': 4 if code in ['w','a'] else 3, 'direction': VIEWS[view]}
    batches['fidget'] = {'frames': [f'm162f{letter}0' for letter in 'abcde'], 'columns': 3, 'direction': 'front'}
    batches['death_corpse'] = {'frames': [f'm162d{letter}0' for letter in 'abcd'] + ['m162xa0'], 'columns': 3,
                              'direction': 'front (falling and prone)'}
    assert len(sources) == 120
    assert sorted(x for b in batches.values() for x in b['frames']) == sorted(sources)
    for key, batch in batches.items():
        cols = batch['columns']; rows = (len(batch['frames']) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 576, rows * 576), (255, 0, 255))
        for i, name in enumerate(batch['frames']):
            im = native(name).resize((512, 512), Image.Resampling.NEAREST)
            sheet.paste(im, (i % cols * 576 + 32, i // cols * 576 + 32), im)
        sheet.save(ROOT / f'references/{key}.png')
        batch.update(rows=rows, cell_size=576, native_offset=[32, 32], reference=f'references/{key}.png')
        prompt = f'''Use case: style-transfer. Faithfully restore the Might and Magic VII Behemoth native sprites into detailed, frightening, believable high-quality dark fantasy game artwork.
Input 1 is exact POSE AND LAYOUT authority: {cols} columns by {rows} rows, {len(batch['frames'])} occupied cells left-to-right then top-to-bottom. Action/view: {key}, {batch.get('direction','front, front-oblique, profile, rear-oblique, back in this exact order')}. Leave unused cells empty. Preserve the different limb positions, hand rotation, fingers, claw arcs, head orientation, hunched back, weight and foot contacts in EACH cell. Do not replace action poses with standing poses.
Same creature in every image: enormous hunched gorilla-like bipedal monster, huge broad shoulders and long thick muscular arms, short powerful bent legs, massive splayed clawed hands. Craggy wrinkled gray/beige leathery hide and very dark blue-gray recessed chest/belly/inner limbs. Deep dark forest-GREEN shaggy mane over the crown, shoulders and along the upper back, with short green chin beard. Ferocious brutish broad snarling face, deep-set small amber eyes, broad flattened snout, heavy brows, large projecting ivory tusks/fangs and teeth. Extremely long thin tapering ivory sickle claws with restrained dark rust-red tips, as in the original, on each massive hand. Follow source finger count and visibility, not generic human hands. Small pointed ear as visible in side view. No clothes, weapons, armor, tail, invented horns, glowing eyes, magic or accessories.
Keep the source's squat heavy hunched proportions and dark muted tonal weight. Detailed pores, cracked leathery folds, wiry mane strands and keratin claws, restrained material shading and soft upper-left baked illumination. Not an upright bear or werewolf, not a cute cartoon, toy, glossy plastic or smooth children's character. Forehead and hunched mane continuous across views. Match native anatomy and silhouette while clarifying detail; do not redesign.
Keep common character scale and native-relative placement across the sheet, no per-cell zoom/recentering. Full body and every claw tip inside its own cell with generous empty gutters. Highest useful detail; aim for a 2048-wide sheet or higher if supported, not a tiny contact sheet.
Background: perfectly uniform pure magenta RGB(255,0,255), no gradient, checkerboard, ground shadow, colored bounce, magenta reflection, text or grid lines. The green-base creature has no purple/fuchsia materials; claw tips are dark warm rust-red, not pink/magenta. Fur stays green and separate from gray hide, ivory teeth/claws, rust-red tips and amber eyes for selective recoloring.
'''
        if key != 'standing':
            prompt += 'Input 2 is accepted restored standing artwork, IDENTITY AND MATERIAL authority only. Preserve that exact face, mane, hide and claw design; input 1 controls every action and camera angle.\n'
        if key == 'death_corpse':
            prompt += ('These are COLLAPSE and CORPSE poses: first two falling backward, then lying on the back '
                       'with legs raised/bent and arms/claws spread. Match exact foreshortening and the changing '
                       'corpse silhouette in the native sheet; the final two cells are low wide bodies on the '
                       'ground, never upright or kneeling. Keep the same body mass and do not enlarge the prone '
                       'body to fill its cell.\n')
        (ROOT / f'prompts/{key}.txt').write_text(prompt)
    (ROOT / 'batches.json').write_text(json.dumps(batches, indent=2)+'\n')
    (ROOT / 'sources.json').write_text(json.dumps({'sources': sources, 'groups': groups, 'palettes': [163,164,165],
        'logical_canvas': [256,256], 'anchor': 'native Center flag; current actor rendering bottom-anchors full canvas', 'logical_pivot': [128,256], 'frame_scale': 2.0,
        'base_palette':163, 'unreferenced':sorted(set(sources)-used),
        'group_sources': {n: {'path': f'assets_dev/engine/rendering/sprite_frames/monsters/{n}.yml',
            'sha256': hashlib.sha256((ASSETS / f'engine/rendering/sprite_frames/monsters/{n}.yml').read_bytes()).hexdigest()}
            for n in groups},
        'palette_sources':{str(p):{'path':str((ASSETS/f'worlds/mm7/textures/pal{p}.act').relative_to(REPO)), 'sha256':hashlib.sha256((ASSETS/f'worlds/mm7/textures/pal{p}.act').read_bytes()).hexdigest()} for p in PALETTES},
        'scope': '120 unique native images; 115 referenced; hit-e art retained as unused source, no invented views or inbetweens'}, indent=2)+'\n')
    contact = Image.new('RGB', (1280,840), (50,50,50)); draw=ImageDraw.Draw(contact)
    for row, palette in enumerate([163,164,165]):
        for view in range(5):
            im = native(f'm162sa{view}',palette)
            contact.paste(im,(view*256,row*280+24),im)
            draw.text((view*256+5,row*280+6),f'Palette {palette}, view {view}',fill='white')
    contact.save(ROOT/'references/native_variants.png')
    print(f'{len(sources)} frames, {len(batches)} generation batches')

if __name__ == '__main__':
    run()
