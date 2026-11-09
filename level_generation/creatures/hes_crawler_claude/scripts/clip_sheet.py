"""Clay contact sheet: each clip at N evenly spaced frames from the side and the three-quarter front.
Args: -- <blend relative to project> <out.jpg> [clips comma list] [frames per clip]"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, a[0]))
out = os.path.join(HERE, a[1])
clips = a[2].split(',') if len(a) > 2 and a[2] else ['Standing', 'Walking', 'Running', 'Attack', 'Bite', 'Hit', 'Death', 'Dead', 'Fidget']
N = int(a[3]) if len(a) > 3 else 5
rig = bpy.data.objects[C.RIG]; sc = bpy.context.scene
tmp = os.path.join(HERE, 'work', 'tmp_sheet'); os.makedirs(tmp, exist_ok=True)
cells = []
for c in clips:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    loop = c in ('Standing', 'Walking', 'Running', 'Fidget')
    for k in range(N):
        f = f0 + round((f1 - f0) * k / (N if loop else N - 1))
        sc.frame_set(f)
        for view, loc, tgt in (('s', (-2.5, 0.0, 0.22), (0, 0, 0.22)), ('q', (-1.6, -1.9, 0.9), (0, 0, 0.18))):
            p = f'{tmp}/{c}_{k}_{view}.png'
            C.render(loc, tgt, 1.25, p, res=(320, 220))
            cells.append(p)
compose = """
import sys
from PIL import Image, ImageDraw
out, n, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); names = sys.argv[4].split(','); paths = sys.argv[5:]
ims = [Image.open(p) for p in paths]; w, h = ims[0].size
o = Image.new('RGB', (w * cols, (h + 16) * n), (40, 40, 40)); d = ImageDraw.Draw(o)
for i, im in enumerate(ims):
    r, c = divmod(i, cols); o.paste(im, (c * w, r * (h + 16) + 16))
for r, nm in enumerate(names): d.text((4, r * (h + 16) + 2), nm, fill=(255, 220, 120))
o.save(out, quality=88)
"""
subprocess.run(['/usr/bin/python3', '-c', compose, out, str(len(clips)), str(2 * N), ','.join(clips)] + cells, check=True)
print('SHEET', out)
