"""Clip sheet: every clip at evenly spaced frames from the side (left) and a front three-quarter, with a floor plane.
Args: -- <blend> <out.png> [frames per clip]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[:2]; K = int(args[2]) if len(args) > 2 else 6
crest = args[3] if len(args) > 3 else 'full'
clips_arg = args[4].split(',') if len(args) > 4 else None
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0)); floor = bpy.context.object; floor.name = 'Floor'
show = [C.MESH, 'Floor'] + [o.name for o in bpy.data.objects if o.name.startswith(f'Crest_{crest}_') and '_LOD' not in o.name]
clips = clips_arg or ['Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget']
tmp = C.path('work/sheet_tmp'); os.makedirs(tmp, exist_ok=True)
files = []
for clip in clips:
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    f0, f1 = act.frame_range
    row = []
    for k in range(K):
        f = round(f0 + (f1 - f0) * k / max(K - 1, 1))
        bpy.context.scene.frame_set(int(f))
        for view, (loc, tgt) in (('s', ((6, -0.1, 0.45), (0, -0.1, 0.45))), ('q', ((3.6, -4.2, 1.6), (0, -0.1, 0.5)))):
            p = f'{tmp}/{clip}_{k}_{view}.png'
            C.render_ortho(loc, tgt, 3.4, p, show=show, res=(300, 210), color='material')
            row.append(p)
    files.append((clip, row))
import json
json.dump({'K': K, 'rows': files}, open(C.path(out) + '.json', 'w'))
print('SHEET', out)
