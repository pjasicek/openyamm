"""Per-face labels of the creature project's finished master (../mm9_nobleman_claude/work/final_v1.blend, finish_hw.py output,
the mesh export_hw.py wrote): part (clean_hw NAMES; 20 face, 21 hair, 22 eyes, 30 weapons), mat (0 limbs, 1 torso, 2 head,
3 weapons), lining (finish_hw's inner copies), weapon (1 sword, 2 dagger), world-space rest centroid (Blender frame) and
PartUV per corner. -> work/final_parts.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_nobleman_claude', 'work', 'final_v1.blend'))
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
n = len(me.polygons)
def attr(name):
    a = np.zeros(n, np.int32)
    if name in me.attributes: me.attributes[name].data.foreach_get('value', a)
    return a
M = np.array(body.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
fv = np.array([p.vertices[:] for p in me.polygons])
uvl = me.uv_layers['PartUV'].data
uv = np.array([[uvl[l].uv[:] for l in p.loop_indices] for p in me.polygons])
np.savez(os.path.join(HERE, 'work', 'final_parts.npz'), cen=co[fv].mean(1), part=attr('part'), mat=attr('mat'),
         lining=attr('lining'), weapon=attr('weapon'), uv=uv, co=co, fv=fv)
print('DUMPED', n, {int(k): int((attr('part') == k).sum()) for k in np.unique(attr('part'))}, 'lining', int(attr('lining').sum()))
