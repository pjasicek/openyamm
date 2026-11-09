"""Print attributes, materials, part counts of the creature's build-default master (opened read-only, never saved)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_peasantm3_claude', 'work', 'neck_v5.blend'))
for o in bpy.data.objects:
    print('OBJ', o.name, o.type, o.parent.name if o.parent else None, len(o.data.polygons) if o.type == 'MESH' else '')
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    me = o.data
    print('MESH', o.name, 'mats', [m.name for m in me.materials], 'uv', [u.name for u in me.uv_layers])
    for a in me.attributes:
        if a.name.startswith('.'): continue
        info = ''
        if a.data_type in ('INT', 'BOOLEAN', 'INT8'):
            x = np.array([d.value for d in a.data]); u, c = np.unique(x, return_counts=True); info = dict(zip(u.tolist(), c.tolist()))
        print('  ATTR', a.name, a.domain, a.data_type, info)
    mi = np.array([p.material_index for p in me.polygons]); ntri = np.array([len(p.vertices) - 2 for p in me.polygons])
    print('  tris per mat', {int(m): int(ntri[mi == m].sum()) for m in np.unique(mi)})
