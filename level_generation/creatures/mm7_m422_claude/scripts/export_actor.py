"""Runtime export (batch-B robed casters; creature.json prefix/mesh/out): work/rig_v6.blend (gated rig, timed clips, Meshy UVs, head split) ->
export/<out>_lod0.glb. One skinned mesh <mesh>: materials <mesh>_A (body set 1K, UVMap) and <mesh>Head_A (head set 1K,
HeadUV written into TEXCOORD_0 for the head faces). Socket bones (non-deforming, children of the hands):
'Socket_Palm_L' / 'Socket_Palm_R' on each claw's palm, 3 cm out of it (the missile leaves the left palm, the spell
charges at both). Clips Standing, Walking, Attack, Cast, Hit, Death, Fidget and Dead (Death's last frame held 1 s);
keys at 30 fps, quaternions sign-continuous. No Running: speeds 160-200 stay below the run threshold (run binds to
Walking). Adapted from mm6_natm_claude/scripts/export_runtime.py. Args: none"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
X, NAME, OUTN = cfg.C['prefix'], cfg.C['mesh'], cfg.C['out']
HANDS = cfg.HANDS
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HEAD = os.path.exists(os.path.join(T, f'{X}_head_basecolor_1k.png'))
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
if HEAD:
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
if 'HeadUV' in me.uv_layers:
    me.uv_layers.remove(me.uv_layers['HeadUV'])
# ---------------------------------------------------------------- palm sockets from the hand meshes
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.array([a.value for a in me.attributes['piece'].data])
sock = {}
for s, piece in HANDS.items():
    wr = np.array(rig.data.bones[f'B_{s}_Hand'].head_local); fa = np.array(rig.data.bones[f'B_{s}_Forearm'].head_local)
    ax = (wr - fa) / np.linalg.norm(wr - fa)
    hv = co[(pv == piece) & ((co - wr) @ ax > 0.0)]
    tip = hv[np.argmax((hv - wr) @ ax)]; hl = float((tip - wr) @ ax)
    palm = hv[((hv - wr) @ ax > 0.15 * hl) & ((hv - wr) @ ax < 0.5 * hl)]
    c = palm.mean(0); U = np.linalg.svd(palm - c)[2]; n = U[2]
    if (n[0] > 0) == (s == 'L'):                                   # palms face the thighs at rest (medial)
        n = -n
    sock[s] = (Vector(c + n * 0.03), Vector(n))
    print('SOCKET', s, np.round(c, 3).tolist(), 'normal', np.round(n, 2).tolist(), 'hand length', round(hl, 3))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for s, (p, n) in sock.items():
    eb = rig.data.edit_bones.new(f'Socket_Palm_{s}'); eb.head = p; eb.tail = p + n * 0.05
    eb.parent = rig.data.edit_bones[f'B_{s}_Hand']; eb.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
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


mats = [material(f'{NAME}_A', f'{X}_basecolor_1k.png', f'{X}_normal_1k.png', f'{X}_metal_rough_1k.png')]
if HEAD:
    mats.append(material(f'{NAME}Head_A', f'{X}_head_basecolor_1k.png', f'{X}_head_normal_1k.png', f'{X}_head_metal_rough_1k.png'))
me.materials.clear()
for m in mats:
    me.materials.append(m)
me.polygons.foreach_set('material_index', (hd if HEAD else np.zeros_like(hd)).tolist())
staff = bpy.data.objects.get('Staff')
if staff is not None:                                # rigid prop on bone 'Staff', split into an attachment by build_runtime
    staff.modifiers.clear()
    staff.data.materials.clear(); staff.data.materials.append(material('Staff_A', f'{X}_staff_basecolor.png', f'{X}_staff_normal.png', f'{X}_staff_metal_rough.png'))
    for o in bpy.data.objects:
        o.select_set(o in (body, staff))
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    print('PROP staff joined, tris', sum(len(p.vertices) - 2 for p in body.data.polygons))
body.name = body.data.name = NAME
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co')]:
    body.data.attributes.remove(body.data.attributes[at])
# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if len(death.slots):
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
KEEP = ('Standing', 'Walking', 'Attack', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', f'{OUTN}_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=bool(cfg.C.get("max_influences", 4) > 4), export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
info = {'glb': out, 'head_set': HEAD, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()), 'bones': len(rig.data.bones),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', 'export_info.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
bpy.ops.file.pack_all()                                            # the editable master carries its textures
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'export', f'{OUTN}.blend'))
