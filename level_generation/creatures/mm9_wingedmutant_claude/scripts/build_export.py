"""Animated master + export for the Winged Mutant family: rename rig/mesh, add the mouth socket, build the role clips
from the MM9 clips (clips_mm9.py), assign the composed textures and export export/mm9_wingedmutant_lod0.glb.

Args: <uv blend> <out anim blend> <out glb> <clip report json>
Roles (MM9 WINGEDMUTANT.abc, a flier): Standing StandAir, Walking Flap (MM9 has no walk: it flies), Running Flap
played RUN_RATE times faster, Fidget FidgetAir1, AttackMelee HAttackAir1, AttackRanged RAttack1 (also the cast:
Sparks / Elemental Bolt), Hit WinceAir1, Death dieair1 + fall1 + falldown1 (joins blended), Dead = the last pose.
Socket_Mouth: in front of the lips (the front-most lower-face vertices), carried by Bip01 Head; MM9's own sockets
sit on Spine2 (Mouth) and a foot claw (RangeAttack), which would launch the spells from the chest or the talons.
"""
import bpy, sys, os, json
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'Wmut'
RUN_RATE = 1.25
ROLES = {
    'Standing': (['StandAir'], True),
    'Walking': (['Flap'], True),
    'Fidget': (['FidgetAir1'], False),
    'AttackMelee': (['HAttackAir1'], False),
    'AttackRanged': (['RAttack1'], False),
    'Hit': (['WinceAir1'], False),
    'Death': (['dieair1', 'fall1', 'falldown1'], False),
}

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
body.data.materials.append(material(NAME, 'wmut_basecolor_graded_v2.png', 'wmut_normal_1k.png',
                                    'wmut_metal_rough_1k.png'))
# the wing membranes (faces mostly weighted to the Yw* wing bones; open sheets with their back-face copies) get their
# own material slot with the same maps, so the shadow shrink leaves the thin sheets in place
body.data.materials.append(material(NAME + '_Wing', 'wmut_basecolor_graded_v2.png', 'wmut_normal_1k.png',
                                    'wmut_metal_rough_1k.png'))
gn = {g.index: g.name for g in body.vertex_groups}
wing_w = [sum(g.weight for g in v.groups if gn[g.group].startswith('Yw')) for v in body.data.vertices]
for p in body.data.polygons:
    p.material_index = 1 if sum(wing_w[i] for i in p.vertices) / len(p.vertices) > 0.5 else 0
# rework 2026-10-30: the grafted head (face attribute 'head') takes the 1K head set on its HeadUV, copied into the
# single UV layer; material Wmut_Head (its own region mask, the body's ramps: textures/wmut_ramps_v2.json)
me = body.data
HEADSET = 'head' in me.attributes and 'HeadUV' in me.uv_layers
if HEADSET:
    body.data.materials.append(material(NAME + '_Head', 'wmut_head_basecolor.png', 'wmut_head_normal_1k.png',
                                        'wmut_head_metal_rough_1k.png'))
    hd = [0] * len(me.polygons)
    me.attributes['head'].data.foreach_get('value', hd)
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            p.material_index = 2
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
    me.uv_layers.active = me.uv_layers['UVMap']
    me.uv_layers.remove(me.uv_layers['HeadUV'])
J = {b.name: rig.matrix_world @ b.head_local for b in rig.data.bones}
hg = body.vertex_groups['Bip01 Head'].index
teeth = []
if 'kind' in me.attributes:
    kd = [0] * len(me.vertices)
    me.attributes['kind'].data.foreach_get('value', kd)
    teeth = [body.matrix_world @ me.vertices[i].co for i in range(len(kd)) if kd[i] == 4]
hv = [body.matrix_world @ v.co for v in body.data.vertices
      if any(g.group == hg and g.weight > 0.6 for g in v.groups)]
zmid = sorted(p.z for p in hv)[len(hv) // 2]
low = [p for p in hv if p.z < zmid]
ymin = min(p.y for p in low)
front = [p for p in low if p.y < ymin + 0.015]
mouth = sum(front, Vector()) / len(front) + Vector((0, -0.02, 0))
if teeth:            # the grafted head: just in front of the teeth
    mouth = sum(teeth, Vector()) / len(teeth) + Vector((0, -0.02, 0))
mouth.x = 0.0   # on the symmetry plane
sock = bpy.data.objects.new('Socket_Mouth', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = 'Bip01 Head'
bpy.context.view_layer.update()
sock.matrix_world = Matrix.Translation(mouth)
for a in ('piece', 'side', 'head', 'bridge', 'kind'):
    if a in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[a])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import, ROLES)
recs = report.pop('_recs')
flap = next(a for a in originals if a.name == 'Flap')
rec = C.read_keys(flap, fps_import)
for r in rec.values():
    C.close_seam(r)
dur = next(iter(rec.values()))['t'][-1] - next(iter(rec.values()))['t'][0]
act_r, nr = C.write_action(rig, 'Running', rec, dur, True, rate=RUN_RATE)
report['clips']['Running'] = {'sources': ['Flap'], 'loop': True, 'rate': RUN_RATE, 'duration': nr / C.FPS,
                              'frames': nr}
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
