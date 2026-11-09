"""Animated master + export for the MM9 fish: join the fin leaves into the body mesh (second material), assign the
composed textures (body: graded base, normal, metal-rough; fins: the side-master RGBA atlas, alpha clip), build the
role clips from MM9's `swim` (fish_clips.py), add the mouth socket and export export/mm9_fish_lod0.glb.
Args: <uv blend> <out anim blend> <out glb> <clip report json>"""
import bpy, sys, os, json
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C
import fish_clips as F

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'Fish'
bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']; rig.name = f'{NAME}_Rig'
body, fins = bpy.data.objects['Body'], bpy.data.objects['Fins']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def tex(nt, fname, cs):
    img = bpy.data.images.load(os.path.join(T, fname)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img
    return n


def body_material():
    mat = bpy.data.materials.new(NAME); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    nt.links.new(tex(nt, 'fish_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = tex(nt, 'fish_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    mr = tex(nt, 'fish_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


def fin_material():
    mat = bpy.data.materials.new(f'{NAME}Fin'); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = tex(nt, 'fish_fins_basecolor.png', 'sRGB')
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.55
    try:
        mat.blend_method = 'CLIP'
    except Exception:
        pass
    return mat


body.data.materials.clear(); body.data.materials.append(body_material())
fins.data.materials.clear(); fins.data.materials.append(fin_material())
for o in bpy.data.objects:
    o.select_set(o in (body, fins))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = NAME; body.data.name = NAME
for a in ('piece', 'fin', 'root'):
    if a in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[a])
# mouth socket: the front-most lip vertices (MM9 has no ranged attack; kept for effects and the swimming follow-up)
gi = body.vertex_groups['XCENTER'].index
pts = sorted((body.matrix_world @ v.co for v in body.data.vertices), key=lambda p: p.y)[:12]
mouth = sum(pts, Vector()) / len(pts)
sock = bpy.data.objects.new('Socket_Mouth', None); sc.collection.objects.link(sock)
sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = 'XCENTER'
bpy.context.view_layer.update(); sock.matrix_world = Matrix.Translation(mouth)

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
report = F.build(rig, fps_import)
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS; sc.render.fps_base = 1
act = bpy.data.actions['Death']; rig.animation_data.action = act
sc.frame_set(int(round(act.frame_range[1])))
end = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True; rig.animation_data.action = dead
for f in (0, C.FPS):
    for pb in rig.pose.bones:
        q, l, s_ = end[pb.name]; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion, pb.location, pb.scale = q, l, s_
        for ch in ('rotation_quaternion', 'location', 'scale'):
            pb.keyframe_insert(ch, frame=f)
report['clips']['Dead'] = {'duration': 1.0, 'note': 'Death last pose'}
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
