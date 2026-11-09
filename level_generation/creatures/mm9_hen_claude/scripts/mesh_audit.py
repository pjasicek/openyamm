"""Open/non-manifold edge audit: args <glb|blend> [object name]. Prints counts and boundary loop centres/sizes."""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
if a[0].endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=a[0])
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
ob = bpy.data.objects[a[1]] if len(a) > 1 else next(o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Ico'))
bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
bnd = [e for e in bm.edges if e.is_boundary]
nm = [e for e in bm.edges if len(e.link_faces) > 2]
es = set(bnd); seen = set(); loops = []
for e in bnd:
    if e in seen:
        continue
    st, lp = [e], []; seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y in es and y not in seen:
                    seen.add(y); st.append(y)
    loops.append(lp)
print('AUDIT', ob.name, 'verts', len(bm.verts), 'faces', len(bm.faces), 'open', len(bnd), 'nonmanifold', len(nm), 'loops', len(loops))
for lp in sorted(loops, key=len, reverse=True)[:12]:
    P = np.array([tuple(v.co) for e in lp for v in e.verts])
    print('  loop', len(lp), 'centre', P.mean(0).round(3), 'size', np.ptp(P, 0).round(3))
if nm:
    P = np.array([tuple(v.co) for e in nm for v in e.verts])
    print('  nonmanifold centre', P.mean(0).round(3), 'min', P.min(0).round(3), 'max', P.max(0).round(3))
