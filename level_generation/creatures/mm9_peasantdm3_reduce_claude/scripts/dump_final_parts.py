"""Per-face labels of the Thrall's finished master (../mm9_thrall_claude/work/uv_v3.blend, the mesh export_thrall.py writes):
part (vertex attribute, per face by majority; fit_thrall/graft_thrall: 0 skin, 1 skirt, 3 belt+knot+rope ends, 5 sandals, 6 collar,
10 face skin, 11 hair, 13 eyes; MPFB hands via the face attribute 'hand'), mat (0 limbs, 1 torso, 2 head), hand, fpart, graft_s
(per face mean of the hand graft's blend coordinate), world-space rest centroid (Blender frame). -> work/final_parts.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_thrall_claude', 'work', 'uv_v3.blend'))
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
n = len(me.polygons); nv = len(me.vertices)
print('ATTRS', [(a.name, a.domain, a.data_type) for a in me.attributes])
def attr(name, dom_n, dt=np.int32):
    a = np.zeros(dom_n, dt)
    if name in me.attributes:
        a = np.zeros(len(me.attributes[name].data), dt); me.attributes[name].data.foreach_get('value', a)
    return a
M = np.array(body.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
fv = [p.vertices[:] for p in me.polygons]
pv = attr('part', nv); gs = attr('graft_s', nv, np.float32) if 'graft_s' in me.attributes else np.zeros(nv, np.float32)
part = np.array([np.bincount(pv[list(f)] + 1).argmax() - 1 for f in fv])
partmax = np.array([pv[list(f)].max() for f in fv])
gsf = np.array([gs[list(f)].mean() for f in fv])
cen = np.array([co[list(f)].mean(0) for f in fv])
ntri = np.array([len(f) - 2 for f in fv])
np.savez(os.path.join(HERE, 'work', 'final_parts.npz'), cen=cen, part=part, partmax=partmax, mat=attr('mat', n),
         hand=attr('hand', n), fpart=attr('fpart', n), graft_s=gsf, co=co, ntri=ntri, vpart=pv)
print('DUMPED', n, 'tris', int(ntri.sum()), {int(k): int((part == k).sum()) for k in np.unique(part)}, 'hand', int(attr('hand', n).sum()),
      'mat', {int(k): int((attr('mat', n) == k).sum()) for k in np.unique(attr('mat', n))})
