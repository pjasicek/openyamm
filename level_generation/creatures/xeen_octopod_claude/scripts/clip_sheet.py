"""Clay contact sheet of every clip of work/anim_v1.blend: N frames per clip (rows = clips), with an opaque blue water
plane at z 0 (what the party sees) unless the view name ends in '_dry'. Usage: clip_sheet.py [frames per clip]
[view: quarter|side|front|fq|top, optionally +'_dry'] [clips|all] [blend]; then sheet_join.py <out.png>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
N = int(a[0]) if a else 6
view = a[1] if len(a) > 1 else 'quarter'
ONLYC = a[2].split(',') if len(a) > 2 and a[2] != 'all' else None
BLEND = a[3] if len(a) > 3 else 'anim_v1.blend'
dry = view.endswith('_dry'); view = view.replace('_dry', '')
SCALE = {'quarter': 2.5, 'side': 2.5, 'top': 2.9, 'front': 2.5, 'fq': 2.5}
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', BLEND))
rig = bpy.data.objects['Octopod_Rig']; sc = bpy.context.scene
if not dry:
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0)); wp = bpy.context.active_object; wp.name = 'Water'
    wm = bpy.data.materials.new('water'); wm.diffuse_color = (0.12, 0.32, 0.38, 1); wp.data.materials.append(wm)
CAM = {'quarter': ((3.4, -4.0, 2.3), (0, 0, 0.15)), 'side': ((6, 0, 0.6), (0, 0, 0.15)),
       'top': ((0, -0.001, 6), (0, 0, 0)), 'front': ((0, -6, 1.2), (0, 0, 0.15)),
       'fq': ((-2.6, -4.6, 1.3), (0, 0, 0.15))}[view]
tiles = []
for act in [x for x in bpy.data.actions if x.use_fake_user and (ONLYC is None or x.name in ONLYC)]:
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    row = []
    for k in range(N):
        f = round(f0 + (f1 - f0) * k / max(1, N - 1))
        sc.frame_set(f)
        p = os.path.join(HERE, 'work', f'_sheet_{act.name}_{k}.png')
        C.render(*CAM, SCALE[view], p, res=(480, 330), floor=False, extra=() if dry else ('Water',), color=None if dry else 'MATERIAL')
        row.append(p)
    tiles.append((act.name, row))
import json
json.dump(tiles, open(os.path.join(HERE, 'work', '_sheet.json'), 'w'))
