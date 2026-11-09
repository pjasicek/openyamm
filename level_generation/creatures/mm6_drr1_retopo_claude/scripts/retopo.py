"""Retopology pilot for the MM6 Wyrm (GAME_ASSET_MODELLING_GUIDELINES.md section 8).

Input: work/source_snapshot.blend (snapshot of mm6_drr1_claude/export/mm6_wyrm.blend, 14,413 triangles).
Env REA_TARGET = QuadriFlow target faces (quads) for the main body; REA_TAG names the output.
Steps: the largest connected piece (body) is voxel-remeshed into a manifold copy and QuadriFlow-remeshed with X
symmetry and sharp-feature preservation; the result is shrinkwrapped onto the source, gets the source's vertex
weights (Data Transfer, nearest face interpolated, max 8 influences), its material by the nearest source face and new
per-material UVs. The small separate pieces (horns, teeth, spines) keep their own geometry, UVs and weights.
Base colour and tangent normals are baked from the source (Cycles, selected to active, cage extrusion).
Writes work/retopo_<tag>.blend and textures/<tag>_{body,head}_{base,normal}.png."""
import math
import os
import bmesh
import bpy
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = int(os.environ.get('REA_TARGET', '2500'))
TAG = os.environ.get('REA_TAG', f'q{TARGET}')
VOXEL = float(os.environ.get('REA_VOXEL', '0.0025'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_snapshot.blend'))
scene = bpy.context.scene
src = bpy.data.objects['Wyrm']
rig = bpy.data.objects['Wyrm_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


# ---- split the source copy into the main body and the small pieces
work = src.copy(); work.data = src.data.copy(); work.name = 'WorkSplit'
scene.collection.objects.link(work)
work.modifiers.clear(); work.parent = None; work.matrix_world = src.matrix_world.copy()
select_only(work)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new(); bm.from_mesh(work.data); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]; comp = []; seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if w.index not in seen:
                seen.add(w.index); stack.append(w)
    comps.append(comp)
comps.sort(key=len, reverse=True)
main = set(comps[0])
bm.free()
for v in work.data.vertices:
    v.select = v.index not in main
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
body_src = work; body_src.name = 'BodySource'
pieces = next(o for o in bpy.data.objects if o.name.startswith('WorkSplit') or (o.type == 'MESH' and o.name.startswith('BodySource.')))
pieces.name = 'Pieces'

# ---- quad remesh with Instant Meshes (run outside Blender by remesh_im.py on the exported body triangles)
import numpy as np  # noqa: E402
STAGE = os.environ.get('REA_STAGE', 'build')
body_np = os.path.join(HERE, 'work', 'body_in.npz')
quad_np = os.path.join(HERE, 'work', f'body_{TAG}.npz')
if STAGE == 'export':
    me = body_src.data
    verts = np.array([v.co[:] for v in me.vertices], np.float32) @ np.array(body_src.matrix_world.to_3x3()).T.astype(np.float32) \
        + np.array(body_src.matrix_world.translation[:], np.float32)
    tris = []
    for p in me.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1):
            tris.append((vs[0], vs[k], vs[k + 1]))
    np.savez(body_np, verts=verts, faces=np.array(tris, np.uint32))
    print('EXPORTED body', len(verts), 'verts', len(tris), 'tris')
    raise SystemExit(0)
data = np.load(quad_np)
qv, qf = data['verts'], data['faces']
me = bpy.data.meshes.new('BodyRetopo')
me.from_pydata([tuple(v) for v in qv.tolist()], [], [tuple(dict.fromkeys(f)) for f in qf.tolist()])
me.update()
remesh = bpy.data.objects.new('BodyRetopo', me)
scene.collection.objects.link(remesh)
print('INSTANT MESHES faces', len(me.polygons), 'verts', len(me.vertices))
select_only(remesh)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=1e-5)
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_boundary=True, use_multi_face=False,
                                 use_non_contiguous=False, use_verts=False)
bpy.ops.mesh.fill_holes(sides=int(os.environ.get('REA_FILL', '12')))   # remesher leftovers; larger openings follow the source
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- per-region density: the remesh runs at head density; faces away from the head go back to the coarse quads
# Instant Meshes subdivided once (Un-Subdivide on a selection), so the face keeps detail and the body stays light.
FINE = [g for g in os.environ.get('REA_FINE', '').split(',') if g]
if FINE:
    sb = bmesh.new(); sb.from_mesh(body_src.data); sb.faces.ensure_lookup_table()
    stree = BVHTree.FromBMesh(sb)
    fine_idx = {body_src.vertex_groups[g].index for g in FINE}
    def fine_weight(vi):
        return sum(g.weight for g in body_src.data.vertices[vi].groups if g.group in fine_idx)
    face_fine = []
    for f in sb.faces:
        face_fine.append(sum(fine_weight(v.index) for v in f.verts) / len(f.verts))
    select_only(remesh)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    coarse = 0
    for poly in remesh.data.polygons:
        _, _, index, _ = stree.find_nearest(poly.center)
        poly.select = index is None or face_fine[index] < 0.3
        coarse += poly.select
    bpy.ops.object.mode_set(mode='EDIT')
    before = len(remesh.data.polygons)
    bpy.ops.mesh.unsubdivide(iterations=1)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    sb.free()
    print('UNSUBDIVIDE coarse faces', coarse, 'of', before, '->', len(remesh.data.polygons))

# ---- fit onto the source surface
sw = remesh.modifiers.new('Fit', 'SHRINKWRAP')
sw.target = body_src
sw.wrap_method = 'TARGET_PROJECT'
select_only(remesh)
bpy.ops.object.modifier_apply(modifier=sw.name)

# ---- protrusions (horns, spines, tail spikes): source faces standing out from the new smooth surface keep their
# original geometry, UVs, weights and textures; a normal map cannot restore a silhouette (guidelines section 8)
PROTRUDE = float(os.environ.get('REA_PROTRUDE', '0.010'))   # 0 disables layering
rb = bmesh.new(); rb.from_mesh(remesh.data); rb.transform(remesh.matrix_world)
rtree = BVHTree.FromBMesh(rb)
pb = bmesh.new(); pb.from_mesh(body_src.data); pb.verts.ensure_lookup_table(); pb.faces.ensure_lookup_table()
far = {v.index for v in pb.verts if PROTRUDE > 0 and rtree.find_nearest(body_src.matrix_world @ v.co)[3] > PROTRUDE}
spike_faces = {f.index for f in pb.faces if any(v.index in far for v in f.verts)}
for _ in range(2):                         # two rings more, so each spike keeps its whole base under the new skin
    grow = set()
    for fi in spike_faces:
        for v in pb.faces[fi].verts:
            grow.update(f.index for f in v.link_faces)
    spike_faces |= grow
rb.free(); pb.free()
spikes = body_src.copy(); spikes.data = body_src.data.copy(); spikes.name = 'Protrusions'
scene.collection.objects.link(spikes)
select_only(spikes)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in spikes.data.polygons:
    p.select = p.index not in spike_faces
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='FACE'); bpy.ops.object.mode_set(mode='OBJECT')
spike_tris = sum(len(p.vertices) - 2 for p in spikes.data.polygons)
# Kept pieces are simple cones and plates at Meshy density: a collapse reduction keeps their shape, UVs and weights.
KEEP_RATIO = float(os.environ.get('REA_KEEP_RATIO', '0.55'))
for obj in ((spikes, pieces) if KEEP_RATIO < 1.0 else ()):
    dec = obj.modifiers.new('Reduce', 'DECIMATE'); dec.ratio = KEEP_RATIO; dec.use_collapse_triangulate = True
    select_only(obj)
    while obj.modifiers[0] != dec:
        bpy.ops.object.modifier_move_up(modifier=dec.name)
    bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.ops.object.vertex_group_limit_total(limit=8)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
print('PROTRUSIONS faces', len(spike_faces), 'tris', spike_tris, '->', sum(len(p.vertices) - 2 for p in spikes.data.polygons),
      'pieces ->', sum(len(p.vertices) - 2 for p in pieces.data.polygons), 'threshold', PROTRUDE)

# ---- material per face from the nearest source face
sbm = bmesh.new(); sbm.from_mesh(body_src.data); sbm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(sbm)
src_mats = [f.material_index for f in sbm.faces]
for m in src.data.materials:
    remesh.data.materials.append(m)
for poly in remesh.data.polygons:
    _, _, index, _ = tree.find_nearest(poly.center)
    poly.material_index = src_mats[index] if index is not None else 0
sbm.free()

# ---- triangulate (baker and engine see the same triangles), smooth shading
select_only(remesh)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
for p in remesh.data.polygons:
    p.use_smooth = True

# ---- weights from the source (data transfer, nearest face interpolated), max 8, normalised
for g in body_src.vertex_groups:
    remesh.vertex_groups.new(name=g.name)
dt = remesh.modifiers.new('Weights', 'DATA_TRANSFER')
dt.object = body_src
dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'
dt.layers_vgroup_select_dst = 'NAME'
select_only(remesh)
bpy.ops.object.modifier_apply(modifier=dt.name)
bpy.ops.object.vertex_group_limit_total(limit=8)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
unweighted = sum(1 for v in remesh.data.vertices if not v.groups)
print('UNWEIGHTED', unweighted)

# ---- new UVs per material (each texture set fills its own 0..1)
uv = remesh.data.uv_layers[0] if remesh.data.uv_layers else remesh.data.uv_layers.new(name='UVMap')
for slot in range(len(remesh.data.materials)):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in remesh.data.polygons:
        p.select = p.material_index == slot
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')

# ---- bake base colour and normal from the source body (rest pose) into new images
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
bake_mats = {}
sizes = {'Wyrm': 2048, 'WyrmHead': 1024}
for slot, mat in enumerate(list(remesh.data.materials)):
    new = bpy.data.materials.new(f'{mat.name}_retopo'); new.use_nodes = True
    nt = new.node_tree
    imgs = {}
    for kind, colorspace in (('base', 'sRGB'), ('normal', 'Non-Color')):
        size = sizes[mat.name] if kind == 'base' else 1024
        img = bpy.data.images.new(f'{TAG}_{"head" if "Head" in mat.name else "body"}_{kind}', size, size)
        img.colorspace_settings.name = colorspace
        node = nt.nodes.new('ShaderNodeTexImage'); node.image = img; node.name = kind
        imgs[kind] = (img, node)
    remesh.data.materials[slot] = new
    bake_mats[new.name] = imgs
cage = 0.004
for kind, bake_type in (('base', 'DIFFUSE'), ('normal', 'NORMAL')):
    for name, imgs in bake_mats.items():
        bpy.data.materials[name].node_tree.nodes.active = imgs[kind][1]
    bpy.ops.object.select_all(action='DESELECT')
    body_src.select_set(True); remesh.select_set(True)
    bpy.context.view_layer.objects.active = remesh
    # short rays: the smooth surface lies on the source, and a long ray reaches the neighbouring leg
    # Rays start 5 mm outside the low surface (cage extrusion) and reach 15 mm in: covers where the low surface
    # sits away from the source (inner thighs) without crossing to the neighbouring leg.
    kw = dict(type=bake_type, use_selected_to_active=True, use_cage=False, cage_extrusion=0.005,
              max_ray_distance=0.015, margin=8, margin_type='EXTEND')
    if bake_type == 'DIFFUSE':
        kw['pass_filter'] = {'COLOR'}
    else:
        kw['normal_space'] = 'TANGENT'
    bpy.ops.object.bake(**kw)
os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
for imgs in bake_mats.values():
    for img, _ in imgs.values():
        img.filepath_raw = os.path.join(HERE, 'textures', img.name + '.png'); img.file_format = 'PNG'; img.save()

# ---- final materials: baked base + normal on a Principled shader
for name, imgs in bake_mats.items():
    nt = bpy.data.materials[name].node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    nt.links.new(imgs['base'][1].outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(imgs['normal'][1].outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.7

# ---- join the kept pieces, parent to the rig
pieces_copy = pieces
select_only(remesh)
pieces_copy.select_set(True)
spikes.select_set(True)
bpy.context.view_layer.objects.active = remesh
bpy.ops.object.join()
remesh.name = f'Wyrm_{TAG}'
remesh.parent = rig
mod = remesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
for o in (body_src,):
    bpy.data.objects.remove(o, do_unlink=True)
tris = sum(len(p.vertices) - 2 for p in remesh.data.polygons)
print('RESULT', TAG, 'tris', tris, 'verts', len(remesh.data.vertices), 'unweighted', unweighted)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'retopo_{TAG}.blend'))
