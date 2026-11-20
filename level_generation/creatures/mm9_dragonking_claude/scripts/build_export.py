"""Animated master + export for the Dragon King: rename rig/mesh, add the mouth socket, build the role clips from the
MM9 clips (clips_mm9.py: DRAGON), assign the composed textures and export export/mm9_dragonking_lod0.glb.

Args: <uv blend> <out anim blend> <out glb> <clip report json> [--no-textures]

Mouth socket (`Socket_Mouth`, child of the skull bone Xjawbase, the node of MM9's own RangeAttack socket): the point
between the upper and lower jaw tips at the front of the open mouth in the bind pose, measured on the mesh (the
foremost head vertex of the upper jaw and of the lower jaw, averaged, then pulled 4 % of the head length back inside
the mouth). Dead = Death's last pose held one second.
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv[:4]
TEXTURES = '--no-textures' not in argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'DragonKing'
SOCKET_BONE = 'Xjawbase'
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01'}

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
rig.name = f'{NAME}_Rig'
body = bpy.data.objects['Body']
body.name = NAME
body.data.name = NAME
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o not in (body,):
        bpy.data.objects.remove(o)
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = False  # double-sided: wing membranes are open sheets (the install cook single-sides hidden backs)
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(T, fname))
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        return n
    bc = tex(base, 'sRGB')
    nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
    nm = tex(normal, 'Non-Color')
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    m = tex(mr, 'Non-Color')
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(m.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


if TEXTURES:
    mats = {m.name: i for i, m in enumerate(body.data.materials)}
    body.data.materials.clear()
    body.data.materials.append(material(NAME, 'dragonking_basecolor_graded.png', 'dragonking_normal_1k.png',
                                        'dragonking_metal_rough_1k.png'))
    if os.path.exists(os.path.join(T, 'dragonking_wing_basecolor.png')):
        body.data.materials.append(material(f'{NAME}_Wing', 'dragonking_wing_basecolor.png',
                                            'dragonking_wing_normal_1k.png', 'dragonking_wing_metal_rough_1k.png'))
    # head set (2026-10-30 rework, scripts/jaw/head_split_dk.py): head faces take the 1K head maps through their
    # HeadUV, copied into the single UV layer; material name contains "Head" (material_classes_to_orm.py)
    me_h = body.data
    if 'head' in me_h.attributes and os.path.exists(os.path.join(T, 'dragonking_head_basecolor.png')):
        hd = np.zeros(len(me_h.polygons), np.int32); me_h.attributes['head'].data.foreach_get('value', hd)
        me_h.materials.append(material(f'{NAME}_Head', 'dragonking_head_basecolor.png', 'dragonking_head_normal_1k.png',
                                       'dragonking_head_metal_rough_1k.png'))
        hi = len(me_h.materials) - 1
        huv, buv = me_h.uv_layers['HeadUV'].data, me_h.uv_layers['UVMap'].data
        mi = np.zeros(len(me_h.polygons), np.int32)
        for p_ in me_h.polygons:
            if hd[p_.index]:
                mi[p_.index] = hi
                for li in p_.loop_indices:
                    buv[li].uv = huv[li].uv.copy()
        me_h.polygons.foreach_set('material_index', mi.tolist())
        print('HEAD faces', int(hd.sum()), 'material', hi)
if 'HeadUV' in body.data.uv_layers:
    body.data.uv_layers.remove(body.data.uv_layers['HeadUV'])
body.data.uv_layers.active = body.data.uv_layers['UVMap']

# mouth socket from the bind-pose head vertices
vg = {g.index: g.name for g in body.vertex_groups}


def dominant(v):
    return vg[max(v.groups, key=lambda g: g.weight).group] if v.groups else ''


up, lo = [], []
for v in body.data.vertices:
    d = dominant(v)
    co = body.matrix_world @ v.co
    if d in UPPER:
        up.append(co)
    elif d in LOWER:
        lo.append(co)
up, lo = np.array([tuple(p) for p in up]), np.array([tuple(p) for p in lo])
tip_u = up[up[:, 1].argmin()]
tip_l = lo[lo[:, 1].argmin()]
head_len = up[:, 1].max() - up[:, 1].min()
mouth = Vector(((tip_u + tip_l) / 2).tolist()) + Vector((0, 0.04 * head_len, 0))
sock = bpy.data.objects.new('Socket_Mouth', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = SOCKET_BONE
bpy.context.view_layer.update()
sock.matrix_world = Matrix.Translation(mouth)
for name in ('piece', 'chain', 'label_meshy', 'kept', 'stray'):
    if name in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[name])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

# Smooth shading (2026-10-30 fix). fit_dragon.py builds 'Body' as a new mesh, whose faces Blender makes flat, and no
# later step smoothed them: the export wrote face normals and split every vertex per face (5.6 vertices per position,
# every triangle visible). Smooth, with hard edges only at real creases (dihedral angle above CREASE_DEG: horn and
# claw ridges, spike tips, membrane rims) and around the mouth-patch lip faces (mouth_uv.py), which are a UV seam
# already and open into the mouth when the jaw drops. Other UV seams stay smooth: the Meshy normal map is a detail
# map, not a bake against these normals (per-triangle mean |xy| 0.03, no correlation with the flat-to-smooth tilt).
CREASE_DEG = 60.0
me_b = body.data
me_b.shade_smooth()
me_b.set_sharp_from_angle(angle=np.radians(CREASE_DEG))
# 2026-10-30 rework: the mouth cavity (mouth_rebuild.py 'mouth' faces) meets the lips at a hard edge instead
for crease_attr in ('lip', 'mouth'):
    if crease_attr not in me_b.attributes:
        continue
    lip_face = np.zeros(len(me_b.polygons), np.int32)
    me_b.attributes[crease_attr].data.foreach_get('value', lip_face)
    lip_face = (lip_face > 0).astype(np.int32)
    edge_faces = {}
    for p in me_b.polygons:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(lip_face[p.index])
    sharp = np.zeros(len(me_b.edges), bool)
    me_b.edges.foreach_get('use_edge_sharp', sharp)
    for e in me_b.edges:
        if len(set(edge_faces.get(e.key, []))) > 1:
            sharp[e.index] = True
    me_b.edges.foreach_set('use_edge_sharp', sharp)
n_sharp = sum(e.use_edge_sharp for e in me_b.edges)
print('SHADING smooth faces', sum(p.use_smooth for p in me_b.polygons), 'of', len(me_b.polygons), 'sharp edges',
      n_sharp, 'of', len(me_b.edges))

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import, C.DRAGON)
report.pop('_recs')
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
sc.render.fps_base = 1
act = bpy.data.actions['Death']
rig.animation_data.action = act
# Corpse wings: our membranes are larger than MM9's, so in die1's final pose they cut up to 2.3 units into the floor
# (wrist and fingers). Each wing turns about its shoulder joint (Ywarm head) by the smallest angle that rests its
# lowest point on the floor in the last pose (bisection on a world axis that lifts that point), eased in with a
# smoothstep between WING_T0 and WING_T1 (the fall to HitFloor at 1.944 s) and held after.
WING_T0, WING_T1, WING_CLEAR, WING_MAX_DEG = 1.2, 1.95, 0.02, 45
last = int(round(act.frame_range[1]))
import math
from mathutils import Quaternion


def wing_low(prefix_bones):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me_ = ev.to_mesh()
    ids = [v.index for v in body.data.vertices if v.groups and vg[max(v.groups, key=lambda g: g.weight).group] in prefix_bones]
    pts = [(body.matrix_world @ me_.vertices[i].co) for i in ids]
    ev.to_mesh_clear()
    return min(pts, key=lambda p: p.z)


def subtree(name):
    out, st = set(), [rig.data.bones[name]]
    while st:
        b = st.pop(); out.add(b.name); st += list(b.children)
    return out


wing_fix = {}
for root in ('Ywarm', 'Ywarm01'):
    bones_w = subtree(root)
    sc.frame_set(last)
    base_q = rig.pose.bones[root].rotation_quaternion.copy()
    lowp = wing_low(bones_w)
    if lowp.z >= 0:
        continue
    pb = rig.pose.bones[root]
    head = rig.matrix_world @ pb.head
    # flap axis: the body's long axis in the corpse (tail base -> neck), so the wing folds up like a flap
    axis = (rig.matrix_world @ rig.pose.bones['Xneckpiv'].head) - (rig.matrix_world @ rig.pose.bones['Xtailbase'].head)
    axis.normalize()

    def set_angle(a, frame):
        sc.frame_set(frame)
        pb.rotation_quaternion = base_q if frame == last else pb.rotation_quaternion
        # world rotation about the joint, expressed in the bone's pose space
        Rw = Matrix.Rotation(a, 4, axis)
        M = rig.matrix_world.inverted() @ Matrix.Translation(head) @ Rw @ Matrix.Translation(-head) @ rig.matrix_world @ pb.matrix
        pb.matrix = M
        bpy.context.view_layer.update()
    lo_a, hi_a = 0.0, math.radians(WING_MAX_DEG)
    gains = {}
    for sign in (1, -1):
        sc.frame_set(last)
        set_angle(sign * math.radians(20), last)
        gains[sign] = wing_low(bones_w).z
    axis = axis * max(gains, key=gains.get)
    for _ in range(18):
        mid = (lo_a + hi_a) / 2
        set_angle(mid, last)
        if wing_low(bones_w).z < WING_CLEAR:
            lo_a = mid
        else:
            hi_a = mid
    theta = hi_a
    f0, f1 = int(round(WING_T0 * C.FPS)), int(round(WING_T1 * C.FPS))
    for f in range(f0, last + 1):
        sc.frame_set(f)
        x = min(1.0, (f - f0) / max(1, f1 - f0))
        a = theta * x * x * (3 - 2 * x)
        Rw = Matrix.Rotation(a, 4, axis)
        head_f = rig.matrix_world @ pb.head
        pb.matrix = rig.matrix_world.inverted() @ Matrix.Translation(head_f) @ Rw @ Matrix.Translation(-head_f) @ rig.matrix_world @ pb.matrix
        bpy.context.view_layer.update()
        pb.keyframe_insert('rotation_quaternion', frame=f)
    wing_fix[root] = {'theta_deg': round(math.degrees(theta), 1), 'lowest_before': round(lowp.z, 3)}
for fc in C.fcurves(act):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
report['corpse_wing_fix'] = wing_fix
sc.frame_set(last)
end = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.new('Dead')
dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, C.FPS):
    for pb in rig.pose.bones:
        q, l, s_ = end[pb.name]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion, pb.location, pb.scale = q, l, s_
        pb.keyframe_insert('rotation_quaternion', frame=f)
        pb.keyframe_insert('location', frame=f)
        pb.keyframe_insert('scale', frame=f)
report['clips']['Dead'] = {'sources': ['Death last pose'], 'duration': 1.0}
for a in bpy.data.actions:
    if report['clips'].get(a.name, {}).get('loop'):
        report['clips'][a.name]['seam_after_deg'] = round(C.seam_after(rig, a, C.FPS), 3)
rig.animation_data.action = bpy.data.actions['Standing']
for b in rig.pose.bones:
    b.matrix_basis.identity()
report['socket_mouth'] = list(mouth)
report['triangles'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
report['shading'] = {'smooth': True, 'crease_deg': CREASE_DEG, 'sharp_edges': int(n_sharp), 'edges': len(me_b.edges)}
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
for o in bpy.data.objects:
    o.select_set(o in (body, rig, sock))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
json.dump(report, open(REP, 'w'), indent=1)
print('EXPORTED', OUT_GLB, json.dumps({k: v.get('duration') for k, v in report['clips'].items()}))
