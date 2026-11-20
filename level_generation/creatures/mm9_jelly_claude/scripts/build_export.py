"""Animated master + export for the Jellyspore: rename rig/mesh, build the role clips from the MM9 clips
(clips_mm9.py JELLY), build Death, assign the composed textures and export export/mm9_jelly_lod0.glb.

Args: <uv blend> <out anim blend> <out glb> <clip report json>

Death: JELLYSPORE.abc has no death clip. Death = MM9 wincewater2 (the recoil, 0.8 s), then the body goes limp into the
closed-bell pose of fidgetwater at 1.2 s (smoothstep over LIMP_S) while XCENTER tips over sideways about its head
with a gravity-like ease-in (angle ~ t^2, TIP_DEG over TIP_S), a small bounce and settle; the body sinks with the
tip angle so the corpse's lowest point ends on the model floor (z = 0). The flier hover is eased out
over the whole Death by floor_fix.py --hover and the corpse is grounded by --ground-death (build_runtime.sh).
Dead = the last pose, 1 s.
"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'Jelly'
LIMP_POSE = ('fidgetwater', 1.2)
LIMP_S, TIP_S, BOUNCE_S, SETTLE_S = 0.45, 0.9, 0.12, 0.25
TIP_DEG = 82.0

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
body.data.materials.append(material(NAME, 'jelly_basecolor_graded.png', 'jelly_normal_1k.png',
                                    'jelly_metal_rough_1k.png'))
for a in ('piece', 'chain'):
    if a in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[a])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
# the limp pose (closed bell, legs hanging) from an MM9 clip, before the MM9 actions are replaced
rig.animation_data_create()
rig.animation_data.action = bpy.data.actions[LIMP_POSE[0]]
try:
    rig.animation_data.action_slot = bpy.data.actions[LIMP_POSE[0]].slots[0]
except Exception:
    pass
sc.frame_set(int(round(LIMP_POSE[1] * fps_import)))
limp = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
rig.animation_data.action = None
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import, C.JELLY)
recs = report.pop('_recs')
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
sc.render.fps_base = 1

act = bpy.data.actions['Death']
rig.animation_data.action = act
last = int(round(act.frame_range[1]))
sc.frame_set(last)
start = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


def smooth(a):
    a = max(0.0, min(1.0, a))
    return a * a * (3 - 2 * a)


def lowest():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    z = min((body.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    return z


def pose_at(a_limp, theta, drop=0.0):
    for pb in rig.pose.bones:
        q0, l0, s0 = start[pb.name]
        q1, l1, s1 = limp[pb.name]
        if q0.dot(q1) < 0:
            q1 = -q1
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = q0.slerp(q1, a_limp)
        pb.location = l0.lerp(l1, a_limp)
        pb.scale = s0.lerp(s1, a_limp)
    bpy.context.view_layer.update()
    if theta:
        pb = rig.pose.bones['XCENTER']
        h = (rig.matrix_world @ pb.matrix).translation
        R = Matrix.Translation((0, 0, -drop * theta / th_end)) @ Matrix.Translation(h) @ \
            Matrix.Rotation(theta, 4, 'Y') @ Matrix.Translation(-h)
        pb.matrix = rig.matrix_world.inverted() @ R @ rig.matrix_world @ pb.matrix
        bpy.context.view_layer.update()


nl = int(round(LIMP_S * C.FPS)); nt_ = int(round(TIP_S * C.FPS))
nb = int(round(BOUNCE_S * C.FPS)); ns = int(round(SETTLE_S * C.FPS))
th_end = math.radians(TIP_DEG)
seq = []
total = nt_ + nb + ns
for k in range(1, total + 1):
    a = smooth(k / nl)
    if k <= nt_:
        th = th_end * (k / nt_) ** 2
    elif k <= nt_ + nb:
        th = th_end + (th_end * 0.93 - th_end) * math.sin(0.5 * math.pi * (k - nt_) / nb)
    else:
        up = th_end * 0.93
        th = up + (th_end - up) * (0.5 - 0.5 * math.cos(math.pi * (k - nt_ - nb) / ns))
    seq.append((a, th))
# the corpse rests on the model floor (z = 0) at the end of the tip-over: the body sinks with the tip angle
pose_at(seq[-1][0], seq[-1][1])
drop = lowest()
for k, (a, th) in enumerate(seq, start=1):
    pose_at(a, th, drop)
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=last + k)
        pb.keyframe_insert('location', frame=last + k)
        pb.keyframe_insert('scale', frame=last + k)
for fc in C.fcurves(act):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
report['clips']['Death'].update({'sources': ['wincewater2', f'limp to {LIMP_POSE[0]}@{LIMP_POSE[1]}s',
                                             f'tip over {TIP_DEG} deg'], 'corpse_drop_m': drop,
                                 'duration': (last + len(seq)) / C.FPS, 'frames': last + len(seq)})
sc.frame_set(last + len(seq))
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
report['triangles'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
json.dump(report, open(REP, 'w'), indent=1)
print('EXPORTED', OUT_GLB, json.dumps({k: v.get('duration') for k, v in report['clips'].items()}))
