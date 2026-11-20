"""Animated master + export (from ../mm9_lobber_claude/scripts/build_export.py; basilisk and terror added; their
Death is the MM9 die clip as is): rename rig/mesh, add the mouth socket, build the role
clips from the MM9 clips (clips_mm9.py), assign the composed textures and export export/mm9_<body>_lod0.glb.

Args: <uv blend> <body: lobber|pod|basilisk|terror> <out anim blend> <out glb> <clip report json>

Lobber death: MM9 DieAir1 (the spasm) and then, instead of MM9's fall from the ceiling (fall1/falldown1, which drop the
body downward and would rise in the upright plant), a wilt: the stalk topples backward from Xstembase with a
gravity-like ease-in (angle ~ t^2), shared over Xstembase/XstemA/XstemB/XstemC so it droops in a curve, the total angle
solved so the lowest head/limb point lands on the floor, then a short bounce and settle. Dead = the last pose, 1 s.
"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, BODY, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = {'lobber': 'Lobber', 'pod': 'Pod', 'basilisk': 'Basilisk', 'terror': 'Terror'}[BODY]
SOCKET_BONE = {'lobber': 'Xheadpiv', 'pod': 'Xhead', 'basilisk': 'Xhead', 'terror': 'Bip01 Head'}[BODY]
WILT_S, BOUNCE_S, SETTLE_S = 0.8, 0.12, 0.25
WILT_SHARE = {'Xstembase': 0.55, 'XstemA': 0.2, 'XstemB': 0.15, 'XstemC': 0.1}

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
rig.name = f'{NAME}_Rig'
body = bpy.data.objects['Body']
body.name = NAME
body.data.name = NAME
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
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


body.data.materials.clear()
body.data.materials.append(material(NAME, f'{BODY}_basecolor_graded.png', f'{BODY}_normal_1k.png',
                                    f'{BODY}_metal_rough_1k.png'))
# mouth socket: centre of the mouth pieces (tendrils/teeth) in the bind pose, carried by the skull
piece = body.data.attributes['piece']
pts = [body.matrix_world @ v.co for v in body.data.vertices if piece.data[v.index].value == 2]
mouth = sum(pts, Vector()) / len(pts)
sock = bpy.data.objects.new('Socket_Mouth', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = SOCKET_BONE
bpy.context.view_layer.update()
sock.matrix_world = Matrix.Translation(mouth)
body.data.attributes.remove(body.data.attributes['piece'])
body.data.attributes.remove(body.data.attributes['chain'])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
roles = {'lobber': C.LOBBER, 'pod': C.POD, 'basilisk': C.BASILISK, 'terror': C.TERROR}[BODY]
report = C.build_role_clips(rig, fps_import, roles)
recs = report.pop('_recs')
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
sc.render.fps_base = 1


def lowest(exclude_root=True):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    vg = body.vertex_groups.get('Xroot')
    zs = []
    for v in me.vertices:
        if exclude_root and vg is not None:
            src = body.data.vertices[v.index]
            if any(g.group == vg.index and g.weight > 0.5 for g in src.groups):
                continue
        zs.append((body.matrix_world @ v.co).z)
    ev.to_mesh_clear()
    return min(zs)


if BODY == 'lobber':
    act = bpy.data.actions['Death']
    rig.animation_data.action = act
    last = int(round(act.frame_range[1]))
    sc.frame_set(last)
    base = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}

    def apply_wilt(theta):
        for pb in rig.pose.bones:
            pb.matrix_basis = base[pb.name].copy()
        bpy.context.view_layer.update()
        for name in ('Xstembase', 'XstemA', 'XstemB', 'XstemC'):
            pb = rig.pose.bones[name]
            h = (rig.matrix_world @ pb.matrix).translation
            R = Matrix.Translation(h) @ Matrix.Rotation(-theta * WILT_SHARE[name], 4, 'X') @ Matrix.Translation(-h)
            pb.matrix = rig.matrix_world.inverted() @ R @ rig.matrix_world @ pb.matrix
            bpy.context.view_layer.update()
    lo, hi = 0.0, math.radians(110)
    for _ in range(22):
        mid = (lo + hi) / 2
        apply_wilt(mid)
        if lowest() > 0.012:
            lo = mid
        else:
            hi = mid
    theta_end = lo
    nw = int(round(WILT_S * C.FPS)); nb = int(round(BOUNCE_S * C.FPS)); ns = int(round(SETTLE_S * C.FPS))
    seq = [theta_end * ((k / nw) ** 2) for k in range(1, nw + 1)]
    up = theta_end * 0.93
    seq += [theta_end + (up - theta_end) * math.sin(0.5 * math.pi * k / nb) for k in range(1, nb + 1)]
    seq += [up + (theta_end - up) * (0.5 - 0.5 * math.cos(math.pi * k / ns)) for k in range(1, ns + 1)]
    for k, th in enumerate(seq, start=1):
        apply_wilt(th)
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_quaternion', frame=last + k)
            pb.keyframe_insert('location', frame=last + k)
            pb.keyframe_insert('scale', frame=last + k)
    for fc in C.fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    report['clips']['Death'].update({'sources': ['DieAir1', 'wilt (topple backward)'], 'wilt_deg': math.degrees(theta_end),
                                     'duration': (last + len(seq)) / C.FPS, 'frames': last + len(seq)})
    sc.frame_set(last + len(seq))
    end = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
else:
    act = bpy.data.actions['Death']
    rig.animation_data.action = act
    sc.frame_set(int(round(act.frame_range[1])))
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
