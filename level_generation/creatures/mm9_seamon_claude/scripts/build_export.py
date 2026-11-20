"""Animated master + export for the Sea Monster: rename rig/mesh, build the role clips from the MM9 clips
(clips_mm9.py SEA), assign the composed textures and export export/mm9_seamon_lod0.glb.

Args: <uv or mouth blend (mouth_rebuild.py)> <out anim blend> <out glb> <clip report json>

Death = MM9 diewater2's convulsion, then a limp sprawl on the belly (see below); Dead = that pose, 1 s. The floor pass (build_runtime.sh)
keeps the sinking body on the floor.
"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'Sea'
CUT_S, LIMP_S, ROLL_DEG = 0.45, 0.9, 30
SPRAWL = ('swim', 0.0)

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
body.data.materials.append(material(NAME, 'sea_basecolor_graded.png', 'sea_normal_1k.png',
                                    'sea_metal_rough_1k.png'))
for a in ('piece', 'chain'):
    if a in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[a])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
# the sprawl pose: the start of MM9 swim (limbs swept back along the body, body level), taken before the MM9 actions
# are replaced
rig.animation_data_create()
rig.animation_data.action = bpy.data.actions[SPRAWL[0]]
try:
    rig.animation_data.action_slot = bpy.data.actions[SPRAWL[0]].slots[0]
except Exception:
    pass
sc.frame_set(int(round(SPRAWL[1] * fps_import)))
limp = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
rig.animation_data.action = None
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import, C.SEA)
recs = report.pop('_recs')
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
sc.render.fps_base = 1
act = bpy.data.actions['Death']
rig.animation_data.action = act
# diewater2 is a sinking death: it rolls belly-up and ends hanging head-up with limbs and tail dangling, which on a
# floor would stand on its tail. Death keeps MM9's convulsion up to CUT_S, then goes limp into a sprawl on the belly
# (the swim pose, rolled ROLL_DEG onto its side) with a gravity-like ease; the floor pass (--ground-death) lowers the
# body onto the floor as the limbs come up.
cut = int(round(CUT_S * C.FPS))
for fc in C.fcurves(act):
    for kp in [k for k in fc.keyframe_points if k.co.x > cut + 1e-3][::-1]:
        fc.keyframe_points.remove(kp)
sc.frame_set(cut)
start = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
n = int(round(LIMP_S * C.FPS))
for k in range(1, n + 1):
    x = k / n
    a_ = x * x * (3 - 2 * x)
    th = math.radians(ROLL_DEG) * x * x
    for pb in rig.pose.bones:
        q0, l0, s0 = start[pb.name]
        q1, l1, s1 = limp[pb.name]
        if q0.dot(q1) < 0:
            q1 = -q1
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = q0.slerp(q1, a_)
        pb.location = l0.lerp(l1, a_)
        pb.scale = s0.lerp(s1, a_)
    bpy.context.view_layer.update()
    pb = rig.pose.bones['Bone01']
    h = (rig.matrix_world @ pb.matrix).translation
    R = Matrix.Translation(h) @ Matrix.Rotation(th, 4, 'Y') @ Matrix.Translation(-h)
    pb.matrix = rig.matrix_world.inverted() @ R @ rig.matrix_world @ pb.matrix
    bpy.context.view_layer.update()
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=cut + k)
        pb.keyframe_insert('location', frame=cut + k)
        pb.keyframe_insert('scale', frame=cut + k)
for fc in C.fcurves(act):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
report['clips']['Death'].update({'sources': ['diewater2 (0 - %.2f s)' % CUT_S,
                                             'limp into %s@%.2fs, roll %d deg' % (SPRAWL[0], SPRAWL[1], ROLL_DEG)],
                                 'duration': (cut + n) / C.FPS, 'frames': cut + n})
sc.frame_set(cut + n)
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
# label groups of mouth_rebuild.py ('Mouth', 'Eye') stay in the anim blend for mouth_gates.py, not in the GLB
for g in [g for g in body.vertex_groups if g.name not in rig.data.bones]:
    body.vertex_groups.remove(g)
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
