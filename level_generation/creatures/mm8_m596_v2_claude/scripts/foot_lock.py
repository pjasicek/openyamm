"""Foot locks of a clip: per 1/48 s the world ankle (Foot bone head) of both feet and the lowest sole vertex height;
reports each foot's drift while planted (height under 5 mm) and the Root/Hips travel at the clip end.
Usage: blender -b -P foot_lock.py -- <blend> <clip>"""
import os, sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
rig = bpy.data.objects['CrystalRig']; sc = bpy.context.scene; act = bpy.data.actions[a[1]]; rig.animation_data.action = act
f0, f1 = act.frame_range; rows = []
for k in range(int(f1 - f0) + 1):
    sc.frame_set(int(f0) + k)
    r = []
    for s in ('Left', 'Right'):
        pb = rig.pose.bones[s + 'Foot']; h = rig.matrix_world @ pb.head; r.append(h.copy())
    rows.append((k, r, (rig.matrix_world @ rig.pose.bones['Hips'].head).copy()))
for i, s in enumerate(('Left', 'Right')):
    rest = rows[0][1][i]; planted = [r[1][i] for r in rows if r[1][i].z - rest.z < .005]
    drift = max((p - rest).length for p in planted) if planted else 0
    lift = max(r[1][i].z - rest.z for r in rows)
    reach = max((r[1][i] - rest).length for r in rows)
    print(f'FOOT {s}: planted frames {len(planted)}/{len(rows)}, max lift {lift*100:.1f} cm, max travel {reach*100:.1f} cm, '
          f'max drift while at home height {drift*1000:.1f} mm')
print('HIPS end offset mm', round((rows[-1][2] - rows[0][2]).length * 1000, 2), 'max', round(max((r[2] - rows[0][2]).length for r in rows) * 100, 1), 'cm')
