"""hkr runtime export: the gated chain (work/rig_v3t.blend) -> export/<name>_lod0.glb.
One skinned mesh 'HKR' (the attachments are split from it later by split_attachments_hkr.py, one per bone):
- the MM6 Demon body with its own materials (Demon_Body_A 2K set, Demon_White_Claws, Demon_Iris now glowing orange,
  Demon_Black_Pupil) and the horns (body material);
- MODE=trooper (default): + every armour piece and prop (Arm_*: material HKR_Plate on the armour atlas, HKR_Glow
  emissive): the skinned shell (skin_shell.py weights; it stays in the skinned mesh) and the rigid small parts, each
  100 % on its bone (split out as attachments), and the carbine (object Rifle: Rifle_A on the carbine texture,
  Rifle_Glow emissive); the skin under the shell (`shell_hidden`) is deleted;
- MODE=base: the bare Kreegan body only, plus the MM6 Demon's own clips carried onto the B_* rig (Demon_*), so a bare
  caste (the Drudge) can use them.
Clips: Standing, Walking, Running, Attack, Hit, Death, Dead (Death's last frame held 1 s), Fidget; 30 fps keys,
quaternions sign-continuous. Args: none (env MODE, OUT)"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
MODE = os.environ.get('MODE', 'trooper')
OUTN = os.environ.get('OUT', 'hes_kreegan_trooper' if MODE == 'trooper' else 'hes_kreegan_base')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('SRC', 'rig_v3t.blend')))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()


def material(name, base, normal, mr, emit=None, rough=0.5):
    m = bpy.data.materials.get(name)
    if m is not None:
        m.name = name + '_old'
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    if base:
        def tex(f, cs):
            n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
            return n
        nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Roughness'].default_value = rough; bsdf.inputs['Metallic'].default_value = 0.0
    if emit:
        bsdf.inputs['Base Color'].default_value = (*emit, 1.0)
        bsdf.inputs['Emission Color'].default_value = (*emit, 1.0); bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


# the eyes glow orange (concept): the demon's iris material
iris = bpy.data.materials.get('Demon_Iris')
if iris is not None and iris.node_tree:
    b = next(n for n in iris.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (1.0, 0.42, 0.08, 1.0)
    b.inputs['Emission Color'].default_value = (1.0, 0.42, 0.08, 1.0); b.inputs['Emission Strength'].default_value = 1.0
parts = [body]
if MODE != 'trooper' and 'thin_co' in body.data.attributes:
    # the bare Kreegan keeps the thin Demon shape (bulk_body.py bulks the Trooper caste only)
    th = np.zeros(len(body.data.vertices) * 3); body.data.attributes['thin_co'].data.foreach_get('vector', th)
    body.data.vertices.foreach_set('co', th); body.data.update()
    print('THIN restored for the base')
if MODE == 'trooper' and 'shell_hidden' in body.data.attributes:
    # the skin under the skinned shell's pieces (skin_shell.py) goes: no poke-through, fewer triangles
    import bmesh
    hid = [x.value for x in body.data.attributes['shell_hidden'].data]
    bm = bmesh.new(); bm.from_mesh(body.data)
    dead = [f for f in bm.faces if all(hid[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(body.data); bm.free()
    print('SHELLSKIN removed', len(dead), 'skin faces under the shell')
if MODE == 'trooper':
    plate = material('HKR_Plate', 'hkr_armour_basecolor.png', 'hkr_armour_normal.png', 'hkr_armour_metal_rough.png')
    glow = material('HKR_Glow', None, None, None, emit=(1.0, 0.42, 0.08), rough=0.4)
    rifle = material('Rifle_A', 'hkr_carbine_basecolor.png', 'hkr_carbine_normal.png', 'hkr_carbine_metal_rough.png')
    rglow = material('Rifle_Glow', None, None, None, emit=(1.0, 0.42, 0.08), rough=0.4)
    for o in [o for o in bpy.data.objects if o.name.startswith('Arm_')]:
        slots = [p.material_index for p in o.data.polygons]
        o.data.materials.clear(); o.data.materials.append(plate); o.data.materials.append(glow)
        o.data.polygons.foreach_set('material_index', slots); o.modifiers.clear(); parts.append(o)
    gun = bpy.data.objects['Rifle']
    slots = [p.material_index for p in gun.data.polygons]
    gun.data.materials.clear(); gun.data.materials.append(rifle); gun.data.materials.append(rglow)
    gun.data.polygons.foreach_set('material_index', slots); gun.modifiers.clear(); parts.append(gun)
    # the carbine's glow rides bone Rifle too (one attachment with two primitives)
    if 'RifleGlow' in gun.vertex_groups:
        g = gun.vertex_groups['RifleGlow']; r = gun.vertex_groups['Rifle']
        idx = [v.index for v in gun.data.vertices if any(e.group == g.index for e in v.groups)]
        r.add(idx, 1.0, 'REPLACE'); gun.vertex_groups.remove(g)
else:
    for o in [o for o in bpy.data.objects if o.name.startswith('Arm_') or o.name == 'Rifle']:
        bpy.data.objects.remove(o, do_unlink=True)
body.modifiers.clear()
for o in bpy.data.objects:
    o.select_set(o in parts)
bpy.context.view_layer.objects.active = body
if len(parts) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'HKR'
for at in [a.name for a in body.data.attributes if a.name in ('piece', 'garment', 'finger', 'head', 'orig_co', 'shell_hidden', 'thin_co')]:
    body.data.attributes.remove(body.data.attributes[at])
body.parent = rig; md = body.modifiers.new('Armature', 'ARMATURE'); md.object = rig
# drop the demon's burn-death extras (the Kreegans leave a corpse; the burn maps do not cover the horns)
for m in bpy.data.materials:
    for k in [k for k in m.keys() if 'burn' in k]:
        del m[k]
# ---------------------------------------------------------------- demon clips for the bare base (world copy, same joints)
if MODE == 'base' or os.environ.get('DEMON') == '1':
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'demon_clips.blend'), link=False) as (s_, d_):
        d_.objects = ['Demon']; d_.actions = [n for n in s_.actions if n.startswith('Demon_src_')]
    dem = d_.objects[0]; scene.collection.objects.link(dem); DM = json.loads(scene['demon_map'])
    pairs = [(n, DM[n]) for n in DM if n in rig.pose.bones and DM[n] in dem.pose.bones]
    extra = [n for n in ('Bone_020', 'Bone_019', 'Bone_018', 'Bone_017', 'Bone_016', 'Bone_015', 'Bone_025') if n in dem.pose.bones]
    pairs += [(n, n) for n in extra]
    dem.animation_data_create()
    src_acts = [a for a in bpy.data.actions if a.name.startswith('Demon_src_')]
    for sa in src_acts:
        dem.animation_data.action = sa
        if len(sa.slots): dem.animation_data.action_slot = sa.slots[0]
        f0, f1 = (int(round(x)) for x in sa.frame_range)
        na = bpy.data.actions.new('Demon_' + sa.name[len('Demon_src_'):]); na.use_fake_user = True
        rig.animation_data.action = na
        SRC_FPS = 24.0                                   # the demon's clips were imported at 24 fps; keys here are 30 fps
        nout = int(round((f1 - f0) / SRC_FPS * 30.0))
        for k in range(nout + 1):
            sf = f0 + k * SRC_FPS / 30.0; scene.frame_set(int(sf), subframe=sf - int(sf)); f = k + f0
            for n, dn in pairs:
                Rd = (dem.matrix_world @ dem.pose.bones[dn].matrix).to_3x3()
                Rd0 = (dem.matrix_world @ dem.data.bones[dn].matrix_local).to_3x3()
                Ro0 = rig.data.bones[n].matrix_local.to_3x3()
                Rw = Rd @ Rd0.inverted() @ Ro0
                M = Rw.to_4x4()
                if n == 'B_Pelvis':
                    M.translation = (dem.matrix_world @ dem.pose.bones[dn].matrix).translation + Vector((-0.032, 0, 0))
                else:
                    M.translation = (rig.matrix_world @ rig.pose.bones[n].matrix).translation
                pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.matrix = rig.matrix_world.inverted() @ M
                bpy.context.view_layer.update()
                pb.keyframe_insert('rotation_quaternion', frame=f - f0)
                if n == 'B_Pelvis': pb.keyframe_insert('location', frame=f - f0)
        na.use_frame_range = True; na.frame_start, na.frame_end = 0, nout
        print('DEMONCLIP', na.name, nout + 1, 'frames at 30 fps')
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
if 'Demon' in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects['Demon'], do_unlink=True)
# ---------------------------------------------------------------- Dead, signs, export
death = bpy.data.actions['Death']; rig.animation_data.action = death
if len(death.slots): rig.animation_data.action_slot = death.slots[0]
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
        if len(comps) != 4: continue
        keys = [comps[i].keyframe_points for i in range(4)]; prev = None
        for j in range(min(len(k) for k in keys)):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    keys[i][j].co[1] *= -1; keys[i][j].handle_left[1] *= -1; keys[i][j].handle_right[1] *= -1
                q = [-x for x in q]
            prev = q
        for fc in comps.values(): fc.update()
KEEP = ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')
for a in list(bpy.data.actions):
    if a.name not in KEEP and not (a.name.startswith('Demon_') and not a.name.startswith('Demon_src_')):
        bpy.data.actions.remove(a)
PREFIX = os.environ.get('CLIP_PREFIX', 'Carbine_')     # the carbine set on the shared body; the demon's own: Demon_*
for a in list(bpy.data.actions):
    if a.name in KEEP:
        a.name = PREFIX + a.name
st = bpy.data.actions[PREFIX + 'Standing']; rig.animation_data.action = st
if len(st.slots): rig.animation_data.action_slot = st.slots[0]
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', f'{OUTN}_lod0.glb')
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
info = {'glb': out, 'mode': MODE, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'tris_by_material': {m.name: sum(len(p.vertices) - 2 for p in body.data.polygons if p.material_index == i) for i, m in enumerate(body.data.materials)},
        'rest_height_m': float(co[:, 2].max() - co[:, 2].min()), 'bones': len(rig.data.bones),
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', f'export_info_{MODE}.json'), 'w'), indent=1)
print('EXPORTED', json.dumps(info))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'export', f'{OUTN}.blend'))
