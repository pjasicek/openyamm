"""Large clay renders of chosen action frames (or 'rest'). Args: -- <blend> <out prefix (writes <prefix>.json for sheet.py)> <views comma> action:frame [...]
(env TEXTURED=1 for texture colours, SIZE=ortho height)"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import json
a = sys.argv[sys.argv.index('--') + 1:]
blend, outp, views, picks = a[0], a[1], a[2].split(','), a[3:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
common.workbench_clay(scene, textured=bool(os.environ.get('TEXTURED')))
H = float(os.environ.get('SIZE', '1.9')); ZC = float(os.environ.get('ZC', '0.85'))
tiles = []
for pk in picks:
    name, f = pk.rsplit(':', 1) if ':' in pk else (pk, '0')
    rig.animation_data_create()
    if name == 'rest':
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
    else:
        act = bpy.data.actions[name]; rig.animation_data.action = act
        if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(float(f)), subframe=float(f) - int(float(f)))
    pel = rig.matrix_world @ rig.pose.bones['B_Pelvis'].head
    for v in views:
        p = common.render_views(outp + f'_{name}_{f}', ZC, H, views=(v,), resolution=(560, 760), target=(pel.x, pel.y))[0]
        tiles.append(p)
json.dump([{'label': ' '.join(picks) + ' [' + ','.join(views) + ']', 'frames': tiles}], open(outp + '.json', 'w'))
print('SHOTS', outp + '.json', len(tiles))
