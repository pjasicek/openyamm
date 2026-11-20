"""Inventory MM6 goblin family and prepare only the missing native directions."""
from pathlib import Path
import hashlib
import json
import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
PREVIOUS = ROOT.parent / 'direct_front_final'
CANVAS = (355, 289)
PALETTES = [745, 746, 747]
ACTIONS = {'at': 'attack', 'dy': 'death', 'fi': 'fidget', 'st': 'standing', 'wa': 'walk', 'wi': 'hit'}

def native(name, palette=745):
    index = np.array(Image.open(REPO / f'assets_dev/engine/sprites/{name}.bmp'))
    rgb = np.frombuffer((REPO / f'assets_dev/worlds/mm6/textures/pal{palette}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    return Image.fromarray(np.dstack((rgb[index], np.where(index == 0, 0, 255).astype(np.uint8))))

def asset(path):
    return {'path': str(path.relative_to(REPO)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def run():
    for d in ['references', 'native', 'raw', 'prompts', 'review']:
        (ROOT / d).mkdir(exist_ok=True)
    table = REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
    groups = [g for g in yaml.load(table.read_text(), Loader=yaml.CSafeLoader)['sprites']
              if g['frames'][0]['texture_name'].startswith('gob') and g['sprite_name'] != 'goblet']
    used = {n for g in groups for f in g['frames'] for n in
            ([f['texture_name']] if 'Image1' in f['flags'] else [f['texture_name']+str(v) for v in range(5)])}
    assert len(used) == 59
    sources = {}
    for name in sorted(used):
        im = native(name); im.save(ROOT / f'native/{name}.png')
        sources[name] = dict(asset(REPO / f'assets_dev/engine/sprites/{name}.bmp'), size=im.size,
                             visible_bounds=im.getbbox(), native_offset=[0,0], referenced=True)
    reused = {n: asset(PREVIOUS / f'toned_v1/aligned_2x/{n}.png') for n in used if n.endswith('0')}
    assert len(reused) == 31
    batches = {'standing_sides': {'frames': [f'gobsta{v}' for v in range(1,5)], 'columns':2}}
    for v in range(1,5):
        batches[f'walk_{v}'] = {'frames': [f'gobwa{letter}{v}' for letter in 'abcdef'], 'columns':3}
    for key,b in batches.items():
        b.update(rows=2)
        sheet = Image.new('RGB',(b['columns']*768,2*640),(255,0,255))
        for i,n in enumerate(b['frames']):
            im=native(n).resize((710,578),Image.Resampling.NEAREST)
            sheet.paste(im,(i%b['columns']*768+29,i//b['columns']*640+31),im)
        sheet.save(ROOT/f'references/{key}.png')
        direction = 'front-oblique, profile, rear-oblique, back, in row-major order' if key=='standing_sides' else {'1':'front-oblique','2':'profile','3':'rear-oblique','4':'back'}[key[-1]]
        prompt=f'''Use case: style-transfer. Restore native Might and Magic VI goblin game sprites to detailed high-quality dark fantasy artwork.
Input 1 is exact pose, camera and layout authority: {b['columns']} columns by 2 rows, {len(b['frames'])} poses left-to-right then top-to-bottom. Action {key}; direction {direction}. Every native leg, arm, hand, sword and body orientation must match its own cell. Keep the native pose differences and foot planting; do not duplicate a single walking pose.
Input 2 is the accepted restored FRONT identity/material reference: preserve this same goblin's face, olive-green skin, bald head, long pointed ears, small tusks, yellow eyes, lean muscular body, dark gray riveted/spiked shoulder armor and collar, forearm guards, brown leather strip skirt/belt, metal shin guards, clawed bare toes, and single curved sword with ornate gold guard. Source reference controls the sword angle and visibility, armor coverage and bare back. No extra weapons, helmets, hair, horns, cape, tail or scenery. Keep the sword in its native hand, even viewed from behind.
Follow the accepted reference's precise design, surface detail and quality, with realistic skin, worn leather and dull steel. Keep its dark muted tonal weight, consistent soft upper-left baked lighting and the same proportions. No toy or cartoon redesign. Do not brighten shadows or add rim light. If an additional restored side reference is supplied, use it only for identity continuity; native input 1 remains pose authority.
Full figure and sword tips wholly inside each cell with generous empty gutters, common character scale, no independent zoom/recentering. Aim for 2048-wide or higher useful detail if supported. Background perfectly uniform pure magenta RGB(255,0,255); no gradients, shadows, bounce or magenta reflected onto the creature. No intended purple/pink material on this green-base creature. No labels, grid lines, text or watermark.
'''
        (ROOT/f'prompts/{key}.txt').write_text(prompt)
    identity=Image.open(PREVIOUS/'toned_v1/aligned_2x/gobsta0.png')
    bg=Image.new('RGB',identity.size,(48,48,48));bg.paste(identity,(0,0),identity);bg.save(ROOT/'references/accepted_front.png')
    contact=Image.new('RGB',(5*355,3*320),(45,45,45));draw=ImageDraw.Draw(contact)
    for row,pal in enumerate(PALETTES):
        for v in range(5):
            im=native(f'gobsta{v}',pal);contact.paste(im,(v*355,row*320+24),im)
            draw.text((v*355+5,row*320+5),f'{pal}: view {v}',fill='white')
    contact.save(ROOT/'references/native_variants.png')
    (ROOT/'sources.json').write_text(json.dumps({'sources':sources,'groups':{'goblin':{'sprites':groups}},'reused':reused,
       'group_source':asset(table),'palette_sources':{str(p):asset(REPO/f'assets_dev/worlds/mm6/textures/pal{p}.act') for p in PALETTES},
       'excluded':['goblet.bmp: unrelated object'], 'pixel_aliases':{'gobdyf0':'gobdyd0'}, 'logical_canvas':CANVAS,'logical_pivot':[177.5,289],
       'variant_scales':{str(p):sorted({f.get('scale',1) for g in groups for f in g['frames'] if f['palette_id']==p}) for p in PALETTES}},indent=2)+'\n')
    (ROOT/'batches.json').write_text(json.dumps(batches,indent=2)+'\n')
    print('59 native frames; reuse 31 accepted front frames; generate 28 in five batches.')

if __name__=='__main__':run()
