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
# soften the ridges and the jagged chest fringe where the fur layers fused
sm = body.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 4
bpy.ops.object.modifier_apply(modifier='smooth')
# QuadriFlow needs a manifold input with consistent normals: split non-manifold vertices (voxel corners where two
# surfaces touch), drop tiny loose islands, recalculate normals
bmc = bmesh.new(); bmc.from_mesh(body.data)
nm = [v for v in bmc.verts if not v.is_manifold]
print('NONMANIFOLD verts', len(nm), 'edges', sum(1 for e in bmc.edges if not e.is_manifold))
if nm:
    bmesh.ops.split_edges(bmc, edges=list({e for v in nm for e in v.link_edges if not e.is_manifold}))
    nm = [v for v in bmc.verts if not v.is_manifold]
    for v in nm:
        bmesh.utils.vert_separate(v, v.link_edges) if len(v.link_faces) else None
# voxel components: the skin plus inner bubbles (closed cavities); keep components above 2 % of the largest
bmc.verts.ensure_lookup_table()
seen2, comps2 = set(), []
for v in bmc.verts:
    if v.index in seen2:
        continue
    c, st = [], [v]; seen2.add(v.index)
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen2:
                seen2.add(y.index); st.append(y)
    comps2.append(c)
comps2.sort(key=len, reverse=True)
print('VOXEL_COMPONENTS', [len(c) for c in comps2[:12]], len(comps2))
for c in comps2[1:4]:
    print('VOXCOMP', len(c), [round(min(v.co[i] for v in c), 3) for i in range(3)], [round(max(v.co[i] for v in c), 3) for i in range(3)])
print('VOXMAIN tail', max(v.co.y for v in comps2[0]), min(v.co.z for v in comps2[0] if v.co.y > 0.44))
drop = [v for c in comps2[1:] if len(c) < 0.02 * len(comps2[0]) for v in c]
bmesh.ops.delete(bmc, geom=drop, context='VERTS')
bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces)
bmc.to_mesh(body.data); bmc.free()
import os
if os.environ.get('CLEAN_MODE', 'quadriflow') == 'quadriflow':
    # uniform quads (no slivers: a decimated voxel surface has slivers that flip under the slightest fit motion)
    r = bpy.ops.object.quadriflow_remesh(target_faces=TARGET, use_preserve_sharp=False, use_preserve_boundary=False,
                                     use_mesh_symmetry=False, smooth_normals=False, seed=0)
    print('QUADRIFLOW', r, len(body.data.polygons))
elif os.environ.get('CLEAN_MODE') == 'none':
    pass   # keep the uniform voxel quads: fit and weight on them, reduce_body.py decimates after weighting
else:
    mod = body.modifiers.new('dec', 'DECIMATE'); mod.ratio = min(1.0, TARGET / max(voxel, 1))
    bpy.ops.object.modifier_apply(modifier='dec')
for p in body.data.polygons:
    p.use_smooth = True
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE')
print('CLEAN', {'main_before': before, 'voxel': voxel, 'main_after': sum(1 for _ in body.data.polygons) - 0,
                'pieces': len(comps) - 1})
