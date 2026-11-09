"""Per-face labels of the Lich's rigged master (../mm9_lich_claude/work/rig_final.blend, the mesh build_export.py writes):
part (prep_v2: 1 pants, 2 cloak (sleeves, cape, hood), 3/10 hands, 4/7 boots, 6 belt, 8 robe, 12/14 small pieces, 30 skull,
40/41/42 linings of hood/robe/boot flares), rest positions (Blender frame, rest pose). -> work/final_parts.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_lich_claude', 'work', 'rig_final.blend'))
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
n = len(me.polygons)
part = np.zeros(n, np.int32); me.attributes['part'].data.foreach_get('value', part)
M = np.array(body.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
fv = np.array([p.vertices[:] for p in me.polygons])
np.savez(os.path.join(HERE, 'work', 'final_parts.npz'), cen=co[fv].mean(1), part=part, lining=(part >= 40).astype(np.int32), co=co, fv=fv)
print('DUMPED', n, {int(k): int((part == k).sum()) for k in np.unique(part)})
