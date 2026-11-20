"""Animated master + export for the MM9 Eye: rename rig/mesh, add the eye socket, build the role clips from the MM9
clips (clips_mm9.py), assign the composed textures and export export/mm9_eye_lod0.glb (from
mm9_lobber_claude/scripts/build_export.py). Dead = the last Death pose held one second.

Args: <uv blend> <out anim blend> <out glb> <clip report json>
"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
BODY = 'eye'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'Eye'

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
# eye socket (RangeAttack release): the front pole of the big eyeball in the bind pose, carried by Box01 (MM9's
# RangeAttack1 socket sits on the eyelid bone Box71 at the eye's front; our eyeball is rigid on Box01)
piece = body.data.attributes['piece']
pts = [body.matrix_world @ v.co for v in body.data.vertices if piece.data[v.index].value == 3]
front = min(pts, key=lambda p: p.y)
cen = sum(pts, Vector()) / len(pts)
mouth = Vector((cen.x, front.y - 0.02, cen.z))
sock = bpy.data.objects.new('Socket_Eye', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = 'Box01'
bpy.context.view_layer.update()
sock.matrix_world = Matrix.Translation(mouth)
body.data.attributes.remove(body.data.attributes['piece'])
body.data.attributes.remove(body.data.attributes['chain'])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
roles = C.ROLES
report = C.build_role_clips(rig, fps_import, roles)
recs = report.pop('_recs')
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
sc.render.fps_base = 1


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
report['socket'] = list(mouth) if mouth is not None else None
report['triangles'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
for o in bpy.data.objects:
    o.select_set(o in (body, rig) or (sock is not None and o == sock))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
json.dump(report, open(REP, 'w'), indent=1)
print('EXPORTED', OUT_GLB, json.dumps({k: v.get('duration') for k, v in report['clips'].items()}))
