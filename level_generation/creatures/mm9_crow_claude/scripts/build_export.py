"""Animated master + export for the MM9 crow: rename rig/mesh, add the beak socket, build the role clips from the MM9
clips (clips_mm9.py), assign the composed textures and export export/mm9_crow_lod0.glb (from
mm9_wolf_claude/scripts/build_export.py).

Args: <uv blend> <out anim blend> <out glb> <clip report json>
"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
BODY = 'crow'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'Crow'

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
# the head rework's seam fade writes <body>_basecolor_final.png (compose_crow.py); older builds use the graded colour
BASE = f'{BODY}_basecolor_final.png' if os.path.exists(os.path.join(T, f'{BODY}_basecolor_final.png')) \
    else f'{BODY}_basecolor_graded.png'
body.data.materials.append(material(NAME, BASE, f'{BODY}_normal_1k.png', f'{BODY}_metal_rough_1k.png'))
# grafted head (2026-10-30 head rework, scripts/graft_head.py): faces with the 'head' attribute take their own 1K set
HEAD_SET = 'head' in body.data.attributes and os.path.exists(os.path.join(T, f'{BODY}_head_basecolor.png'))
if HEAD_SET:
    body.data.materials.append(material(NAME + 'Head', f'{BODY}_head_basecolor.png', f'{BODY}_head_normal_1k.png',
                                        f'{BODY}_head_metal_rough_1k.png'))
    ha = body.data.attributes['head'].data
    for p in body.data.polygons:
        p.material_index = 1 if ha[p.index].value == 1 else 0
# beak socket (MM9 releases the Bird B/C missiles from the head): the front-most beak vertices in the bind pose; the
# grafted head's beak is rigid on Xhead and its tip is stored on the Body ('beak_tip')
if 'beak_tip' in body.keys():
    mouth, sock_bone = Vector(tuple(body['beak_tip'])), 'Xhead'
else:
    gi = body.vertex_groups['Xbeak'].index
    bk = [body.matrix_world @ v.co for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    bk.sort(key=lambda p: p.y)
    mouth, sock_bone = sum(bk[:max(3, len(bk) // 20)], Vector()) / max(3, len(bk) // 20), 'Xbeak'
sock = bpy.data.objects.new('Socket_Mouth', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = sock_bone
bpy.context.view_layer.update()
sock.matrix_world = Matrix.Translation(mouth)
body.data.attributes.remove(body.data.attributes['piece'])
body.data.attributes.remove(body.data.attributes['chain'])
for extra in ('head', 'kind'):
    if extra in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[extra])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
roles = C.CROW
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
