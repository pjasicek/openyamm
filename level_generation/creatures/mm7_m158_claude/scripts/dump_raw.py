"""Dump the Meshy return (Blender space: forward -Y, up +Z) to work/raw_<tag>.npz: co, faces, part id per vertex
(connected pieces, largest first). Args: <glb> <tag>."""
import bpy, bmesh, sys, os
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, tag = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(P, src))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
me = mesh.data; me.transform(mesh.matrix_world)
co = np.array([tuple(v.co) for v in me.vertices]); me.calc_loop_triangles()
tri = np.array([tuple(t.vertices) for t in me.loop_triangles])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
part = -np.ones(len(co), int); k = 0; sizes = []
for v in bm.verts:
    if part[v.index] >= 0: continue
    stack = [v]; part[v.index] = k; n = 0
    while stack:
        a = stack.pop(); n += 1
        for e in a.link_edges:
            b = e.other_vert(a)
            if part[b.index] < 0: part[b.index] = k; stack.append(b)
    sizes.append(n); k += 1
order = np.argsort(sizes)[::-1]; remap = np.empty(k, int); remap[order] = np.arange(k)
np.savez(os.path.join(P, f'work/raw_{tag}.npz'), co=co, tri=tri, part=remap[part])
print('DUMP', len(co), len(tri), k)
