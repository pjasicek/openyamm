"""Per-face labels of Krohn's rigged master before the runtime export (../mm9_krohn_claude/work/grip_props_cape.blend): every mesh
object, its face/vertex attributes (lined, head, hand, ...), world rest centroids (Blender z-up frame), triangle counts.
-> work/master_faces.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_krohn_claude', 'work', 'grip_props_cape.blend'))
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for b in o.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    me = o.data
    print('OBJ', o.name, len(me.polygons), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'mats', [m.name for m in me.materials if m],
          'ATTRS', [(a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')])
    M = np.array(o.matrix_world); co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
    fv = [list(p.vertices) for p in me.polygons]
    cen = np.array([co[f].mean(0) for f in fv]); ntri = np.array([len(f) - 2 for f in fv])
    d = dict(cen=cen, ntri=ntri, mat=np.array([p.material_index for p in me.polygons]))
    for a in me.attributes:
        if a.name.startswith('.') or a.data_type not in ('INT', 'FLOAT', 'BOOLEAN', 'INT8'):
            continue
        v = np.zeros(len(a.data), np.float64 if a.data_type == 'FLOAT' else np.int64)
        try:
            a.data.foreach_get('value', v)
        except Exception:
            continue
        if a.domain == 'FACE':
            d['f_' + a.name] = v
        elif a.domain == 'POINT':
            d['v_' + a.name] = np.array([v[f].max() for f in fv])
    for k, v in d.items():
        out[o.name.replace(' ', '_') + '__' + k] = v
np.savez(os.path.join(HERE, 'work', 'master_faces.npz'), **out)
print('KEYS', sorted(out))
