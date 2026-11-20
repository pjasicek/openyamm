"""Rebuild the Meshy body as one clean closed surface: the main component is voxel-remeshed (the Smart Topology return
has overlapping fur layers on the chest and neck and a hidden inner shell, a third of its area) and rebuilt as uniform quads
(QuadriFlow, the target face count); the small separate pieces (teeth, claws, eyes) are kept as returned.
A light smooth (factor 0.5, 4 iterations) softens the seams where the fur layers fused.
Args: <meshy glb> <out glb> <voxel size> <target faces>   env STRAND_BOX / STRAND_THICK: see below
"""
import bpy, bmesh, sys, os
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, VOX, TARGET = argv[0], argv[1], float(argv[2]), int(argv[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
import os
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
dropped = 0
if os.environ.get('KEEP_PIECES'):
    # keep only the N largest separate pieces (the cat's eyes); the rest (whisker threads) are dropped
    keep_n = int(os.environ['KEEP_PIECES'])
    drop = [i for c in comps[1 + keep_n:] for i in c]
    dropped = len(comps) - 1 - keep_n
    bm.verts.ensure_lookup_table()
    dv = set(drop)
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in drop], context='VERTS')
    bm.verts.ensure_lookup_table()
    old = sorted(set(range(len(bm.verts) + len(dv))) - dv)
    remap = {o: k for k, o in enumerate(old)}
    main = set(remap[i] for i in comps[0])
    comps = [[remap[i] for i in c] for c in comps[:1 + keep_n]]


def make(name, keep):
    b2 = bm.copy()
    b2.verts.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if (v.index in main) != keep], context='VERTS')
    me = bpy.data.meshes.new(name); b2.to_mesh(me)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


strands = 0


def comps_of(b3):
    b3.verts.ensure_lookup_table()
    seen2, out = set(), []
    for v in b3.verts:
        if v.index in seen2:
            continue
        cc, st = [], [v]; seen2.add(v.index)
        while st:
            x = st.pop(); cc.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen2:
                    seen2.add(y.index); st.append(y)
        out.append(cc)
    return out


def keep_largest(b3):
    big = set(max(comps_of(b3), key=len))
    bmesh.ops.delete(b3, geom=[v for v in b3.verts if v not in big], context='VERTS')


def fan_fill(b3):
    """Close every boundary loop with a triangle fan to its centroid (holes_fill leaves ragged loops open)."""
    used, loops = set(), 0
    for e0 in [e for e in b3.edges if len(e.link_faces) == 1]:
        if e0 in used:
            continue
        loop, e, v = [], e0, e0.verts[0]
        while e not in used:
            used.add(e); loop.append(v)
            v = e.other_vert(v)
            nxt = [x for x in v.link_edges if len(x.link_faces) == 1 and x not in used]
            if not nxt:
                break
            e = nxt[0]
        if len(loop) < 3:
            continue
        cen = b3.verts.new(sum((x.co for x in loop), loop[0].co * 0) / len(loop))
        for k in range(len(loop)):
            try:
                b3.faces.new((loop[k], loop[(k + 1) % len(loop)], cen))
            except ValueError:
                pass
        loops += 1
    bmesh.ops.recalc_face_normals(b3, faces=b3.faces)
    return loops


body = make('Body', True)
# the raw shell is open in places (cat: 308 boundary edges): an open shell voxelises as a thin double wall (the flood
# leaks inside), so its holes are closed first: bow-tie vertices cut, every boundary loop fan-filled
b5 = bmesh.new(); b5.from_mesh(body.data)
raw_boundary = sum(1 for e in b5.edges if len(e.link_faces) == 1)
for _ in range(10):
    nm = [v for v in b5.verts if not v.is_manifold]
    if not nm:
        break
    bmesh.ops.delete(b5, geom=nm, context='VERTS')
    keep_largest(b5)
raw_loops = fan_fill(b5)
b5.to_mesh(body.data); b5.free()
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
import os
# Meshy threads (thin strands between the legs, kept as thin tubes by the voxel pass): inside STRAND_BOX
# (x0,x1,y0,y1,z0,z1, Meshy units) every vertex whose inward ray leaves the surface within STRAND_THICK goes; the
# openings are filled and the body is voxelised again, so it stays one closed surface
if os.environ.get('STRAND_BOX'):
    from mathutils.bvhtree import BVHTree
    bx = [float(x) for x in os.environ['STRAND_BOX'].split(',')]
    thick = float(os.environ.get('STRAND_THICK', '0.008'))
    b3 = bmesh.new(); b3.from_mesh(body.data); b3.normal_update()
    keep_largest(b3)
    tree = BVHTree.FromBMesh(b3)
    bad = [v for v in b3.verts if bx[0] < v.co.x < bx[1] and bx[2] < v.co.y < bx[3] and bx[4] < v.co.z < bx[5]
           and tree.ray_cast(v.co - v.normal * 1e-4, -v.normal, thick)[0] is not None]
    strands = len(bad)
    bmesh.ops.delete(b3, geom=bad, context='VERTS')
    keep_largest(b3)
    for _ in range(10):   # bow-tie vertices where the strands left: cut them so every boundary is one simple loop
        nm = [v for v in b3.verts if not v.is_manifold]
        if not nm:
            break
        bmesh.ops.delete(b3, geom=nm, context='VERTS')
        keep_largest(b3)
    filled = fan_fill(b3)
    assert not any(len(e.link_faces) == 1 for e in b3.edges), 'strand cut left open edges'
    b3.to_mesh(body.data); b3.free()
    bpy.ops.object.voxel_remesh()
    sm = body.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 2
    bpy.ops.object.modifier_apply(modifier='smooth')
# voxel bubbles (closed inner shells) go: the body is its largest component
b4 = bmesh.new(); b4.from_mesh(body.data)
bubbles = len(comps_of(b4)) - 1
keep_largest(b4); b4.to_mesh(body.data); b4.free()
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
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE')
print('CLEAN', {'raw_boundary': raw_boundary, 'raw_loops_filled': raw_loops, 'bubbles': bubbles, 'pieces_dropped': dropped, 'strand_verts': strands, 'main_before': before, 'voxel': voxel, 'main_after': sum(1 for _ in body.data.polygons) - 0,
                'pieces': len(comps) - 1})
