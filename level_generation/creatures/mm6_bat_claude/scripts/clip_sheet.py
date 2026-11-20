"""Contact sheet: each clip at 4 evenly spaced frames, side + three-quarter. Args: out_png [clips]"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bat as C
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
clips = args[1].split(',') if len(args) > 1 else ['Fly', 'Attack', 'Hit', 'Death']
rig = bpy.data.objects['Bat_Rig']; sc = bpy.context.scene
tmp = os.path.join(os.path.dirname(out), 'tmp_sheet'); os.makedirs(tmp, exist_ok=True)
cells = []
for c in clips:
    a = bpy.data.actions[c]; rig.animation_data.action = a
    f0, f1 = (int(x) for x in a.frame_range)
    for k in range(4):
        f = f0 + round((f1 - f0) * k / 4) if a.get('loop') or c in ('Fly',) else f0 + round((f1 - f0) * k / 3)
        sc.frame_set(f)
        for view, loc in (('f', (0.0, -1.6, 0.2)), ('q', (-1.0, -1.1, 0.6))):
            p = f'{tmp}/{c}_{k}_{view}.png'
            C.render_ortho(loc, (0, 0, 0.15), 1.2, p, res=(300, 220))
            cells.append(p)
compose = """
import sys
from PIL import Image, ImageDraw
out, n = sys.argv[1], int(sys.argv[2]); names = sys.argv[3].split(','); paths = sys.argv[4:]
ims = [Image.open(p) for p in paths]; w, h = ims[0].size
o = Image.new('RGB', (w * 8, (h + 16) * n), (40, 40, 40)); d = ImageDraw.Draw(o)
for i, im in enumerate(ims):
    r, c = divmod(i, 8); o.paste(im, (c * w, r * (h + 16) + 16))
for r, nm in enumerate(names): d.text((4, r * (h + 16) + 2), nm, fill=(255, 220, 120))
o.save(out)
"""
subprocess.run(['/usr/bin/python3', '-c', compose, out, str(len(clips)), ','.join(clips)] + cells, check=True)
print('SHEET', out)
