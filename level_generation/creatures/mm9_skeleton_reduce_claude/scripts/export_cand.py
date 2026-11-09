"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, 8 with REA_INFLUENCES=8; no clips), the mesh node named like the installed one so swap_lod0.py can check transforms.
Shading: smooth (default; the reduced faces share vertices, about a quarter of the flat vertex data), or flat
like the Batch E export (every triangle its own face normal) with REA_FLAT=1."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
# Skeleton: the vest, strap and hip-strip linings (stripped before the ladder, strip_lining.py) come back as reversed
# copies of every sheet face (kept or reduced; REA_TAG names work/mesh_r<tag>.npz with its per-face sheet flag), each
# corner on the installed linings' single dark texel (glTF uv 0.6315241, 0.17832583), same weights (duplicated vertices)
if os.environ.get('REA_TAG'):
    import bmesh, numpy as np
    sh = np.load(os.path.join(HERE, 'work', f"mesh_r{os.environ['REA_TAG']}.npz"))['sheet']
    assert len(sh) == len(cand.data.polygons)
    bm = bmesh.new(); bm.from_mesh(cand.data); bm.faces.ensure_lookup_table()
    hit = [bm.faces[i] for i in np.flatnonzero(sh)]
    new = [g for g in bmesh.ops.duplicate(bm, geom=hit)['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=new)
    uvl = bm.loops.layers.uv.active
    for f in new:
        for l in f.loops:
            l[uvl].uv = (0.6315241, 1.0 - 0.17832583)
    bm.to_mesh(cand.data); bm.free(); cand.data.update()
    print('LINING', len(new), 'faces')
# REA_DOUBLES (mm6_hrp_reduce_claude): two-sided faces merged by the source weld get their reversed copy back
if os.environ.get('REA_DOUBLES'):
    import bmesh, numpy as np
    keys = {tuple(map(tuple, k)) for k in np.load(os.environ['REA_DOUBLES'])}
    bm = bmesh.new(); bm.from_mesh(cand.data)
    hit = [f for f in bm.faces if tuple(sorted(tuple(np.round(v.co[:], 5)) for v in f.verts)) in keys]
    new = [g for g in bmesh.ops.duplicate(bm, geom=hit)['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=new)
    bm.to_mesh(cand.data); bm.free(); cand.data.update()
    print('DOUBLED', len(hit), 'of', len(keys))
# soles: the collapse placed a few new sole vertices up to 1.8 mm under the rest floor (source soles sit at z = 0 and
# the Standing/Walking sole gate is 0.0 cm); keeping the sole faces exactly took budget from the torso and failed the
# ladder, so new vertices below the floor are lifted onto it (rest pose = bind pose)
# Igrid: the bind pose is not on z = 0 (the pelvis is at the origin); the floor is the source mesh's lowest point
src_body = bpy.data.objects['Body']; floor_z = min(v.co.z for v in src_body.data.vertices)
low = 0
for v in cand.data.vertices:
    if v.co.z < floor_z:
        v.co.z = floor_z; low += 1
print('FLOOR lifted', low, 'vertices to', round(floor_z, 5))
for poly in cand.data.polygons:
    poly.use_smooth = os.environ.get('REA_FLAT', '0') != '1'
bpy.data.objects['Body'].name = 'Source_Body'; cand.name = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'cand_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=os.environ.get('REA_INFLUENCES', '4') == '8',
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
