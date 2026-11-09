"""The turret actors: the head and barrels of Landfall's wall turrets, built by the hard-surface builder
(level_generation/props/hesper_decorations/scripts/build_hard_surface.py, turret(heavy, part)) in the same place as in
the whole decoration, on a rigid armature, with their clips. The mount stays a decoration (hes_*_mount); the actor
stands at the same position and turns on the mount's gold ring.

Bones (every vertex 100 % on one): B_Root at the ring's top centre (the engine turns the whole actor to its facing),
B_Head (child, same pivot: the housing, neck, lenses, pennant or shoulders), B_Barrel (the barrels' pitch axis point;
the bastion's two barrels on one bone), Socket_Muzzle (bastion: Socket_Muzzle_L at +x, the turret's left, and
Socket_Muzzle_R) at the emitter tips, non-deforming children of B_Barrel. Front along -y, feet (the mount's bottom)
at z = 0, metres: the binding's scale is 100 like the decoration's height. Clips at 30 fps, all starting at 0:
Standing (6 s scan), Attack (0.5 s, the shot at frame 5 = 0.167 s), Hit (0.4 s), Death (1.2 s), Dead (held).
LODs are authored, not decimated: the builder's turret(heavy, part, lod) with fewer sides per level (TURRET_SIDES),
each level its own mesh <Mesh>_LOD1..3 on the same rig (a decimator turned the thin rings and bands into spikes).
Writes export/<name>_lod0.glb (LOD0, rig, clips), export/<name>_authored_lods.glb (LOD1..3 on the rig, no clips;
scripts/link_lods.py links them), export/<name>.blend and export/<name>_info.json.
Args: -- <hes_ward_turret_actor|hes_gate_bastion_actor>"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'props', 'hesper_decorations', 'scripts'))
import build_hard_surface as hs                                      # noqa: E402  (its builds run only as __main__)

NAME = sys.argv[sys.argv.index('--') + 1]
HEAVY = NAME == 'hes_gate_bastion_actor'
MESH = 'GateBastion' if HEAVY else 'WardTurret'
FPS = 30

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps, scene.render.fps_base = FPS, 1


def part(kind, lod):
    """Build one part of the turret at `lod` and join it into one object; returns it and the builder's pivots."""
    before = set(bpy.context.scene.objects)
    pivots = hs.turret(HEAVY, kind, lod)
    obj = hs.join([o for o in bpy.context.scene.objects if o not in before])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    group = obj.vertex_groups.new(name='B_Head' if kind == 'head' else 'B_Barrel')
    group.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
    return obj, pivots


bodies = []
for lod in range(4):
    head, pivots = part('head', lod)
    barrel, _ = part('barrel', lod)
    bodies.append(hs.join([head, barrel]))
    bodies[-1].name = bodies[-1].data.name = MESH + (f'_LOD{lod}' if lod else '')
body = bodies[0]
ring, pitch, tips = Vector(pivots['ring']), Vector(pivots['pitch']), [Vector(t) for t in pivots['tips']]

arm_data = bpy.data.armatures.new('Rig')
rig = bpy.data.objects.new('Rig', arm_data)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.context.selected_objects:
    o.select_set(False)
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
root = eb.new('B_Root'); root.head, root.tail = ring, ring + Vector((0, 0, 0.2))
bhead = eb.new('B_Head'); bhead.head, bhead.tail = ring, ring + Vector((0, 0, 0.3)); bhead.parent = root
bbar = eb.new('B_Barrel'); bbar.head, bbar.tail = pitch, pitch + Vector((0, -0.3, 0)); bbar.parent = bhead
sockets = ['Socket_Muzzle'] if not HEAVY else ['Socket_Muzzle_R', 'Socket_Muzzle_L']   # barrels at -x, +x
for name, tip in zip(sockets, tips):
    sock = eb.new(name); sock.head, sock.tail = tip, tip + Vector((0, -0.05, 0))
    sock.parent = bbar; sock.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
for obj in bodies:
    obj.parent = rig
    mod = obj.modifiers.new('Armature', 'ARMATURE'); mod.object = rig


def local_rotation(bone_name, axis, degrees):
    """A pose rotation of `degrees` about the armature-space `axis`, in the bone's rest frame."""
    rest = rig.data.bones[bone_name].matrix_local.to_3x3()
    local_axis = (rest.inverted() @ Vector(axis)).normalized()
    return Quaternion(local_axis, math.radians(degrees))


def yaw(deg):           # about up; + turns the front (-y) toward +x (the turret's left)
    return ('z', deg)


def key(action, frame, poses):
    """poses: {bone: (quaternion, location)} at frame; bones left out rest."""
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        q, loc = poses.get(pb.name, (Quaternion(), Vector()))
        pb.rotation_quaternion, pb.location = q, loc
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)


def pose(head_yaw=0.0, head_roll=0.0, barrel_up=0.0, recoil=0.0):
    """Head yaw about up, head roll about the front axis, barrel elevation (+ raises the muzzle: about +x by -deg),
    recoil = metres the barrel slides back (+y, the bone's local -Y)."""
    hq = local_rotation('B_Head', (0, 0, 1), head_yaw) @ local_rotation('B_Head', (0, 1, 0), head_roll)
    bq = local_rotation('B_Barrel', (1, 0, 0), -barrel_up)
    return {'B_Head': (hq, Vector()), 'B_Barrel': (bq, Vector((0, -recoil, 0)))}


def clip(name, keys):
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create()
    for frame, p in keys:
        key(action, frame, p)
    action.use_frame_range = True
    action.frame_start, action.frame_end = keys[0][0], keys[-1][0]
    return action


rig.animation_data_create()
scan = [(f, pose(head_yaw=25 * math.sin(2 * math.pi * f / 180), barrel_up=2 * math.sin(2 * math.pi * f / 90)))
        for f in range(0, 181, 10)]
clip('Standing', scan)
clip('Attack', [(0, pose()), (4, pose()), (5, pose(barrel_up=4, recoil=0.07)), (9, pose(barrel_up=2.5, recoil=0.035)),
                (15, pose())])
clip('Hit', [(0, pose()), (2, pose(head_yaw=4, head_roll=2, barrel_up=2)), (4, pose(head_yaw=-3, head_roll=-1.5)),
             (6, pose(head_yaw=2, head_roll=1, barrel_up=-1)), (8, pose(head_yaw=-1)), (12, pose())])
slump = dict(head_yaw=8, head_roll=5, barrel_up=-20)
clip('Death', [(0, pose()), (3, pose(head_yaw=3, barrel_up=3)), (24, pose(**slump)),
               (30, pose(head_yaw=8, head_roll=4.5, barrel_up=-17)), (36, pose(**slump))])
clip('Dead', [(0, pose(**slump)), (30, pose(**slump))])

for action in bpy.data.actions:                      # linear between keys: mechanical moves, no overshoot
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER' if action.name == 'Standing' else 'LINEAR'

standing = bpy.data.actions['Standing']
rig.animation_data.action = standing
if len(standing.slots):
    rig.animation_data.action_slot = standing.slots[0]
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', f'{NAME}_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in bpy.data.objects:
    o.select_set(o in bodies[1:] or o == rig)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'export', f'{NAME}_authored_lods.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_animations=False, export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False,
                          export_image_format='AUTO')
info = {'glb': out, 'mesh': MESH, 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons),
        'lod_tris': [sum(len(p.vertices) - 2 for p in obj.data.polygons) for obj in bodies],
        'ring': list(ring), 'pitch': list(pitch), 'tips': [list(t) for t in tips], 'sockets': sockets,
        'clips': {a.name: [int(x) for x in a.frame_range] for a in bpy.data.actions}}
json.dump(info, open(os.path.join(HERE, 'export', f'{NAME}_info.json'), 'w'), indent=1)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'export', f'{NAME}.blend'))
print('EXPORTED', json.dumps(info))
