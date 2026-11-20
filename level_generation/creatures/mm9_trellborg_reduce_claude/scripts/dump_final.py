"""Dump the creature project's final rest mesh (../mm9_trellborg_claude/work/final_c.blend, object Body) for face labels:
per face the rest corner positions, every int face attribute (part, mat, ...). -> work/final_faces.npz. Read only."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_trellborg_claude', 'work', 'final_c.blend'))
print('OBJECTS', [(o.name, o.type, len(o.data.polygons) if o.type == 'MESH' else 0) for o in bpy.data.objects])
body = bpy.data.objects['Body']; me = body.data
me.calc_loop_triangles()
print('ATTRS', [(a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')])
print('MATS', [m.name for m in me.materials], 'MODS', [m.type for m in body.modifiers])
P = np.array([v.co[:] for v in me.vertices]); tri = np.array([t.vertices[:] for t in me.loop_triangles]); poly = np.array([t.polygon_index for t in me.loop_triangles])
out = dict(co=P[tri], tri=tri, poly=poly, matidx=np.array([t.material_index for t in me.loop_triangles]))
for a in me.attributes:
    if a.name.startswith('.') or a.data_type not in ('INT', 'FLOAT', 'BOOLEAN', 'INT8'): continue
    vals = np.array([d.value for d in a.data])
    if a.domain == 'FACE': out['f_' + a.name] = vals[poly]
    elif a.domain == 'POINT': out['v_' + a.name] = vals
np.savez(os.path.join(HERE, 'work', 'final_faces.npz'), **out)
print('DUMP', len(tri), {k: v.shape for k, v in out.items()})
