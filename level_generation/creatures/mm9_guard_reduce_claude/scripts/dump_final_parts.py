"""Per-face labels of the Guard project's finished master (../mm9_guard_claude/work/final_v1.blend, finish_guard.py output, the
mesh export_guard.py wrote): part (clean_guard NAMES: 1 tunic, 2 face, 3 helmet, 4 hand, 5 pants, 6 boot, 7 skirt, 8 gauntlet,
9 belt, 10 buckle, 11 badge, 13 brooch, 14 fin, 15 bit), head (head texture set), hand (grafted MPFB hands), lining
(finish_guard's inner copies and the shoulder fans), pole (halberd, split off at runtime), rest centroid (Blender frame).
-> work/final_parts.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_guard_claude', 'work', 'final_v1.blend'))
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
n = len(me.polygons)
print('NGON', sum(1 for p in me.polygons if len(p.vertices) != 3))


def attr(name):
    a = np.zeros(n, np.int32)
    if name in me.attributes: me.attributes[name].data.foreach_get('value', a)
    return a


M = np.array(body.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
fv = np.array([p.vertices[:] for p in me.polygons])
gs = None
if 'graft_s' in me.attributes:
    gs = np.zeros(len(me.vertices), np.float32); me.attributes['graft_s'].data.foreach_get('value', gs)
np.savez(os.path.join(HERE, 'work', 'final_parts.npz'), cen=co[fv].mean(1), part=attr('part'), head=attr('head'), hand=attr('hand'),
         lining=attr('lining'), pole=attr('pole'), co=co, fv=fv, graft_s=gs if gs is not None else np.zeros(0))
print('DUMPED', n, {int(k): int((attr('part') == k).sum()) for k in np.unique(attr('part'))}, 'lining', int(attr('lining').sum()),
      'head', int(attr('head').sum()), 'hand', int(attr('hand').sum()), 'pole', int(attr('pole').sum()), 'graft_s', gs is not None)
