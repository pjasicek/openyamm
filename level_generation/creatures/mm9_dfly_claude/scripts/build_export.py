"""Animated master + export: join wings into the body, add the mouth socket, build the role clips from the MM9
clips (clips_mm9.py), assign the composed textures and export export/mm9_dfly_lod0.glb.

Args: <uv blend> <out anim blend> <out glb> <clip report json>
"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
rig.name = 'Dfly_Rig'
body = bpy.data.objects['Dfly']
wings = bpy.data.objects['Dfly_Wings']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def material(name, base, normal, mr, rough_default=None):
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
    if normal:
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
body.data.materials.append(material('Dfly', 'dfly_basecolor_graded.png', 'dfly_normal_1k.png', 'dfly_metal_rough_1k.png'))
wings.data.materials.clear()
wings.data.materials.append(material('Dfly_Wing', 'dfly_wing_basecolor.png', None, 'dfly_wing_metal_rough.png'))
wings.data.uv_layers[0].name = body.data.uv_layers[0].name
# mouth socket: centre of the teeth/jaw pieces in the bind pose, carried by the skull
piece = body.data.attributes['piece']
pts = [body.matrix_world @ v.co for v in body.data.vertices if piece.data[v.index].value == 2]
mouth = sum(pts, pts[0] * 0) / len(pts)
sock = bpy.data.objects.new('Socket_Mouth', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = 'Xheadpiv'
bpy.context.view_layer.update()
sock.matrix_world = sock.matrix_world.__class__.Translation(mouth)
# join wings into the body (two materials, one skinned mesh)
for o in bpy.data.objects:
    o.select_set(o in (body, wings))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.data.attributes.remove(body.data.attributes['piece'])
for name in ('bone',):
    if name in body.data.color_attributes:
        body.data.color_attributes.remove(body.data.color_attributes[name])
# clips
fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import)
for a in originals:
    bpy.data.actions.remove(a)
sc.render.fps = C.FPS
sc.render.fps_base = 1
for act in bpy.data.actions:
    if report['clips'].get(act.name, {}).get('loop'):
        report['clips'][act.name]['seam_after_deg'] = round(C.seam_after(rig, act, C.FPS), 3)
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
