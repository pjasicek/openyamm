#!/usr/bin/env python3
"""v3b review sheets (system Python + Blender renders; v3a from export/mm7_m182_v3a.glb baked per tier, v3b from
the master with the baked tier maps): front vs native m182sa0 and side vs m182sa2 (Standing frame 0 at the motion-gate
camera), head graft close-ups from the user's three-quarter-below angle per tier (v3a | v3b), wing root in mid-flap
from the user's angle (v3a | v3b). Out: review/shots/v3b/*.png"""
import json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[2]; O = P / 'review/shots/v3b'; O.mkdir(parents=True, exist_ok=True)
R = P / 'work/v3b/renders/shots'; R.mkdir(parents=True, exist_ok=True)
NAT = P.parent / 'mm7_m182/aligned_2x'; E = 0.0195
def blend_for(tier):
    out = P / f'work/v3b/textured_v3b_{tier}.blend'
    subprocess.run(['blender', '-b', '--factory-startup', '-P', str(P / 'scripts/v3/preview_tex.py'), '--',
                    *(str(P / f'work/v3/tiers/{s}_{tier}.png') for s in ('body', 'head', 'wings')), str(P / 'work/v3/spec_none.json'), str(out)], check=True, capture_output=True)
    return out
def render(src, shots, tag):
    spec = {'out': str(R / tag), 'engine': 'EEVEE', 'res': [700, 700], 'shots': shots}
    (R / f'{tag}.json').write_text(json.dumps(spec))
    subprocess.run(['blender', '-b', '--factory-startup', '-P', str(P / 'scripts/v3/render.py'), '--', str(src), str(R / f'{tag}.json')], check=True, capture_output=True)
    return {s['name']: Image.open(R / tag / (s['name'] + '.png')).convert('RGB') for s in shots}
def native(frame):
    im = Image.open(NAT / f'{frame}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (90, 90, 92, 255)); bg.alpha_composite(im); return bg.convert('RGB')
def sheet(cells, labels, name, size=420):
    c = Image.new('RGB', (size * len(cells), size + 22), (40, 40, 44)); d = ImageDraw.Draw(c)
    for k, (im, lab) in enumerate(zip(cells, labels)):
        c.paste(im.resize((size, size)), (size * k, 22)); d.text((size * k + 6, 4), lab, fill=(255, 255, 160))
    c.save(O / name)
fs = [{'name': 'front', 'clip': 'Standing', 'frame': 0, 'dir': [0, -1, E], 'target': [0, -.5, .85], 'scale': 3.4},
      {'name': 'side', 'clip': 'Standing', 'frame': 0, 'dir': [-1, 0, E], 'target': [0, -.4, .8], 'scale': 3.4}]
graft = [{'name': 'graft', 'clip': 'Standing', 'frame': 0, 'dir': [1, -.75, -.15], 'track': 'Head', 'offset': [0, .12, -.12], 'scale': .75},
         {'name': 'graft_below', 'clip': 'Standing', 'frame': 0, 'dir': [.3, -.6, -.8], 'track': 'Head', 'offset': [0, .08, -.12], 'scale': .75},
         {'name': 'graft_attack', 'clip': 'Attack', 'frame': 8, 'dir': [1, -.5, .2], 'track': 'Head', 'offset': [0, .12, -.1], 'scale': .8}]
wing = [{'name': f'wing_{f}', 'clip': 'Standing', 'frame': f, 'dir': [1, .9, -.25], 'track': 'LWing0', 'offset': [.1, 0, -.05], 'scale': .75} for f in (3, 9, 15)]
new, old = {}, {}
for t in 'abc':
    new[t] = render(blend_for(t), fs + graft + wing, f'v3b_{t}'); old[t] = render(P / f'work/v3b/v3a_m182_{t}.glb', fs + graft + wing, f'v3a_{t}')
sheet([native('m182sa0'), old['a']['front'], new['a']['front']], ['native m182sa0', 'v3a Standing', 'v3b Standing'], 'front_vs_native.png')
sheet([native('m182sa2'), old['a']['side'], new['a']['side']], ['native m182sa2', 'v3a Standing', 'v3b Standing'], 'side_vs_native.png')
for t, pid in zip('abc', (183, 184, 185)):
    sheet([old[t]['graft'], new[t]['graft'], old[t]['graft_below'], new[t]['graft_below'], new[t]['graft_attack']],
          [f'v3a tier {t} ({pid})', 'v3b', 'v3a below', 'v3b below', 'v3b Attack (jaw open)'], f'head_graft_{t}.png', 360)
sheet([old['a'][f'wing_{f}'] for f in (3, 9, 15)] + [new['a'][f'wing_{f}'] for f in (3, 9, 15)],
      ['v3a Standing f3', 'v3a f9 (mid-flap)', 'v3a f15', 'v3b Standing f3', 'v3b f9 (mid-flap)', 'v3b f15'], 'wing_root_mid_flap.png', 330)
print('SHOTS', sorted(p.name for p in O.iterdir()))
