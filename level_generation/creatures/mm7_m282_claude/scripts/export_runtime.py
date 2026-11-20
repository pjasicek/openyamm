"""Runtime export (Medusa, after mm7_m278_claude / mm7_m214_claude): work/anim_v2.blend (rig, procedural clips, UVs)
-> export/mm7_m282_lod0.glb and export/export_info.json. The bow, string and arrow objects are joined into the one
skinned mesh 'M282' with materials M282_A (body set 1K), M282Head_A (head set 1K, faces with
attribute head), Bow and Arrow (own small textures; split into attachments by build_runtime.sh). The string keeps the
body material (a swatch, textures/m282_swatches.json) so it stays in the body after the split.
Clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget at 30 fps; quaternion keys sign-continuous.
Args: none"""
import bpy, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v2.blend'))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
SW = json.load(open(os.path.join(T, 'm282_swatches.json')))


def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


for m in list(bpy.data.materials):                               # the props' working materials (props.blend)
    m.name = '_work_' + m.name
mats = [material('M282_A', 'm282_basecolor_1k.png', 'm282_normal_1k.png', 'm282_metal_rough_1k.png'),
        material('M282Head_A', 'm282_head_basecolor_1k.png', 'm282_head_normal_1k.png', 'm282_head_metal_rough_1k.png'),
        material('Bow', 'props/bow_basecolor.png', 'props/bow_normal.png', 'props/bow_metal_rough.png'),
        material('Arrow', 'props/arrow_basecolor.png', 'props/arrow_normal.png', 'props/arrow_metal_rough.png')]
me = body.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
me.materials.clear()
for m in mats:
    me.materials.append(m)
me.polygons.foreach_set('material_index', hd.tolist())
for at in [a.name for a in me.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
    me.attributes.remove(me.attributes[at])
# props: material slots, the string onto the body swatch, joined into the body
props = []
for name, slot in (('BowMesh', 2), ('StringMesh', 0), ('ArrowMesh', 3)):
    o = bpy.data.objects[name]; pm = o.data
    pm.materials.clear()
    for m in mats:
        pm.materials.append(m)
    pm.polygons.foreach_set('material_index', [slot] * len(pm.polygons))
    if name == 'StringMesh':
        for l in pm.uv_layers['UVMap'].data:
            l.uv = SW['string_uv']
    for g in body.vertex_groups:
        if g.name not in o.vertex_groups:
            o.vertex_groups.new(name=g.name)
    props.append(o)
for o in bpy.data.objects:
    o.select_set(o in props or o is body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'M282'
# ---------------------------------------------------------------- signs, export


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for act in bpy.data.actions:
    curves = {}
    for fc in fcurves(act):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values():
            fc.update()
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm7_m282_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
mi = np.array([p.material_index for p in body.data.polygons]); tri = np.array([len(p.vertices) - 2 for p in body.data.polygons])
info = {'glb': out, 'head_set': True, 'tris': int(tri.sum()),
        'tris_by_material': {m.name: int(tri[mi == k].sum()) for k, m in enumerate(mats)},
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'bones': len(rig.data.bones),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'export_master.blend'))
print('EXPORTED', json.dumps(info))
