"""Per-face labels of PeasantM2d's last master before export (../mm9_peasantm2d_claude/work/final_v2.blend, opened read-only,
never saved): face attributes part (clean_pm2 NAMES: 1 tunic, 4 hand, 5 trousers, 6 boot, 7 skirt, 9 strap/belt, 10 buckle,
20 face, 21 hair, 22 lips/eyes; 22 = ears per add_ears), mat (0 limbs, 1 torso, 2 head), lining (1 skirt+cuff lining 3 mm,
2 skirt cap, 3 hair lining 2 mm, 4 upper-tunic lining 3 mm), hand, ear; world-space rest centroid (Blender frame, z up).
-> work/final_parts.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_peasantm2d_claude', 'work', 'final_v2.blend'))
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig and rig.animation_data: rig.animation_data.action = None
if rig:
    for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
n = len(me.polygons); nv = len(me.vertices)
print('ATTRS', [(a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')])
def fattr(name):
    if name not in me.attributes: return np.zeros(n, np.int32)
    a = me.attributes[name]
    x = np.zeros(len(a.data), np.int32); a.data.foreach_get('value', x)
    if a.domain == 'POINT':
        fv = [p.vertices[:] for p in me.polygons]
        return np.array([np.bincount(x[list(f)] - x.min()).argmax() + x.min() for f in fv])
    return x
M = np.array(body.matrix_world)
co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
fv = [p.vertices[:] for p in me.polygons]
cen = np.array([co[list(f)].mean(0) for f in fv]); ntri = np.array([len(f) - 2 for f in fv])
out = dict(cen=cen, ntri=ntri, co=co, mat=np.array([p.material_index for p in me.polygons]))
for k in ('part', 'lining', 'hand', 'ear', 'mat'):
    if k in me.attributes: out[k if k != 'mat' else 'mat_attr'] = fattr(k)
np.savez(os.path.join(HERE, 'work', 'final_parts.npz'), **out)
print('DUMPED', n, 'tris', int(ntri.sum()), 'mats', [m.name for m in me.materials])
for k in ('part', 'lining', 'hand', 'ear'):
    if k in out: print(k, {int(a): int((out[k] == a).sum()) for a in np.unique(out[k])})
