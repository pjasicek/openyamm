"""Animated master + export for the Flying Icky: rename rig/mesh, join the wings (second material), add the mouth
socket, build the role clips from the MM9 clips (clips_mm9.py), assign the composed textures and export
export/mm9_icky_lod0.glb.

Args: <uv blend> <out anim blend> <out glb> <clip report json>
Running = Flap x RUN_RATE; Dead = the last Death pose held one second.
"""
import bpy, sys, os, json
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
SOCKET_BONE = 'Xhead'

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
rig.name = 'Icky_Rig'
body = bpy.data.objects['Body']
body.name = 'Icky'
body.data.name = 'Icky'
wings = bpy.data.objects['Wings']
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
wings.data.materials.clear()
for m in list(bpy.data.materials):
    if m.name.startswith(('Icky', 'Icky_Wing')):
        bpy.data.materials.remove(m)
body.data.materials.append(material('Icky', 'icky_basecolor_final.png', 'icky_normal_1k.png',
                                    'icky_metal_rough_1k.png'))
wings.data.materials.clear()
wings.data.materials.append(material('Icky_Wing', 'icky_wing_basecolor.png', None, 'icky_wing_metal_rough.png'))
wings.data.uv_layers[0].name = body.data.uv_layers[0].name
# mouth socket: centre of the teeth in the bind pose, carried by the skull
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
for name in ('piece', 'chain'):
    if name in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[name])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])
# join the wings into the body (two materials, one skinned mesh)
for o in bpy.data.objects:
    o.select_set(o in (body, wings))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import, C.ICKY)
recs = report.pop('_recs')
# Running: Flap faster (sources read again from the MM9 action)
flap = C.read_keys(bpy.data.actions['Flap'], fps_import)
for r in flap.values():
    C.close_seam(r)
dur = next(iter(flap.values()))['t'][-1]
act, n = C.write_action(rig, 'Running', flap, dur, True, rate=C.RUN_RATE)
report['clips']['Running'] = {'sources': ['Flap'], 'loop': True, 'rate': C.RUN_RATE, 'duration': n / C.FPS,
                              'frames': n}
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
