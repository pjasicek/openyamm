"""Right-arm carry probe: per clip frame the world shoulder, elbow, wrist and fist centre (handle centre), the elbow's
lateral offset from the shoulder (flare, cm), the fist's distance outside the dress surface (cm, nearest skirt face,
signed by its normal) and the dagger direction. Also the rest-pose skirt half-width on her right at fist heights.
Args: -- <blend> [action ...]"""
import bpy, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); acts = a[1:] or ['Standing', 'Walking', 'Running']
P = Path(__file__).resolve().parents[1]
G = json.loads((P / 'work/grip_pose.json').read_text()); GC = Vector(G['handle_centre_hand_local'])
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([v.co[:] for v in me.vertices])
for z in (0.80, 0.85, 0.90, 0.95, 1.00):
    m = (pv == 0) & (np.abs(co[:, 2] - z) < 0.01) & (co[:, 0] < 0) & (np.abs(co[:, 1]) < 0.12)
    print('SKIRT z', z, 'right half-width cm', round(float(-co[m, 0].min()) * 100, 1) if m.any() else None)
W = lambda n: rig.matrix_world @ rig.pose.bones[n].matrix
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); rows = []
    for f in range(f0, f1 + 1, max(1, (f1 - f0) // 6)):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        tree = BVHTree.FromPolygons([body.matrix_world @ v.co for v in m.vertices],
                                    [p.vertices[:] for p in m.polygons if pv[p.vertices[0]] == 0 and m.vertices[p.vertices[0]].co.z < 1.05])
        ev.to_mesh_clear()
        S = W('B_R_UpperArm').translation; E = W('B_R_Forearm').translation; Wr = W('B_R_Hand').translation
        F = W('B_R_Hand') @ GC; loc, n, i, d = tree.find_nearest(F); sd = d if (F - loc).dot(n) >= 0 else -d
        D = (W('Dagger').to_3x3() @ Vector((0, 1, 0))) if 'Dagger' in rig.pose.bones else Vector()
        if f == f0:
            print('JOINTS', name, 'shoulder', [round(x, 3) for x in S], 'elbow', [round(x, 3) for x in E], 'wrist', [round(x, 3) for x in Wr],
                  'upper/fore len', round((E - S).length, 3), round((Wr - E).length, 3), 'S-W', round((Wr - S).length, 3))
        rows.append(f"f{f}: elbow flare {(S.x - E.x) * 100:+.1f} wrist ({Wr.x:+.2f},{Wr.y:+.2f},{Wr.z:.2f}) fist out {sd * 100:+.1f}cm "
                    f"dagger ({D.x:+.2f},{D.y:+.2f},{D.z:+.2f})")
    print('CARRY', name, ' | '.join(rows))
