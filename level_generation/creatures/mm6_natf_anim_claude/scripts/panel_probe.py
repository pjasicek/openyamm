"""Skirt panel structure: welded parts among cage-driven faces, boundary loops, and per part how many vertices lie
under another skirt layer (a ray along the vertex normal hits skirt within 3 cm) or above one (ray inward).
Usage: blender -b -P panel_probe.py -- <blend>"""
import os, sys, bpy, bmesh
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
body = bpy.data.objects['Body']; me = body.data
names = {g.index: g.name for g in body.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
z = lambda f: f.calc_center_median().z
# skirt faces: between hem and waist, belonging to the big parts that contain the skirt region
parts = []; seen = set()
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; comp = []; seen.add(f.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.edges:
            for o in e.link_faces:
                if o.index not in seen: seen.add(o.index); st.append(o)
    parts.append(comp)
parts.sort(key=len, reverse=True)
for k, comp in enumerate(parts[:4]):
    sk = [f for f in comp if 0.5 < z(f) < 0.92]
    if not sk: continue
    tree = BVHTree.FromBMesh(bm)
    vs = {v for f in sk for v in f.verts}
    under = above = 0
    for v in vs:
        hit = tree.ray_cast(v.co + v.normal * 1e-4, v.normal, 0.03)
        if hit[0] is not None: under += 1
        hit = tree.ray_cast(v.co - v.normal * 1e-4, -v.normal, 0.03)
        if hit[0] is not None: above += 1
    edges = {e for f in sk for e in f.edges if e.is_boundary}
    print(f'PART {k} faces {len(comp)} skirt-zone faces {len(sk)} verts {len(vs)} under-a-layer {under} above-a-layer {above} boundary edges {len(edges)}')
