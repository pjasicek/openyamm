"""Large review renders of chosen frames of one action with the spear/buckler stand-ins (spear_sheet.py look), several
views, cropped round the character. Args: -- <blend> <action> <out png> <frames a,b,c> [views comma list]"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, action, outp, frames = a[0], a[1], a[2], [float(x) for x in a[3].split(',')]
views = a[4].split(',') if len(a) > 4 else ['left', 'three_quarter', 'front']
sys.argv = [sys.argv[0], '--', blend, '/tmp/x', 'left', '1', action]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spear_sheet.py')).read().split("fl = os.environ.get('FRAMES')")[0])
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
tiles = []
for f in frames:
    scene.frame_set(int(f), subframe=f - int(f))
    H = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix; shaft.matrix_world = H; head.matrix_world = H
    fa = rig.matrix_world @ rig.pose.bones['B_L_Forearm'].matrix; hd = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix
    p0, p1 = fa.translation, hd.translation; along = (p1 - p0).normalized()
    lat = hd.to_3x3() @ Vector((0, 0, 1)); lat = (lat - along * lat.dot(along)).normalized()
    buck.matrix_world = Matrix.Translation(p0 + (p1 - p0) * 0.65 + lat * 0.06) @ Matrix((along, lat.cross(along), lat)).transposed().to_4x4()
    pel = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation
    row = []
    for v in views:
        p = common.render_views(outp[:-4] + f'_f{f:g}', 0.95, 2.3, views=(v,), resolution=(420, 460), distance=9, target=(pel.x, pel.y - 0.25))[0]
        row.append([p, f'{action} f{f:g} ({f / 30:.2f}s) {v}'])
    tiles.append((f, row))
json.dump([[x for x in row] for f, row in tiles], open(outp[:-4] + '.json', 'w'))
print('KEYSHOTS', outp)
