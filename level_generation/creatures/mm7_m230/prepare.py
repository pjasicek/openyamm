"""Inventory native m230 inputs and prepare pose-authority grids; no AI generation."""
from pathlib import Path
import hashlib
import json
import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ASSETS = REPO / 'assets_dev'
VIEWS = ['front', 'front_oblique', 'profile', 'rear_oblique', 'back']

def native(name, palette=54):
    index = np.array(Image.open(ASSETS / f'engine/sprites/{name}.bmp'))
    rgb = np.frombuffer((ASSETS / f'worlds/mm7/textures/pal{palette:03}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    return Image.fromarray(np.dstack((rgb[index], np.where(index == 0, 0, 255).astype(np.uint8))))

def run():
    for directory in ['references', 'prompts', 'raw', 'native', 'review']:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    groups = {n: yaml.safe_load((ASSETS / f'engine/rendering/sprite_frames/monsters/{n}.yml').read_text())
              for n in ['m231', 'm232', 'm233']}
    files = sorted((ASSETS / 'engine/sprites').glob('m230*.bmp'))
    sources = {}
    for file in files:
        im = native(file.stem)
        im.save(ROOT / f'native/{file.stem}.png')
        sources[file.stem] = {'path': str(file.relative_to(REPO)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                              'size': list(im.size), 'visible_bounds': im.getbbox()}
    batches = {'standing': {'frames': [f'm230sa{v}' for v in range(5)], 'columns': 3}}
    for code, action, letters in [('a', 'attack', 'abcdef'), ('n', 'hit', 'abcdef'), ('w', 'walk', 'abcdefgh')]:
        for view in range(5):
            batches[f'{action}_{view}'] = {'frames': [f'm230{code}{letter}{view}' for letter in letters],
                'columns': 4 if code == 'w' else 3, 'direction': VIEWS[view]}
    batches['fidget'] = {'frames': [f'm230f{letter}0' for letter in 'abcd'], 'columns': 2, 'direction': 'front'}
    batches['death_corpse'] = {'frames': [f'm230d{letter}0' for letter in 'abcd'] + ['m230xa0'], 'columns': 3,
                              'direction': 'front (falling and prone)'}
    assert len(sources) == 114
    assert sorted(x for b in batches.values() for x in b['frames']) == sorted(sources)
    for key, batch in batches.items():
        cols = batch['columns']; rows = (len(batch['frames']) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 576, rows * 576), (255, 0, 255))
        for i, name in enumerate(batch['frames']):
            im = native(name).resize((512, 512), Image.Resampling.NEAREST)
            sheet.paste(im, (i % cols * 576 + 32, i // cols * 576 + 32), im)
        sheet.save(ROOT / f'references/{key}.png')
        batch.update(rows=rows, cell_size=576, native_offset=[32, 32], reference=f'references/{key}.png')
        prompt = f'''Use case: style-transfer. Restore the original Might and Magic VII armored fighter sprites into detailed, coherent game sprite artwork.
Input 1 is the exact native pose and layout authority: {cols} columns by {rows} rows, {len(batch['frames'])} occupied cells, ordered left-to-right then top-to-bottom: {', '.join(batch['frames'])}. Leave unused cells empty.
View/action: {key}, {batch.get('direction', 'front, front-oblique, profile, rear-oblique, back in that order')}.
Preserve EVERY original pose, head direction, torso twist, weapon foreshortening, grip, arm bends, raised/planted feet and leg separation. In particular this is the SAME slim adult armored fighter, not a bulky modern redesign. Preserve the cylindrical closed visor helmet with narrow horizontal eye slit and curved green/white plume, silver steel plates and chainmail, restrained gold edging, deep forest-green surcoat with the original white heraldic emblem and diagonal white bands, dark leather joints, steel boots, and the original sword.
Clarify real metal and fabric texture with fine restrained detail. Keep the original dark tonal weight and soft upper-left baked lighting, readable silver highlights and dark recesses; no cartoon, toy, oversize pauldrons, invented accessories, dramatic rim lighting, ground shadows or new costume. White heraldry and silver/gold must remain distinct from the green cloth for selective recoloring.
Keep the input layout, common scale and native-relative pose placement; no per-cell zoom or recentering. Keep whole figures, plume tips and sword tips within their own cells with clear margins, no overlapping cells. Render high detail at the highest supported useful resolution, aiming at about twice the original per-character pixel detail.
Background: perfectly uniform pure magenta RGB(255,0,255), no checkerboard, no gradients, no colored bounce or reflected magenta, no text, labels or grid lines. This is an extraction matte; intended character materials have NO magenta.
'''
        if key != 'standing':
            prompt += 'Input 2 is the selected enhanced five-view standing sheet, IDENTITY AND MATERIAL reference only. Match that same helmet, armor, heraldry, colors and rendering detail. Do NOT replace input 1 action poses with standing poses.\n'
        (ROOT / f'prompts/{key}.txt').write_text(prompt)
    (ROOT / 'batches.json').write_text(json.dumps(batches, indent=2)+'\n')
    (ROOT / 'sources.json').write_text(json.dumps({'sources': sources, 'groups': groups, 'palettes': [54,55,233],
        'logical_canvas': [256,256], 'anchor': 'Center', 'logical_pivot': [128,128], 'frame_scale': 0.899994,
        'scope': '114 unique native images; no new views or inbetweens'}, indent=2)+'\n')
    contact = Image.new('RGB', (1280,840), (50,50,50)); draw=ImageDraw.Draw(contact)
    for row, palette in enumerate([54,55,233]):
        for view in range(5):
            im = native(f'm230sa{view}',palette)
            contact.paste(im,(view*256,row*280+24),im)
            draw.text((view*256+5,row*280+6),f'Palette {palette}, view {view}',fill='white')
    contact.save(ROOT/'references/native_variants.png')
    print(f'{len(sources)} frames, {len(batches)} generation batches')

if __name__ == '__main__':
    run()
