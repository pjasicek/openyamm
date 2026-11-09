"""Print size, piece list and orientation hints of the Smart Topology head returns. Args: -- k [k ...]"""
import bpy, sys, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for k in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', f'head{k}_smart_topology_v1', 'model_urls_glb.glb'))
    ob = next(o for o in bpy.data.objects if o.type == 'MESH'); ob.parent = None
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    co = np.array([tuple(v.co) for v in ob.data.vertices])
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    import collections
    lab = {}; n = 0
    for v in bm.verts:
        if v in lab: continue
        st = [v]; lab[v] = n
        while st:
            a = st.pop()
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in lab: lab[b] = n; st.append(b)
        n += 1
    cnt = collections.Counter(lab.values())
    print(f'HEAD {k}: verts {len(co)} tris {sum(len(p.vertices)-2 for p in ob.data.polygons)} min {co.min(0).round(3)} max {co.max(0).round(3)} pieces {n} largest {cnt.most_common(6)} lowest-z centroid {co[co[:,2]<co[:,2].min()+0.03].mean(0).round(3)} min-y vertex {co[np.argmin(co[:,1])].round(3)}')
