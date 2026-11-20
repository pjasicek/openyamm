"""Mirror the knight's left half (+x) onto the right, except both gauntlets (the right one is the fitted sword fist),
with mirrored skin weights (_L_ <-> _R_ groups). The mesh is centred on x = 0 (the rig's mid-plane is within 8 mm).
In: a runtime GLB (LOD0 mesh node REA_NODE, default KnightPlate). Out: work/sym.blend with objects Body and Rig.
Prints the triangle count and the open edges before and after.
Usage: blender -b -P symmetrize.py -- <in.glb>"""
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb = sys.argv[sys.argv.index('--') + 1]
NODE = os.environ.get('REA_NODE', 'KnightPlate')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = bpy.data.objects[NODE]; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o is not body]:
    bpy.data.objects.remove(o, do_unlink=True)
body.name = 'Body'; rig.name = 'Rig'
groups = {g.index: g.name for g in body.vertex_groups}
name_to_index = {g.name: g.index for g in body.vertex_groups}
hand = {i for i, n in groups.items() if '_Hand' in n or '_Finger' in n}

bm = bmesh.new(); bm.from_mesh(body.data)
# weld seam duplicates with identical weights first, so pieces are connected and the mirror seam can weld
dl = bm.verts.layers.deform.active
sig = lambda v: tuple(sorted((g, round(w, 4)) for g, w in v[dl].items()))
classes = {}
for v in bm.verts:
    classes.setdefault(sig(v), []).append(v)
for vs in classes.values():
    bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-6)
open0, tris0 = sum(e.is_boundary for e in bm.edges), len(bm.faces)

# gauntlets: connected pieces whose vertices are mostly hand/finger weighted
bm.faces.ensure_lookup_table()
seen, gauntlet = set(), set()
for f in bm.faces:
    if f.index in seen:
        continue
    stack, piece = [f], []
    seen.add(f.index)
    while stack:
        g = stack.pop(); piece.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen:
                    seen.add(h.index); stack.append(h)
    verts = {v for g in piece for v in g.verts}
    handw = sum(sum(w for k, w in v[dl].items() if k in hand) for v in verts) / len(verts)
    if len(piece) > 300 and handw > .5:
        gauntlet |= {g.index for g in piece}
print('GAUNTLET faces kept', len(gauntlet))

rest = [f for f in bm.faces if f.index not in gauntlet]
geom = list({v for f in rest for v in f.verts}) + list({e for f in rest for e in f.edges}) + rest
before = set(bm.verts)
bmesh.ops.symmetrize(bm, input=geom, direction='X', dist=1e-4)   # 'X': keep +x, mirror to -x
# mirrored vertices are new: swap their left/right weights
swapped = 0
for v in bm.verts:
    if v in before or v.co.x > -1e-5:
        continue
    w = dict(v[dl]); v[dl].clear()
    for k, val in w.items():
        n = groups[k]
        m = n.replace('_L_', '_X_').replace('_R_', '_L_').replace('_X_', '_R_')
        v[dl][name_to_index.get(m, k)] = val
    swapped += 1
bmesh.ops.triangulate(bm, faces=bm.faces)
print('SYM tris', tris0, '->', len(bm.faces), 'open edges', open0, '->', sum(e.is_boundary for e in bm.edges),
      'mirrored verts', swapped)
bm.to_mesh(body.data); bm.free(); body.data.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'sym.blend'))
