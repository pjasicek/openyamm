"""Animated master + export for the Greater Demon, v2 (2026-10-30 rework): rename rig/mesh, add the mouth socket, build
the role clips from the MM9 clips (clips_mm9.py), assign the composed v2 textures and export.
Materials: GreaterDemon (body, wing bones, spikes: the v2 body maps), GreaterDemon_Wing (membrane, piece 3: same maps,
own slot so the shadow shrink keeps the thin shell), GreaterDemonHead (the three heads, head > 0: the 1K head set;
their HeadUV is copied into the single UV layer).

Args: <uv blend> <out anim blend> <out glb> <clip report json>
Roles (MM9 STAGE2DEMON.abc): Standing stand, Walking walk, Running run, Fidget fidget1, AttackMelee Hattack1,
AttackRanged Rattack1 (also the cast: the row has no spells), Hit wince1, Death die1, Dead = die1's last pose.
Socket_Mouth: the main mouth (between the snout tip Xhnose and the chin Xhchin), carried by Xhead; MM9 releases its
missile from the jaw pivot (RangeAttack socket on Xhjawpiv).
"""
import bpy, sys, os, json
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT_BLEND, OUT_GLB, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NAME = 'GreaterDemon'
ROLES = {
    'Standing': (['stand'], True),
    'Walking': (['walk'], True),
    'Running': (['run'], True),
    'Fidget': (['fidget1'], False),
    'AttackMelee': (['Hattack1'], False),
    'AttackRanged': (['Rattack1'], False),
    'Hit': (['wince1'], False),
    'Death': (['die1'], False),
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


import numpy as np
import bmesh
me = body.data
# stray loose bits left by the decimation (single triangles off the elbows, detached_parts_audit.py): drop loose parts
# of fewer than 3 faces
bmx = bmesh.new(); bmx.from_mesh(me); bmx.faces.ensure_lookup_table()
seen, stray = set(), []
for f in bmx.faces:
    if f.index in seen:
        continue
    comp, st = [], [f]; seen.add(f.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
    if len(comp) < 3:
        stray += comp
bmesh.ops.delete(bmx, geom=stray, context='FACES')
bmesh.ops.delete(bmx, geom=[v for v in bmx.verts if not v.link_faces], context='VERTS')
bmx.to_mesh(me); bmx.free()
print('STRAY faces removed', len(stray))
me.materials.clear()
me.materials.append(material(NAME, 'gdemon_v2_basecolor_graded.png', 'gdemon_v2_normal_1k.png',
                             'gdemon_v2_metal_rough_1k.png'))
me.materials.append(material(NAME + '_Wing', 'gdemon_v2_basecolor_graded.png', 'gdemon_v2_normal_1k.png',
                             'gdemon_v2_metal_rough_1k.png'))
me.materials.append(material(NAME + 'Head', 'gdemon_v2_head_basecolor_1k.png', 'gdemon_v2_head_normal_1k.png',
                             'gdemon_v2_head_metal_rough_1k.png'))
pc = me.attributes['piece']
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
buv, huv = me.uv_layers['UVMap'].data, me.uv_layers['HeadUV'].data
for p in me.polygons:
    if hd[p.index] > 0:
        p.material_index = 2
        for li in p.loop_indices:
            buv[li].uv = huv[li].uv
    else:
        p.material_index = 1 if all(pc.data[i].value == 3 for i in p.vertices) else 0
me.uv_layers.remove(me.uv_layers['HeadUV'])
me.uv_layers.active = me.uv_layers['UVMap']
J = {b.name: rig.matrix_world @ b.head_local for b in rig.data.bones}
mouth = (J['Xhnose'] * 0.55 + J['Xhchin'] * 0.45)
sock = bpy.data.objects.new('Socket_Mouth', None)
sc.collection.objects.link(sock)
sock.parent = rig
sock.parent_type = 'BONE'
sock.parent_bone = 'Xhead'
bpy.context.view_layer.update()
sock.matrix_world = Matrix.Translation(mouth)
for a in ('piece', 'side', 'head', 'anchor'):
    if a in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[a])
if 'bone' in body.data.color_attributes:
    body.data.color_attributes.remove(body.data.color_attributes['bone'])

fps_import = sc.render.fps / sc.render.fps_base
originals = list(bpy.data.actions)
report = C.build_role_clips(rig, fps_import, ROLES)
report.pop('_recs')
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
