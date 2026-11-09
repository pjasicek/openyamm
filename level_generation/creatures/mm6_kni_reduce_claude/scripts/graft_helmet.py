"""Replace the knight's helmet pieces (shell, T-visor, side bolts, upright horns, ram horns) on work/sym.blend with
a reduced Meshy helmet (skull mask, crest, upright and ram horns), rigid on B_Head. The new helmet is fitted to the
old pieces' rest-pose bounding box (uniform scale from the height, centred on x = 0 and the old box's y/z centre,
then a small x/y scale so width and depth match too); the hair stays.
In: work/sym.blend, a helmet GLB (one mesh, its own UVs and material). Out: work/graft.blend (Body with material
slot 0 body, slot 1 helmet; face attribute 'helmet'), printed fit.
Usage: blender -b -P graft_helmet.py -- <helmet.glb> [y_shift_m]"""
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
helmet_glb = os.path.abspath(args[0]); y_shift = float(args[1]) if len(args) > 1 else 0.0
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'sym.blend'))
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
head_index = body.vertex_groups['B_Head'].index

bm = bmesh.new(); bm.from_mesh(body.data); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
names = {g.index: g.name for g in body.vertex_groups}
# pieces above the collar that belong to the helmet: head/neck weighted, not the hair (largest, reaches the waist)
seen, remove, old_pts = set(), [], []
for f in bm.faces:
    if f.index in seen:
        continue
    stack, piece = [f], []; seen.add(f.index)
    while stack:
        g = stack.pop(); piece.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen:
                    seen.add(h.index); stack.append(h)
    vs = list({v for g in piece for v in g.verts}); co = np.array([v.co[:] for v in vs])
    w = {}
    for v in vs:
        for k, x in v[dl].items():
            w[names[k]] = w.get(names[k], 0) + x
    dom = max(w, key=w.get)
    if co[:, 2].mean() > 1.5 and dom in ('B_Head', 'B_Neck') and np.ptp(co[:, 2]) < .5:
        remove += piece; old_pts.append(co)
old = np.concatenate(old_pts); lo, hi = old.min(0), old.max(0)
print('REMOVE', len(remove), 'faces; old helmet box', lo.round(3), hi.round(3))
bmesh.ops.delete(bm, geom=remove, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(body.data); bm.free()

names_before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=helmet_glb)
hel = next(o for o in bpy.data.objects if o.name not in names_before and o.type == 'MESH')
for o in [o for o in bpy.data.objects if o.name not in names_before and o is not hel]:
    bpy.data.objects.remove(o, do_unlink=True)
hel.data.transform(hel.matrix_world); hel.matrix_world = Matrix.Identity(4); hel.parent = None
hco = np.array([v.co[:] for v in hel.data.vertices]); hlo, hhi = hco.min(0), hco.max(0)
# uniform scale (a box fit squashed the wide ram horns to half width): FIT=depth matches the face-to-back depth of
# the old helmet, FIT=height the old height, a number scales the depth fit; the rim sits at the old rim height
mode = os.environ.get('FIT', 'depth')
s_depth = (hi[1] - lo[1]) / (hhi[1] - hlo[1]); s_height = (hi[2] - lo[2]) / (hhi[2] - hlo[2])
s = s_height if mode == 'height' else s_depth * (float(mode) if mode not in ('depth', 'height') else 1.0)
z_lift = float(os.environ.get('Z_LIFT', '0'))
M = (Matrix.Translation(Vector((0, hi[1] - s * hhi[1] + y_shift, lo[2] - s * hlo[2] + z_lift)))
     @ Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(Vector((-(hlo[0] + hhi[0]) / 2, 0, 0))))
hel.data.transform(M)
nco = np.array([v.co[:] for v in hel.data.vertices])
print('FIT', mode, 'scale', round(s, 4), 'new box', nco.min(0).round(3), nco.max(0).round(3))
# The v1 hair is a tall plume that arches forward over the head (Hit, Fidget) and rose above the new horns. Keep it
# as hair falling from the back of the helmet: above CAP_Z it is squashed into a low cap behind the helmet (y >= 3 cm),
# and from BLEND_Z up it follows the rigid helmet (B_Head). HAIR_TOP=0 keeps it unchanged.
if os.environ.get('HAIR_TOP', '1') != '0':
    CAP_Z, CAP_K, BLEND_Z = 1.62, .25, (1.50, 1.58)
    bmh = bmesh.new(); bmh.from_mesh(body.data); dlh = bmh.verts.layers.deform.active; bmh.verts.ensure_lookup_table()
    seen, pieces = set(), []
    for v0 in bmh.verts:
        if v0.index in seen:
            continue
        stack, piece = [v0], []; seen.add(v0.index)
        while stack:
            v = stack.pop(); piece.append(v)
            for e in v.link_edges:
                u = e.other_vert(v)
                if u.index not in seen:
                    seen.add(u.index); stack.append(u)
        pieces.append(piece)
    hair = max((p for p in pieces if min(v.co.z for v in p) > .9 and max(v.co.z for v in p) - min(v.co.z for v in p) > .5
                and np.mean([v.co.y for v in p]) > .05), key=len)
    for v in hair:
        if v.co.z > CAP_Z:
            v.co.z = CAP_Z + (v.co.z - CAP_Z) * CAP_K; v.co.y = max(v.co.y, .03)
        f = min(max((v.co.z - BLEND_Z[0]) / (BLEND_Z[1] - BLEND_Z[0]), 0.0), 1.0)
        w = {k: x * (1 - f) for k, x in v[dlh].items()}
        w[head_index] = w.get(head_index, 0.0) + f
        v[dlh].clear()
        for k, x in w.items():
            if x > 1e-4:
                v[dlh][k] = x
    print('HAIR', len(hair), 'verts, top now', round(max(v.co.z for v in hair), 3))
    bmh.to_mesh(body.data); bmh.free()
# attribute and rigid weights on the head (the join appends the helmet's material as slot 1)
hel.data.attributes.new('helmet', 'BOOLEAN', 'FACE').data.foreach_set('value', [True] * len(hel.data.polygons))
g = hel.vertex_groups.new(name='B_Head'); g.add(list(range(len(hel.data.vertices))), 1.0, 'REPLACE')
if 'helmet' not in body.data.attributes:
    body.data.attributes.new('helmet', 'BOOLEAN', 'FACE')
for o in bpy.data.objects:
    o.select_set(False)
hel.select_set(True); body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('GRAFT tris', sum(len(p.vertices) - 2 for p in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'graft.blend'))
