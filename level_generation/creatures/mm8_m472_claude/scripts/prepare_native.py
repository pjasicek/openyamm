from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw
import yaml

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
for folder in ('source/native', 'source/palettes', 'review/native', 'references_hd', 'references_head',
               'scripts', 'motion', 'requests', 'work', 'export', 'textures'):
    (P / folder).mkdir(parents=True, exist_ok=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
palettes = {}
records = []
for tier in (473, 474, 475):
    path = next(p for p in (ROOT/'assets_dev/worlds/mm8/textures').iterdir()
                if p.name.lower() == f'pal{tier}.act')
    palettes[tier] = np.frombuffer(path.read_bytes()[:768], dtype=np.uint8).reshape(256, 3)
    records.append({'id': tier, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
    (P/f'source/palettes/pal{tier}.act').write_bytes(path.read_bytes())
originals = []
images = {}
for path in sorted((ROOT/'assets_dev/engine/sprites').glob('m472*.bmp')):
    index = np.array(Image.open(path))
    assert index.ndim == 2
    rgba = np.dstack((palettes[473][index], np.where(index == 0, 0, 255).astype('uint8')))
    image = Image.fromarray(rgba)
    name = path.stem.lower()
    image.save(P/f'source/native/{name}.png')
    images[name] = image
    originals.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'frame': name,
                      'size': list(image.size), 'alpha_bbox': image.getbbox()})
assert len(originals) == 160, len(originals)
groups = {}
for tier in palettes:
    path = ROOT/f'assets_dev/engine/rendering/sprite_frames/monsters/m{tier}.yml'
    groups[str(tier)] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                         'groups': yaml.safe_load(path.read_text())['sprites']}
inventory = {'identity': 'mm8:m472', 'original_frames': originals, 'palettes': records,
             'sprite_groups': groups, 'monster_ids': [55, 56, 57],
             'descriptors': ['Necromancer (monster) A', 'Necromancer (monster) B', 'Necromancer (monster) C']}
(P/'source/native_inventory.json').write_text(json.dumps(inventory, indent=2)+'\n')

def sheet(name, rows):
    cw, ch = 240, 360
    result = Image.new('RGB', (cw*max(map(len, rows)), ch*len(rows)), (70, 73, 78))
    draw = ImageDraw.Draw(result)
    for y,row in enumerate(rows):
        for x,(image,label) in enumerate(row):
            crop=image.crop(image.getbbox())
            factor=min((cw-20)/crop.width,(ch-35)/crop.height)
            crop=crop.resize((round(crop.width*factor),round(crop.height*factor)),Image.Resampling.NEAREST)
            result.paste(crop,(x*cw+(cw-crop.width)//2,y*ch+ch-12-crop.height),crop)
            draw.text((x*cw+8,y*ch+8),label,fill='white')
    result.save(P/f'review/native/{name}.png')
sheet('standing', [[(images[f'm472sa{v}'], f'Native standing view {v}') for v in range(5)]])
sheet('attack', [[(images[f'm472a{f}{v}'],f'Cast {f} view {v}') for f in 'abcdefgh'] for v in (0,2,4)])
sheet('actions', [[(images[f'm472{role}{f}{v}'], f'{role}{f} view {v}') for f in frames]
                 for role,frames,v in [('w','abcdefgh',0),('w','abcdefgh',2),('n','abcde',0),
                                       ('d','abcd',2),('f','abcde',0),('x','a',0)]])
tiers=[]
path=ROOT/'assets_dev/engine/sprites/m472Sa0.bmp'
index=np.array(Image.open(path))
for tier,palette in palettes.items():
    rgba=np.dstack((palette[index],np.where(index==0,0,255).astype('uint8')))
    tiers.append((Image.fromarray(rgba), f'Native palette {tier}'))
sheet('tiers',[tiers])
state_path=P/'creature_3d_progress.json'
state=json.loads(state_path.read_text())
state.update(scope='complete production: three tiers, fitted humanoid rig, robe deformation, casting sockets, textures, LODs and verified game integration',
             status='in_progress',stage='1_references_and_motion',current_stage='1_references_and_motion',
             current_substep='native_study',source_inventory='source/native_inventory.json',
             native_descriptor_ids=[55,56,57], required_components=[{'id':'armoured_robed_body','artifact_role':'body','required':True}],
             selected_artifacts=[],review={'technical_completion':False,'agent_visual_completion':False,'user_artistic_acceptance':'not_requested'},
             next_action={'owner':'codex','action':'Inspect native anatomy, choose casting motions, generate and gate HD references.'})
state_path.write_text(json.dumps(state,indent=2)+'\n')
print('Decoded',len(originals),'native frames; three palettes and all sprite groups recorded.')
