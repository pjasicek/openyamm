"""Runtime export (m150, from mm7_m406_claude): work/rig_v6.blend (gated rig, timed clips, wings, Meshy UVs, head split)
-> export/mm7_m150_lod0.glb. One skinned mesh 'M150': materials M150_A (body + wings, 1K, UVMap), M150Head_A (head set
1K, HeadUV as TEXCOORD_0), Sword_A (the Meshy flamberge, import_sword.py) and Shield_A (make_props_m150.py). Bone
'Shield' (child of B_L_Forearm at FOREARM_T of the forearm, +Y toward the hand, +Z out of the back of the forearm,
laterally away from the body) carries the shield 100 %; it is split into its own attachment like the sword. Bone added: 'Sword' (child of B_R_Hand at the solved handle, +Y along
the source grip axis toward the tip, +X toward the cutting (convex) edge: the knuckle direction turned BLADE_ROLL
about the grip axis, bar1's rule; blade_edge_gate.py checks the edge leads). The sword is skinned 100 % to it and
split into an attachment later (tools/split_attachment.py). Clips Standing, Walking, Running, Attack, Hit, Death,
Fidget and Dead (last Death frame held 1 s); keys at 30 fps, quaternions sign-continuous. Args: none"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))   # clips synced from rig_v5 (sync_actions.py)
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, 'm150_head_basecolor_1k.png'))

# ---------------------------------------------------------------- head UVs into the single UV layer
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
if HEAD:
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])

# ---------------------------------------------------------------- sword bone (bar1 rule) and the sword mesh
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
AXL = Vector(G['handle_axis_hand_local']).normalized(); GCL = Vector(G['handle_centre_hand_local'])
Hm = rig.data.bones['B_R_Hand'].matrix_local
c = Hm @ GCL; ax = (Hm.to_3x3() @ AXL).normalized()
kn = rig.data.bones['B_R_Finger2'].head_local
side = (kn - c); side = (side - ax * side.dot(ax)).normalized()
BLADE_ROLL = math.radians(float(os.environ.get('BLADE_ROLL', '90')))   # blade_edge_gate.py sweep 2026-10-20: attack 0.70, walk 0.83, fidget 0.78
SX = (side * math.cos(BLADE_ROLL) + ax.cross(side) * math.sin(BLADE_ROLL)).normalized(); SZ = SX.cross(ax)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Sword'); eb.head = c; eb.tail = c + ax * 0.15; eb.parent = rig.data.edit_bones['B_R_Hand']; eb.align_roll(SZ)
bpy.ops.object.mode_set(mode='OBJECT')
# shield frame on the left forearm: +Y along the forearm toward the hand, +Z out of the back of the forearm (in the
# A-pose rest the back of the left forearm faces laterally out, +X)
F0, F1 = rig.data.bones['B_L_Forearm'].head_local, rig.data.bones['B_L_Hand'].head_local
fy = (F1 - F0).normalized(); fz = Vector((1, 0, 0)); fz = (fz - fy * fz.dot(fy)).normalized(); fx = fy.cross(fz)
FOREARM_T = float(os.environ.get('FOREARM_T', '0.55'))
sc0 = F0 + (F1 - F0) * FOREARM_T
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Shield'); eb.head = sc0; eb.tail = sc0 + fy * 0.15; eb.parent = rig.data.edit_bones['B_L_Forearm']; eb.align_roll(fz)
bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
    dst.objects = ['SwordMesh', 'ShieldMesh'] + ([] if 'HelmetFitted' in bpy.data.objects else ['HelmetMesh'])
props = []
if 'HelmetFitted' in bpy.data.objects:                        # helmet_fit.py: fitted and cheek guards bent, world space
    hf = bpy.data.objects['HelmetFitted']; hf.hide_render = hf.hide_viewport = False; hf.name = 'HelmetMesh'
    hf.vertex_groups.new(name='Helmet').add(list(range(len(hf.data.vertices))), 1.0, 'REPLACE')
    props.append(hf)
    print('PROP Helmet', sum(len(p.vertices) - 2 for p in hf.data.polygons), 'tris (fitted)')
for o in dst.objects:
    scene.collection.objects.link(o)
    if o.name.startswith('Sword'):
        M = Matrix((SX, ax, SZ)).transposed().to_4x4(); M.translation = c; bone = 'Sword'
    elif o.name.startswith('Helmet'):                          # v2: fitted on the head by helmet_fit.py
        HF = json.load(open(os.path.join(HERE, 'work', 'helmet_fit.json')))
        sc_ = HF['scale'] if isinstance(HF['scale'], list) else [HF['scale']] * 3
        M = Matrix.Translation(Vector(HF['offset'])) @ Matrix.Diagonal(tuple(sc_) + (1,)); bone = 'Helmet'
    else:
        M = Matrix((fx, fy, fz)).transposed().to_4x4(); M.translation = sc0; bone = 'Shield'
    o.data.transform(M); o.matrix_world = Matrix()
    o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    props.append(o)
    print('PROP', bone, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris, sword roll deg', round(math.degrees(BLADE_ROLL), 1))
# ---------------------------------------------------------------- materials


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


mats = [material('M150_A', 'm150_basecolor_1k.png', 'm150_normal_1k.png', 'm150_metal_rough_1k.png')]
if HEAD:
    mats.append(material('M150Head_A', 'm150_head_basecolor_1k.png', 'm150_head_normal_1k.png', 'm150_head_metal_rough_1k.png'))
pm = [material('Sword_A', 'm150_sword_basecolor.png', 'm150_sword_normal.png', 'm150_sword_metal_rough.png'),
      material('Shield_A', 'm150_shield_basecolor.png', 'm150_shield_normal.png', 'm150_shield_metal_rough.png'),
      material('Helmet_A', 'm150_helmet_basecolor.png', 'm150_helmet_normal.png', 'm150_helmet_metal_rough.png')]
me.materials.clear()
for m in mats + pm:
    me.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
for o in props:
    o.data.materials.clear(); o.data.materials.append(pm[0] if o.name.startswith('Sword') else pm[2] if o.name.startswith('Helmet') else pm[1])
for o in bpy.data.objects:
    o.select_set(o in [body] + props)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'M150'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
    body.data.attributes.remove(body.data.attributes[at])

# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if getattr(death, 'slots', None) is not None and len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
dead = bpy.data.actions.get('Dead') or bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


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
KEEP = ('Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')   # m150: flies, no run
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if getattr(st, 'slots', None) is not None and len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm7_m150_lod0.glb')
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
info = {'glb': out, 'head_set': HEAD, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
