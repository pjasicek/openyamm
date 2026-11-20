"""Rebuild the Meshy body as one clean closed surface: the main component is voxel-remeshed (the Smart Topology return
has overlapping fur layers on the chest and neck and a hidden inner shell, a third of its area) and rebuilt as uniform quads
(QuadriFlow, the target face count); the small separate pieces (teeth, claws, eyes) are kept as returned.
A light smooth (factor 0.5, 4 iterations) softens the seams where the fur layers fused.
Args: <meshy glb> <out glb> <voxel size> <target faces>"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, VOX, TARGET = argv[0], argv[1], float(argv[2]), int(argv[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
# sheep: Meshy spun a 0.5-unit thread from the chin to a front hoof (31 sliver faces); drop faces with an edge over
# six times the median, then loose vertices, before the voxel rebuild closes the holes
import numpy as _np
_med = float(_np.median([e.calc_length() for e in bm.edges]))
_bad = [f for f in bm.faces if max(e.calc_length() for e in f.edges) > 6 * _med]
bmesh.ops.delete(bm, geom=_bad, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print('THREAD faces removed', len(_bad))
# close the holes (ear sockets, chin, chest, tail) so the voxel rebuild sees a closed volume, not a thin sheet
_bd = [e for e in bm.edges if len(e.link_faces) == 1]
_fill = bmesh.ops.holes_fill(bm, edges=_bd, sides=0)
print('HOLES filled', len(_fill['faces']))
bm.verts.ensure_lookup_table()
seen, comps = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
print('COMPONENTS', [len(c) for c in comps[:8]])
main = set(comps[0])
# thread remnants (tiny separate pieces) are dropped
for c in comps[1:]:
    if len(c) < 60:
        bmesh.ops.delete(bm, geom=[bm.verts[i] for i in c], context='VERTS')
bm.verts.ensure_lookup_table(); bm.verts.index_update()
seen, comps = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
main = set(comps[0])


def make(name, keep):
    b2 = bm.copy()
    b2.verts.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if (v.index in main) != keep], context='VERTS')
    me = bpy.data.meshes.new(name); b2.to_mesh(me)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


body = make('Body', True)
pieces = make('Pieces', False)
for o in list(bpy.data.objects):
    if o not in (body, pieces):
        bpy.data.objects.remove(o)
before = len(body.data.polygons)
body.data.remesh_voxel_size = VOX
body.data.remesh_voxel_adaptivity = 0.0
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.voxel_remesh()
voxel = len(body.data.polygons)
# report the voxel components (a hollow shell shows as two nested components of similar size)
_b = bmesh.new(); _b.from_mesh(body.data); _b.verts.ensure_lookup_table()
_seen, _cs = set(), []
for _v in _b.verts:
    if _v.index in _seen:
        continue
    _c, _st = 0, [_v]; _seen.add(_v.index)
    while _st:
        _x = _st.pop(); _c += 1
        for _e in _x.link_edges:
            _y = _e.other_vert(_x)
            if _y.index not in _seen:
                _seen.add(_y.index); _st.append(_y)
    _cs.append(_c)
print('VOXEL components', sorted(_cs, reverse=True)[:6])
# soften the ridges and the jagged chest fringe where the fur layers fused
sm = body.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 4
bpy.ops.object.modifier_apply(modifier='smooth')
import os
if os.environ.get('CLEAN_MODE', 'quadriflow') == 'quadriflow':
    # uniform quads (no slivers: a decimated voxel surface has slivers that flip under the slightest fit motion)
    bpy.ops.object.quadriflow_remesh(target_faces=TARGET, use_preserve_sharp=False, use_preserve_boundary=False,
                                     use_mesh_symmetry=False, smooth_normals=False, seed=0)
elif os.environ.get('CLEAN_MODE') == 'none':
    pass   # keep the uniform voxel quads: fit and weight on them, reduce_body.py decimates after weighting
else:
    mod = body.modifiers.new('dec', 'DECIMATE'); mod.ratio = min(1.0, TARGET / max(voxel, 1))
    bpy.ops.object.modifier_apply(modifier='dec')
for p in body.data.polygons:
    p.use_smooth = True
# sheep: the ears come back as open single sheets (the engine culls back faces): give them a closed 2.5 mm shell
if len(pieces.data.vertices) and float(os.environ.get('PIECE_SHELL', '0.0025')) > 0:
    sol = pieces.modifiers.new('shell', 'SOLIDIFY'); sol.thickness = float(os.environ.get('PIECE_SHELL', '0.0025'))
    sol.offset = 0.0; sol.use_rim = True; sol.use_even_offset = True
    bpy.context.view_layer.objects.active = pieces
    for o in bpy.data.objects:
        o.select_set(o == pieces)
    bpy.ops.object.modifier_apply(modifier='shell')
    for p in pieces.data.polygons:
        p.use_smooth = True
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE')
print('CLEAN', {'main_before': before, 'voxel': voxel, 'main_after': sum(1 for _ in body.data.polygons) - 0,
                'pieces': len(comps) - 1})
