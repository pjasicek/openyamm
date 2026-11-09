"""UV-preserving reduction ladder for a rigged creature (pilot: MM6 Fire Lizard `drag`).

Quadric collapse (Blender Decimate) on the existing mesh keeps its UVs, textures and skin weights, so nothing is
re-textured. Head/Jaw are protected through a weight group, the collapse is X-symmetric, influences are limited to 4.
For each ratio: triangles, open edges, two-way surface error against the source over every 3rd frame of every
clip (candidate -> source catches bulges, source -> candidate catches lost spikes/claws), and 6 silhouette +
6 textured renders for compare_ladder.py. Writes work/ladder.json, work/ladder.blend, review/ladder/*.png."""
import json
import math
import os
import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIOS = [float(r) for r in os.environ.get('REA_RATIOS', '0.70,0.55,0.45,0.35').split(',')]
MESH, RIG = os.environ.get('REA_MESH', 'Body'), os.environ.get('REA_RIG', 'Rig')
PROTECT = os.environ.get('REA_PROTECT', 'Head,Jaw').split(',')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
scene = bpy.context.scene
src = bpy.data.objects[MESH]; rig = bpy.data.objects[RIG]
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not src:
        o.hide_render = True


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj


def rest():
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    bpy.context.view_layer.update()


rest()
# protection weights: summed weight of the protected bones
prot = src.vertex_groups.new(name='ReduceProtect')
idx = {g.index for g in src.vertex_groups if any(p and p in g.name for p in PROTECT)}
for v in src.data.vertices:
    w = min(1.0, sum(g.weight for g in v.groups if g.group in idx))
    if w > 0:
        prot.add([v.index], w, 'REPLACE')

# UV seams are locked too (user review: the belly plates slid apart where collapses crossed the belly's UV split):
# a vertex whose face corners carry different UVs lies on a seam and keeps full protection.
bm_ = bmesh.new(); bm_.from_mesh(src.data); uvl_ = bm_.loops.layers.uv.active
seam = [v.index for v in bm_.verts if len({tuple(round(c, 5) for c in l[uvl_].uv) for l in v.link_loops}) > 1
        or v.is_boundary]
bm_.free()
prot.add(seam, 1.0, 'REPLACE')
print('SEAM vertices locked', len(seam), 'of', len(src.data.vertices))

METHOD = os.environ.get('REA_METHOD', 'blender')


def from_npz(r):
    """Texture-aware MeshLab result -> skinned candidate: wedge UVs, material by the u offset, weights by data
    transfer from the source (nearest face interpolated), 4 influences."""
    import numpy as np
    d = np.load(os.path.join(HERE, 'work', f'mesh_r{int(r * 100)}.npz'))
    me = bpy.data.meshes.new(f'Cand_{int(r * 100)}')
    me.from_pydata([tuple(v) for v in d['verts'].tolist()], [], [tuple(f) for f in d['faces'].tolist()])
    me.update()
    for m in src.data.materials:
        me.materials.append(m)
    uvl = me.uv_layers.new(name=src.data.uv_layers.active.name)
    w = d['wuv']
    for p in me.polygons:
        mat = int(w[p.index * 3][0] // 2)
        p.material_index = min(mat, len(me.materials) - 1); p.use_smooth = True
        for k, li in enumerate(p.loop_indices):
            u, v = w[p.index * 3 + k]
            uvl.data[li].uv = (u - 2.0 * mat, v)
    c = bpy.data.objects.new(f'Cand_{int(r * 100)}', me); scene.collection.objects.link(c); c.hide_render = True
    c.matrix_world = src.matrix_world.copy(); c.parent = src.parent
    if c.parent is not None:
        c.matrix_parent_inverse = src.matrix_parent_inverse.copy()
    for g in src.vertex_groups:
        if g.name != 'ReduceProtect':
            c.vertex_groups.new(name=g.name)
    tmp = src.copy(); tmp.data = src.data.copy(); scene.collection.objects.link(tmp)
    for m in list(tmp.modifiers):
        tmp.modifiers.remove(m)
    dt = c.modifiers.new('W', 'DATA_TRANSFER'); dt.object = tmp; dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
    dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'; dt.use_object_transform = False
    select_only(c); bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(tmp, do_unlink=True)
    # A vertex that is still a source vertex keeps its exact weights: the nearest-face transfer can take a touching
    # piece's weights (the goblin's neck took its collar's and stayed with the spine in Hit).
    from mathutils import kdtree
    tree = kdtree.KDTree(len(src.data.vertices))
    for v in src.data.vertices:
        tree.insert(v.co, v.index)
    tree.balance()
    exact = 0
    for v in c.data.vertices:
        _, index, distance = tree.find(v.co)
        if distance < 1e-6:
            for g in list(v.groups):
                c.vertex_groups[g.group].remove([v.index])
            for g in src.data.vertices[index].groups:
                name = src.vertex_groups[g.group].name
                if name != 'ReduceProtect':
                    c.vertex_groups[name].add([v.index], g.weight, 'REPLACE')
            exact += 1
    print('EXACT WEIGHTS', exact, 'of', len(c.data.vertices), flush=True)
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    a = c.modifiers.new('Armature', 'ARMATURE'); a.object = rig
    return c


cands = {}
for r in RATIOS:
    if METHOD == 'texture':
        cands[r] = from_npz(r)
        continue
    c = src.copy(); c.data = src.data.copy(); c.name = f'Cand_{int(r * 100)}'
    scene.collection.objects.link(c); c.hide_render = True
    select_only(c)
    for m in list(c.modifiers):
        if m.type == 'ARMATURE':
            c.modifiers.remove(m)
    d = c.modifiers.new('Reduce', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = r
    d.use_collapse_triangulate = True; d.use_symmetry = True; d.symmetry_axis = 'X'
    # the group selects what decimates: inverted, the head/jaw weights protect
    d.vertex_group = 'ReduceProtect'; d.invert_vertex_group = True; d.vertex_group_factor = 4.0
    bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    a = c.modifiers.new('Armature', 'ARMATURE'); a.object = rig
    cands[r] = c


def stats(obj):
    b = bmesh.new(); b.from_mesh(obj.data)
    out = (sum(len(f.verts) - 2 for f in b.faces), sum(1 for e in b.edges if e.is_boundary))
    b.free(); return out


def evaluated(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    b = bmesh.new(); b.from_object(obj, dg); b.transform(obj.matrix_world)
    return b


def error(a_obj, b_obj):
    """max over both directions of vertex -> nearest surface distances (metres)"""
    ba, bb = evaluated(a_obj), evaluated(b_obj)
    ta, tb = BVHTree.FromBMesh(ba), BVHTree.FromBMesh(bb)
    d1 = [tb.find_nearest(v.co)[3] for v in ba.verts]
    d2 = [ta.find_nearest(v.co)[3] for v in bb.verts]
    ba.free(); bb.free()
    return [x for x in d1 + d2 if x is not None]


result = {'source': dict(zip(('tris', 'open_edges'), stats(src))), 'candidates': {}}
for r, c in cands.items():
    allerr = []; worst = (0, '')
    for act in bpy.data.actions:
        rig.animation_data.action = act
        f0, f1 = (int(x) for x in act.frame_range)
        for f in range(f0, f1 + 1, 3):
            scene.frame_set(f)
            e = error(c, src); allerr += e
            if max(e) > worst[0]:
                worst = (max(e), f'{act.name}:{f}')
    allerr.sort()
    tris, opened = stats(c)
    result['candidates'][str(r)] = {'tris': tris, 'open_edges': opened,
                                    'p99_mm': round(allerr[int(len(allerr) * .99)] * 1000, 2),
                                    'max_mm': round(worst[0] * 1000, 2), 'worst_at': worst[1]}
    print('LADDER', r, result['candidates'][str(r)], flush=True)

# renders: 6 silhouettes (workbench flat) + 6 textured (Eevee) per mesh, rest pose... and Standing frame 0
rest()
rig.animation_data.action = bpy.data.actions.get('Standing'); scene.frame_set(0)
lo = Vector([min((src.matrix_world @ Vector(b))[k] for b in src.bound_box) for k in range(3)])
hi = Vector([max((src.matrix_world @ Vector(b))[k] for b in src.bound_box) for k in range(3)])
ctr = (lo + hi) / 2; size = (hi - lo).length
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 50
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); scene.collection.objects.link(sun)
world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x, scene.render.resolution_y = 512, 512
VIEWS = {'front': (0, -1, .25), 'back': (0, 1, .3), 'left': (1, 0, .2), 'right': (-1, 0, .2), 'q34': (.75, -.75, .35),
         'top': (.1, -.2, 1)}
out = os.path.join(HERE, 'review', 'ladder'); os.makedirs(out, exist_ok=True)
meshes = {'source': src, **{f'r{int(r * 100)}': c for r, c in cands.items()}}
for label, obj in meshes.items():
    for o in meshes.values():
        o.hide_render = o is not obj
    for vname, d in VIEWS.items():
        dv = Vector(d).normalized()
        cam.location = ctr + dv * size * 1.6
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for mode in ('sil', 'tex'):
            if mode == 'sil':
                scene.render.engine = 'BLENDER_WORKBENCH'; scene.display.shading.light = 'FLAT'
                scene.display.shading.color_type = 'SINGLE'; scene.display.shading.single_color = (1, 1, 1)
                scene.render.film_transparent = True
            else:
                scene.render.engine = 'BLENDER_EEVEE'; scene.render.film_transparent = False
            scene.render.filepath = os.path.join(out, f'{label}_{vname}_{mode}.png')
            bpy.ops.render.render(write_still=True)
json.dump(result, open(os.path.join(HERE, 'work', 'ladder.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
print('DONE')
