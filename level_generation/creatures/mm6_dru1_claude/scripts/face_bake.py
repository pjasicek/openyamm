"""Face graft by project-and-bake (review 3: patches on the old head texture fought each other; the playbook's "problem
heads" route). In place on <blend> (the textured master), then bakes:
1. Our face vertices (head faces, piece 0, front ellipse round the face) move onto the head-only Meshy model's surface
   (meshy/head_model_v1, placed by work/face_align.json), weight 1 in the face centre fading to 0 at the ellipse border,
   displacement capped at CAP, so the face's features (lip crease, eyes, nose) sit where the model painted them.
2. New HeadUV: the head-set skin (piece 0 head faces, eye caps included) as large islands (Smart UV Project 89 deg,
   scaled FACE_SCALE x before packing), hair and hood (pieces 1, 3) Smart UV Project 66 deg, all packed.
3. Cycles bakes at BAKE px into work/: face colour and normals from the head model (selected to active), and colour and
   normals of the whole head set from a copy of the previous head (old HeadUV + the previous composed head textures),
   so hair and hood keep their paint. compose_dru1.py merges them by a 3D face mask.
The old head textures are kept as textures/prev_head_*.png. Args: -- <blend>"""
import bpy, bmesh, sys, os, json, math, shutil
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, *p)
CAP, FACE_SCALE, BAKE = 0.008, 2.2, 2048
FC, FR = (-0.007, 1.553), (0.058, 0.080)          # face ellipse centre (x, z) and radii
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
# keep the previous head textures (the source of bake B)
for f in ('basecolor', 'normal'):
    src = W('textures', f'dru1_head_{f}_1k.png'); dst = W('textures', f'prev_head_{f}_1k.png')
    if not os.path.exists(dst):
        shutil.copy(src, dst)
# ---------------------------------------------------------------- head model, placed
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=W('meshy', 'head_model_v1', 'model_urls_glb.glb'))
hm = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
for o in bpy.data.objects:
    if o not in before and o is not hm:
        o.select_set(False)
T = Matrix(json.load(open(W('work', 'face_align.json')))['matrix'])
hm.parent = None; hm.matrix_world = T @ hm.matrix_world
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
mesh_eval = hm.evaluated_get(dg).to_mesh()
MV = [hm.matrix_world @ v.co for v in mesh_eval.vertices]
mesh_eval.calc_loop_triangles()
tree = BVHTree.FromPolygons(MV, [tuple(t.vertices) for t in mesh_eval.loop_triangles])
# ---------------------------------------------------------------- 1. face onto the model
head_v = sorted({i for p in me.polygons if hd[p.index] for i in p.vertices if pv[i] == 0})
moved = 0; dmax = 0.0
if not me.get('face_grafted'):
    for i in head_v:
        p = me.vertices[i].co
        if p.y > -0.05:
            continue
        e = math.hypot((p.x - FC[0]) / FR[0], (p.z - FC[1]) / FR[1])
        if e >= 1.0:
            continue
        w = min(1.0, (1.0 - e) / 0.3); w = w * w * (3 - 2 * w)
        loc, n, idx, d = tree.find_nearest(p, 0.03)
        if loc is None:
            continue
        dv = (loc - p)
        if dv.length > CAP:
            dv = dv.normalized() * CAP
        me.vertices[i].co = p + dv * w; moved += 1; dmax = max(dmax, (dv * w).length)
    me['face_grafted'] = 1
print('FACEFIT vertices moved', moved, 'max mm', round(dmax * 1000, 1))
# ---------------------------------------------------------------- 2. new HeadUV (previous kept as HeadUV_prev)
if 'HeadUV_prev' not in me.uv_layers:
    old = me.uv_layers['HeadUV']; prev = me.uv_layers.new(name='HeadUV_prev')
    for li in range(len(me.loops)):
        prev.data[li].uv = old.data[li].uv
me.uv_layers.active = me.uv_layers['HeadUV']
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body


def select_faces(pred):
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = bool(pred(p))
    bpy.ops.object.mode_set(mode='EDIT')


bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.object.mode_set(mode='OBJECT')
select_faces(lambda p: hd[p.index] and pv[p.vertices[0]] == 0)
bpy.ops.uv.smart_project(angle_limit=math.radians(89), island_margin=0.003, scale_to_bounds=False)
select_faces(lambda p: hd[p.index] and pv[p.vertices[0]] != 0)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
uvd = me.uv_layers['HeadUV'].data
for p in me.polygons:                                    # skin islands get FACE_SCALE x the texel density
    if hd[p.index] and pv[p.vertices[0]] == 0:
        for li in p.loop_indices:
            uvd[li].uv = uvd[li].uv * FACE_SCALE
select_faces(lambda p: hd[p.index])
bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
print('HEADUV repacked')
# ---------------------------------------------------------------- 3. bake targets: head faces only
def head_copy(name, uv_keep):
    ob = body.copy(); ob.data = body.data.copy(); ob.name = name
    scene.collection.objects.link(ob); ob.parent = None; ob.matrix_world = body.matrix_world.copy()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    bm = bmesh.new(); bm.from_mesh(ob.data); hl = bm.faces.layers.int['head']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] == 0], context='FACES')
    bm.to_mesh(ob.data); bm.free()
    for l in [l.name for l in ob.data.uv_layers if l.name != uv_keep]:
        ob.data.uv_layers.remove(ob.data.uv_layers[l])
    ob.data.materials.clear()
    return ob


target = head_copy('BakeTarget', 'HeadUV')
source_old = head_copy('PrevHead', 'HeadUV_prev')


def image_material(ob, img_files, uv):
    m = bpy.data.materials.new(ob.name + '_m'); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uv
    if img_files:
        bc = nt.nodes.new('ShaderNodeTexImage'); bc.image = bpy.data.images.load(img_files[0])
        nt.links.new(u.outputs['UV'], bc.inputs['Vector']); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
        nm_t = nt.nodes.new('ShaderNodeTexImage'); nm_t.image = bpy.data.images.load(img_files[1]); nm_t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(u.outputs['UV'], nm_t.inputs['Vector'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = uv
        nt.links.new(nm_t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    ob.data.materials.append(m)
    return m


image_material(source_old, [W('textures', 'prev_head_basecolor_1k.png'), W('textures', 'prev_head_normal_1k.png')], 'HeadUV_prev')
# the target: one material with the active bake image node
tm = image_material(target, [], 'HeadUV')
img_node = tm.node_tree.nodes.new('ShaderNodeTexImage'); tm.node_tree.nodes.active = img_node
try:
    scene.render.engine = 'CYCLES'
except TypeError:
    pass
scene.cycles.samples = 4; scene.cycles.device = 'CPU'
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.012; scene.render.bake.max_ray_distance = 0.03
scene.render.bake.use_pass_direct = False; scene.render.bake.use_pass_indirect = False; scene.render.bake.use_pass_color = True
scene.render.bake.margin = 8


def bake(source, kind, out_name, colorspace):
    img = bpy.data.images.new(out_name, BAKE, BAKE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    img_node.image = img
    for o in bpy.data.objects:
        o.select_set(o in (source, target))
    bpy.context.view_layer.objects.active = target
    if kind == 'NORMAL':
        scene.render.bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, uv_layer='HeadUV')
    else:
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_selected_to_active=True, uv_layer='HeadUV')
    img.filepath_raw = W('work', out_name + '.png'); img.file_format = 'PNG'; img.save()
    print('BAKED', out_name)


bake(hm, 'DIFFUSE', 'bake_face_color', 'sRGB')
bake(hm, 'NORMAL', 'bake_face_normal', 'Non-Color')
bake(source_old, 'DIFFUSE', 'bake_prev_color', 'sRGB')
bake(source_old, 'NORMAL', 'bake_prev_normal', 'Non-Color')
for o in (target, source_old, hm):
    bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    if o.type in ('EMPTY',) and o.parent is None and o.name not in ('Rig',) and not o.children:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_mainfile()
print('FACEBAKE done')
