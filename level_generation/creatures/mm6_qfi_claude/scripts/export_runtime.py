"""Runtime export: work/anim_v4.blend (rig, twist bones, game clips, Meshy UVs, head UVs) -> export/mm6_qfi_lod0.glb.

Meshes: 'Queen' (skinned; materials QueenBody = body set 1K on UVMap and QueenHead = head set 1K, the head faces'
HeadUV copied into UVMap) and 'Alcove' (the rock, rigid on the Rock bone; material Rock, base colour 2K). Sockets Socket_Palm_L/R
(non-deforming bones on the palms). Clips Standing, Attack, Cast, Hit, Death and Dead (the last Death pose held 1 s);
quaternion keys sign-continuous; keys at 30 fps. Writes export/export_info.json."""
import bpy, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
T = P / 'textures'
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']; rock = bpy.data.objects['Rock']
me = queen.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
part = np.array([p.value for p in me.attributes['part'].data])
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if part[p.index]:
        for li in p.loop_indices:
            buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])


def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(str(T / f))
        n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


me.materials.clear()
me.materials.append(material('QueenBody', 'qfi_basecolor_1k.png', 'qfi_normal_1k.png', 'qfi_metal_rough_1k.png'))
me.materials.append(material('QueenHead', 'qfi_head_basecolor_1k.png', 'qfi_head_normal_1k.png',
                             'qfi_head_metal_rough_1k.png'))
me.polygons.foreach_set('material_index', part.tolist())
rock.name = 'Alcove'                    # the 'Rock' bone carries it; node names must be unique in the GLB
rock.data.materials.clear()
rock.data.materials.append(material('Rock', 'qfi_rock_basecolor_2k.png', 'qfi_rock_normal_1k.png',
                                    'qfi_rock_metal_rough_1k.png'))
for at in [a.name for a in me.attributes if a.name in ('part',)]:
    me.attributes.remove(me.attributes[at])
for ca in list(me.color_attributes):
    me.color_attributes.remove(ca)

# ---------------------------------------------------------------- Dead held 1 s
death = bpy.data.actions['Death']; rig.animation_data.action = death
if len(death.slots):
    rig.animation_data.action_slot = death.slots[0]
scene.frame_set(int(death.frame_range[1]))
held = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Dead'])
dead = bpy.data.actions.new('Dead'); dead.use_fake_user = True
rig.animation_data.action = dead
for f in (0, 30):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion, pb.location, pb.scale = held[pb.name]
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
        pb.keyframe_insert('scale', frame=f)
dead.use_frame_range = True; dead.frame_start, dead.frame_end = 0, 30
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


def fcurves(action):
    return [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


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
KEEP = ('Standing', 'Attack', 'Cast', 'Hit', 'Death', 'Dead')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
st = bpy.data.actions['Standing']; rig.animation_data.action = st
if len(st.slots):
    rig.animation_data.action_slot = st.slots[0]
(P / 'export').mkdir(exist_ok=True)
out = P / 'export' / 'mm6_qfi_lod0.glb'
for o in bpy.data.objects:
    o.select_set(o in (queen, rock, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(queen.matrix_world @ v.co) for v in me.vertices])
rc = np.array([tuple(rock.matrix_world @ v.co) for v in rock.data.vertices])
info = {'glb': str(out), 'queen_triangles': sum(len(p.vertices) - 2 for p in me.polygons),
        'rock_triangles': sum(len(p.vertices) - 2 for p in rock.data.polygons),
        'queen_bounds': [co.min(0).round(3).tolist(), co.max(0).round(3).tolist()],
        'rock_bounds': [rc.min(0).round(3).tolist(), rc.max(0).round(3).tolist()],
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
(P / 'export' / 'export_info.json').write_text(json.dumps(info, indent=1))
print('EXPORTED', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'export' / 'mm6_qfi.blend'))
