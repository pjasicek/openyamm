"""Runtime export of the retextured reduced thief: work/master_tex.blend -> export/mm6_thf_tex_lod0.glb, after
../mm6_thf_claude/scripts/export_runtime.py. Three materials by the face attribute `tex_set`: Thief_A (body set),
ThiefCloak_A (cloak and hood), ThiefHead_A (the kept face and hair set). Daggers: every dagger face into one of the
body set's swatches by its position along the dagger bone (pommel and guard iron, grip leather, blade steel).
Game clips only (Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget), quaternion keys sign-continuous."""
import json
import os

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_tex.blend'))
mesh, rig = bpy.data.objects['Thief'], bpy.data.objects['Thief_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()


def fcurves(action):
    return [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


def fix_quaternion_signs(action):
    curves = {}
    for fc in fcurves(action):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    flipped = 0
    for comps in curves.values():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]
        prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] = -keys[i][j].co[1]
                    keys[i][j].handle_left[1] = -keys[i][j].handle_left[1]
                    keys[i][j].handle_right[1] = -keys[i][j].handle_right[1]
                q = [-x for x in q]
                flipped += 1
            prev = q
        for fc in comps.values():
            fc.update()
    return flipped


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(T, fname))
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


mesh.data.materials.clear()
mesh.data.materials.append(material('Thief_A', 'thf_body_basecolor_1k.png', 'thf_body_normal_1k.png',
                                     'thf_body_metal_rough_1k.png'))
mesh.data.materials.append(material('ThiefCloak_A', 'thf_cloak_basecolor_1k.png', 'thf_cloak_normal_1k.png',
                                     'thf_cloak_metal_rough_1k.png'))
mesh.data.materials.append(material('ThiefHead_A', 'thf_head_basecolor_1k.png', 'thf_head_normal_1k.png',
                                     'thf_head_metal_rough_1k.png'))
tex_set = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['tex_set'].data.foreach_get('value', tex_set)
mesh.data.polygons.foreach_set('material_index', tex_set)

OWN_DAGGER_UVS = 'dagger_piece' in mesh.data.attributes           # rebuilt daggers carry their own UVs (dagger_mesh.py)
SW = json.load(open(os.path.join(T, 'thf_dagger_swatches.json'))) if not OWN_DAGGER_UVS else {}
parts = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(mesh.data.polygons), np.int32)
mesh.data.attributes['part'].data.foreach_get('value', part)
GRIP_L = 0.085
uvl = mesh.data.uv_layers.active.data
counts = {}
for side in ('L', 'R'):
    b = rig.data.bones['Dagger' + side]
    h0 = rig.matrix_world @ b.head_local
    ax = (rig.matrix_world @ b.tail_local - h0).normalized()
    for p in mesh.data.polygons:
        if OWN_DAGGER_UVS or parts[part[p.index]] != 'Dagger':
            continue
        c = mesh.matrix_world @ p.center
        if (c - h0).length > 0.3 or ((c.x > 0) != (h0.x > 0)):
            continue
        s_ = (c - h0).dot(ax)
        name = 'blade' if s_ > GRIP_L / 2 + 0.012 else ('grip' if -GRIP_L / 2 < s_ < GRIP_L / 2 else 'iron')
        u, v, r = SW[name]
        for k, li in enumerate(p.loop_indices):
            ang = 2.0 * np.pi * k / len(p.loop_indices)
            uvl[li].uv = (u + r * np.cos(ang), v + r * np.sin(ang))
        counts[name] = counts.get(name, 0) + 1
print('DAGGER faces', counts)
for a in [a.name for a in mesh.data.attributes if a.name in ('part', 'uv_region', 'hid', 'head', 'tex_set', 'dagger_piece', 'maw_kind')]:
    mesh.data.attributes.remove(mesh.data.attributes[a])

KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP:
        bpy.data.actions.remove(a)
print('SIGNS', {a.name: fix_quaternion_signs(a) for a in bpy.data.actions})
st = bpy.data.actions['Standing']
rig.animation_data.action = st
if st.slots:
    rig.animation_data.action_slot = st.slots[0]
bpy.context.scene.frame_set(0)
out = os.path.join(HERE, 'export', 'mm6_thf_tex_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, [a.name for a in bpy.data.actions], sum(len(p.vertices) - 2 for p in mesh.data.polygons))
