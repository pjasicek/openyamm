"""Assemble a Noble boss for export: the body with the covered skin removed and the textured shell joined into one
skinned mesh node `Noble`; the weapon joint `Weapon_R` (an exact copy of the Overseer's accepted CollarRod grip frame)
with `Socket_Tip` at the weapon's tip, palm sockets; the boss clips from the seven accepted Overseer clips with the
empty hand(s) relaxed (the Overseer's left hand held a pistol).

Usage (Blender): assemble.py <boss> --tip <metres from the grip to the tip> [--open-right]
Reads work/<boss>/shell_tex.blend and source/hes_kreegan_winged.glb (joint frames); writes work/<boss>/assembled.blend
and export/<boss>_lod0.glb."""
import bpy, sys, math, argparse
from pathlib import Path
from mathutils import Quaternion, Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('boss'); ap.add_argument('--tip', type=float, required=True)
ap.add_argument('--open-right', action='store_true')
ap.add_argument('--prefix', default='Noble')
ap.add_argument('--wing-spread', action='store_true')
ap.add_argument('--seated', action='store_true')
a = ap.parse_args(argv)
P = Path(__file__).resolve().parents[1]
W = P / 'work' / a.boss

# ---------------------------------------------------------------- the Overseer grip frames from the source
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'source/hes_kreegan_winged.glb'))
src = bpy.data.objects['Rig']
frames = {n: (src.data.bones[n].matrix_local.copy(), src.data.bones[n].length, src.data.bones[n].parent.name)
          for n in ('CollarRod', 'Socket_Rod')}
bpy.ops.wm.open_mainfile(filepath=str(W / 'shell_tex.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']
for n in ('Figure', 'Body'):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
body = bpy.data.objects[f'Body_{a.boss}']; shell = bpy.data.objects['Shell']
# the shell maps are files (transfer_tex.py, grade_gold.py): reload them so later grading reaches the export
import os
for img in bpy.data.images:
    path = bpy.path.abspath(img.filepath_raw or img.filepath)
    if path and os.path.exists(path) and '_shell_' in os.path.basename(path):
        img.source = 'FILE'; img.filepath = path; img.reload()
for o in (body, shell):
    o.hide_render = False; o.hide_viewport = False
# shell material: metallic 0 (runtime contract), keep the roughness map
sm = shell.data.materials[0]; bsdf = next(n for n in sm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
for l in list(bsdf.inputs['Metallic'].links):
    sm.node_tree.links.remove(l)
bsdf.inputs['Metallic'].default_value = 0.0
for l in list(bsdf.inputs['Emission Strength'].links) + list(bsdf.inputs['Emission Color'].links):
    sm.node_tree.links.remove(l)
bsdf.inputs['Emission Strength'].default_value = 0.0
# join body + shell into one mesh node
bpy.ops.object.select_all(action='DESELECT')
addons = [o for o in sc.objects if o.name.startswith('AddOn_')]
for o in [body, shell] + addons:
    o.hide_render = False; o.hide_viewport = False; o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
noble = bpy.context.view_layer.objects.active; noble.name = 'Noble'; noble.data.name = 'Noble'

# ---------------------------------------------------------------- joints: weapon frame, tip, palms
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for new, old in (('Weapon_R', 'CollarRod'), ('Socket_Tip', 'Socket_Rod')):
    M, length, parent = frames[old]
    b = eb.new(new); b.length = length; b.matrix = M
    b.parent = eb['Weapon_R'] if new == 'Socket_Tip' else eb[parent]
    b.use_deform = False
# the tip along the weapon axis (the grip frame's local +Z in glTF = the bone's own axis set by the importer)
w = eb['Weapon_R']; t = eb['Socket_Tip']
axis = (frames['Socket_Rod'][0].translation - frames['CollarRod'][0].translation).normalized()
t.translate(w.head + axis * a.tip - t.head)
for side in 'LR':
    hand = eb[f'B_{side}_Hand']
    tips = [eb[f'B_{side}_Finger{i}'].head for i in range(1, 6)]
    base = sum(tips, Vector()) / len(tips)
    palm = hand.head.lerp(base, 0.6)
    s = eb.new(f'Socket_Palm_{side}'); s.head = palm; s.tail = palm + (base - hand.head).normalized() * 0.05
    s.parent = hand; s.use_deform = False
if a.seated:
    t = eb.new('Throne'); t.head = Vector((0, 0, 0)); t.tail = Vector((0, 0.1, 0)); t.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- clips
roles = {'Flight': 'Flight', 'AttackMelee': 'AttackMelee', 'AttackRanged': 'AttackRanged', 'Cast': 'Cast',
         'Hit': 'Hit', 'Death': 'Death', 'Dead': 'Dead'}
relax = [f'B_L_Finger{i}{s}' for i in range(6) for s in ('', '1', '2')]
if a.open_right:
    relax += [f'B_R_Finger{i}{s}' for i in range(6) for s in ('', '1', '2')] + ['B_R_Finger0.001', 'B_R_Finger0.002']
for role, srcname in roles.items():
    sa = bpy.data.actions['Src_' + srcname]
    act = sa.copy(); act.name = f'{a.prefix}_{role}'; act.use_fake_user = True
    open_amount = 0.85 if role == 'AttackRanged' else 0.6
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in list(bag.fcurves):
                    name = fc.data_path.split('"')[1] if '"' in fc.data_path else ''
                    if name in relax and fc.data_path.endswith('rotation_quaternion'):
                        pass
                groups = {}
                for fc in bag.fcurves:
                    if '"' not in fc.data_path or not fc.data_path.endswith('rotation_quaternion'):
                        continue
                    name = fc.data_path.split('"')[1]
                    if name in relax:
                        groups.setdefault(name, {})[fc.array_index] = fc
                for name, chans in groups.items():
                    if len(chans) != 4:
                        continue
                    n = len(chans[0].keyframe_points)
                    for k in range(n):
                        q = Quaternion([chans[i].keyframe_points[k].co[1] for i in range(4)])
                        q = q.slerp(Quaternion(), open_amount)
                        for i in range(4):
                            chans[i].keyframe_points[k].co[1] = q[i]
                            chans[i].keyframe_points[k].handle_left[1] = q[i]
                            chans[i].keyframe_points[k].handle_right[1] = q[i]
for sa in [x for x in bpy.data.actions if x.name.startswith('Src_')]:
    bpy.data.actions.remove(sa)
sys.path.insert(0, str(P / 'scripts'))
import extra_clips
rig.animation_data_create()
if a.wing_spread:
    extra_clips.wing_spread(rig, sc, a.prefix)
if a.seated:
    extra_clips.seated(rig, sc, a.prefix)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'assembled.blend'))

# ---------------------------------------------------------------- export
for o in list(sc.objects):
    if o.type == 'MESH' and o != noble:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
noble.select_set(True); rig.select_set(True)
(P / 'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P / f'export/{a.boss}_lod0.glb'), export_format='GLB', use_selection=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_def_bones=False, export_yup=True,
                          export_image_format='AUTO', export_apply=False)
print('ASSEMBLED', a.boss, sum(len(p.vertices) - 2 for p in noble.data.polygons), 'tris',
      sorted(x.name for x in bpy.data.actions))
