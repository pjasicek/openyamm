"""Which vertices does the skirt cage drive: connected parts with any Skirt_* weight, their size, height range and
mean cage share. Usage: blender -b -P skirt_probe.py -- <glb>"""
import os, sys, bpy, bmesh
import numpy as np
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = bpy.data.objects['Natf']; me = body.data
names = {g.index: g.name for g in body.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.verts.ensure_lookup_table()
# parts on the welded mesh, mapped back by position
import mathutils
co = np.array([v.co[:] for v in me.vertices])
share = np.array([sum(g.weight for g in v.groups if names[g.group].startswith('Skirt_')) for v in me.vertices])
lab = {}
seen = set(); parts = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; comp = []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen.add(o.index); stack.append(o)
    parts.append(comp)
kd = mathutils.kdtree.KDTree(len(co))
for i, c in enumerate(co): kd.insert(c, i)
kd.balance()
for k, comp in enumerate(parts):
    pts = [bm.verts[i].co for i in comp]
    idx = [j for p in pts for (_, j, _) in kd.find_range(p, 1e-6)]
    s = share[idx]
    if s.max() > 0:
        z = co[idx][:, 2]
        print(f'PART {k} verts {len(comp)} z {z.min():.3f}-{z.max():.3f} skirt share mean {s.mean():.2f} max {s.max():.2f} n>0 {(s > 0).sum()}')
print('TOTAL skirt-weighted verts', int((share > 0).sum()), 'of', len(co), 'Z of weighted', co[share > 0][:, 2].min().round(3), co[share > 0][:, 2].max().round(3))
print('GROUPS non-skirt on weighted', sorted({names[g.group] for v in me.vertices if share[v.index] > 0 for g in v.groups if not names[g.group].startswith('Skirt_')}))
