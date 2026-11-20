"""Attack v2 for the Dire Wolf: the native leaping bite (m512 attack frames a-g). Crouch, rear up on the hind legs,
leap about 0.35 m clear of the floor, bite on the way down (impact 0.875 s, unchanged), land front first with the
rear high, recover. Same 1.125 s, rig and posing helpers as mm8_m512_claude/scripts/animate_wolf.py; front and hind
legs blend between planted IK and free FK on their own (free_front / free_hind).
Usage: blender -b -P attack_v2.py [-- render]   -> work/attack_v2.blend, work/attack_v2.glb (Attack only),
review/attack_v2/ side and front frames at the native frame times."""
import bpy
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parent / 'mm8_m512_claude'
sys.path.insert(0, str(HERE.parent / 'mm6_rat_claude/scripts'))
import posing as P  # noqa: E402
bpy.ops.wm.open_mainfile(filepath=str(SRC / 'work/anim_v1.blend'))
rig = bpy.data.objects['Wolf_Rig']; mesh = bpy.data.objects['Wolf']; sc = bpy.context.scene
FPS = 24; sc.render.fps = FPS
P.reset(rig)
REST = {b.name: b.matrix.copy() for b in rig.pose.bones}
FEET = {(kind, s): REST[f'{kind}Paw_{s}'].translation.copy() for kind in ['Front', 'Hind'] for s in 'LR'}
V = Vector
LEGS = {'Front': ['UpperArm', 'ForeArm', 'FrontPaw'], 'Hind': ['Thigh', 'Shin', 'HindPaw']}


def smooth(t):
    t = min(1, max(0, t)); return t * t * (3 - 2 * t)


def rot(name, axis, degrees):
    if abs(degrees) > 1e-7:
        P.rotate_world(rig, name, axis, degrees)


def body(pitch=0, spine=0, head=0, yaw=0, roll=0, offset=(0, 0, 0), jaw=0, tail=-10, phase=0):
    P.reset(rig)
    root = rig.pose.bones['Spine1']; root.matrix = Matrix.Translation(V(offset)) @ root.matrix
    bpy.context.view_layer.update()
    rot('Spine1', 'Y', roll); rot('Spine1', 'X', pitch)
    rot('Spine2', 'X', spine * .5); rot('Spine3', 'X', spine * .5)
    rot('Neck1', 'X', head * .4); rot('Head', 'X', head * .6)
    rot('Neck1', 'Z', yaw * .5); rot('Head', 'Z', yaw * .5); rot('Jaw', 'X', -jaw)
    for i in range(1, 7):
        rot(f'Tail{i}', 'X', tail if i == 1 else 0)
        rot(f'Tail{i}', 'Z', 3 * i / 6 * math.sin(2 * math.pi * phase - i * .4))


def leg(kind, side, target, pitch=0):
    upper, lower = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'Front' else (f'Thigh_{side}', f'Shin_{side}')
    pole = V(target) + V((.04 if side == 'L' else -.04, .3 if kind == 'Front' else -.3, .08))
    P.two_bone_ik(rig, upper, lower, target, pole)
    bone = rig.pose.bones[f'{kind}Paw_{side}']
    q = Quaternion(V((1, 0, 0)), math.radians(pitch)) @ REST[bone.name].to_quaternion()
    bone.matrix = Matrix.LocRotScale(bone.head.copy(), q, V((1, 1, 1)))
    bpy.context.view_layer.update()


def pose(p):
    body(**{k: p[k] for k in ['pitch', 'spine', 'head', 'yaw', 'roll', 'offset', 'jaw', 'tail'] if k in p})
    free = {'Front': p.get('free_front', 0), 'Hind': p.get('free_hind', 0)}
    fk = {}
    if free['Front'] > 0 or free['Hind'] > 0:
        # FK swing about world X at each joint (positive = paw toward the tail), then a paw flex
        for side in 'LR':
            for bone, key in [('UpperArm', 'front'), ('ForeArm', 'elbow'), ('FrontPaw', 'fpaw'),
                              ('Thigh', 'hind'), ('Shin', 'knee'), ('HindPaw', 'hpaw')]:
                rot(f'{bone}_{side}', 'X', p.get(key, 0))
        fk = {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}
    for (kind, side), base in FEET.items():
        if free[kind] >= 1:
            continue
        off = p.get('front_offset' if kind == 'Front' else 'hind_offset', (0, 0, 0))
        leg(kind, side, base + V(off), p.get('paw', 0) if kind == 'Front' else 0)
    for kind, w in free.items():
        if 0 < w < 1:
            for side in 'LR':
                for bone in LEGS[kind]:
                    b = rig.pose.bones[f'{bone}_{side}']; q, loc = fk[b.name]
                    b.rotation_quaternion = b.rotation_quaternion.slerp(q, w); b.location = b.location.lerp(loc, w)
            bpy.context.view_layer.update()


READY = {'pitch': 9, 'spine': 4, 'head': -12, 'tail': -8, 'front_offset': (0, -.035, 0)}
# Forward is -Y, up +Z; pitch > 0 lowers the nose, tail > 0 raises the tail. Times follow the seven native frames
# (a 0, b .16, c .32, d .48, e .64, f .80, g .96 s); the bite closes at the 0.875 s impact.
ATTACK = [
    (0, READY),
    # b: load up, chest and head low
    (.16, {'pitch': 8, 'spine': 6, 'head': 6, 'offset': (0, .04, -.035), 'front_offset': (0, -.07, 0),
           'paw': 10, 'jaw': 8, 'tail': -18}),
    # c: rising, front paws leave the floor, jaws opening
    (.32, {'pitch': -3, 'spine': -2, 'head': -14, 'offset': (0, -.02, -.01), 'front_offset': (0, -.06, 0),
           'jaw': 16, 'tail': -12}),
    # d: reared up on the hind legs, forelegs reaching up and forward
    (.48, {'pitch': -30, 'spine': -8, 'head': 14, 'offset': (0, -.04, -.01), 'hind_offset': (0, .02, 0),
           'free_front': 1, 'front': -40, 'elbow': 30, 'fpaw': -20, 'jaw': 22, 'tail': -16}),
    # e: airborne, stretched level, forelegs reaching, hind legs trailing
    (.64, {'pitch': -4, 'spine': -6, 'head': -2, 'offset': (0, -.14, .25),
           'free_front': 1, 'front': -58, 'elbow': 10, 'fpaw': -25,
           'free_hind': 1, 'hind': 55, 'knee': 5, 'hpaw': 20, 'jaw': 26, 'tail': -4}),
    # f: coming down, head driving down into the bite, jaws wide
    (.80, {'pitch': 6, 'spine': 2, 'head': 14, 'offset': (0, -.13, .27),
           'free_front': 1, 'front': -50, 'elbow': 25, 'fpaw': -10,
           'free_hind': 1, 'hind': 10, 'knee': 30, 'hpaw': 10, 'jaw': 30, 'tail': 2}),
    # impact: jaws snap shut, still in the air
    (.875, {'pitch': 10, 'spine': 4, 'head': 18, 'offset': (0, -.12, .21),
            'free_front': 1, 'front': -25, 'elbow': 10, 'fpaw': 0,
            'free_hind': 1, 'hind': 0, 'knee': 35, 'hpaw': 5, 'jaw': 3, 'tail': 10}),
    # g: forelegs land first, rear and tail high
    (.96, {'pitch': 14, 'spine': 6, 'head': 4, 'offset': (0, -.10, .10), 'front_offset': (0, -.10, 0),
           'free_hind': .7, 'hind': -10, 'knee': 30, 'hpaw': 10, 'hind_offset': (0, -.06, .05), 'jaw': 6,
           'tail': 28}),
    (1.125, READY)]


def keys(frames, t):
    for (t0, a), (t1, b) in zip(frames[:-1], frames[1:]):
        if t <= t1:
            u = smooth((t - t0) / (t1 - t0)); out = {}
            for k in a.keys() | b.keys():
                av, bv = a.get(k, 0), b.get(k, 0)
                if isinstance(av, tuple) or isinstance(bv, tuple):
                    av = V(av if isinstance(av, tuple) else (0, 0, 0)); bv = V(bv if isinstance(bv, tuple) else (0, 0, 0))
                    out[k] = tuple(av.lerp(bv, u))
                else:
                    out[k] = av + (bv - av) * u
            return out
    return frames[-1][1]


def coordinates():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.array([v.co[:] for v in me.vertices]); ev.to_mesh_clear(); return co


seconds = 1.125; n = round(seconds * FPS); poses = []; mins = []; paws = []
rig.animation_data.action = None
for f in range(n + 1):
    pose(keys(ATTACK, f / FPS))
    co = coordinates(); assert np.isfinite(co).all()
    lift = max(0., -.003 - float(co[:, 2].min()))  # same floor rule as the production clips
    if lift:
        root = rig.pose.bones['Spine1']; root.matrix = Matrix.Translation(V((0, 0, lift))) @ root.matrix
        bpy.context.view_layer.update()
    mins.append(float(coordinates()[:, 2].min()))
    paws.append([round((rig.matrix_world @ rig.pose.bones[f'{k}Paw_{s}'].tail).z, 3) for k in ['Front', 'Hind'] for s in 'LR'])
    poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
old = bpy.data.actions['Attack']; old.name = 'Attack_v1'
act = bpy.data.actions.new('Attack'); act.use_fake_user = True
rig.animation_data.action = act; prev = {}
for f, pose_data in enumerate(poses):
    for b in rig.pose.bones:
        q, loc = pose_data[b.name]
        if b.name in prev and prev[b.name].dot(q) < 0:
            q = -q
        prev[b.name] = q; b.rotation_quaternion = q; b.location = loc; b.scale = (1, 1, 1)
        for channel in ['rotation_quaternion', 'location', 'scale']:
            b.keyframe_insert(channel, frame=f + 1)
report = {'duration': seconds, 'frames': n, 'minimum_z': min(mins), 'clearance_by_frame': [round(m, 4) for m in mins],
          'paw_tips_FL_FR_HL_HR': paws}
print('ATTACK', json.dumps({k: v for k, v in report.items() if k != 'clearance_by_frame'}), 'max clearance',
      round(max(mins), 3), 'at', mins.index(max(mins)) / FPS, flush=True)
assert min(mins) > -.015
(HERE / 'work').mkdir(exist_ok=True)
(HERE / 'work/attack_v2_report.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'work/attack_v2.blend'))

# Attack-only GLB with the production export settings, for grafting into the staged runtime GLB
for a in list(bpy.data.actions):
    if a.name != 'Attack':
        bpy.data.actions.remove(a)
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); mesh.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(HERE / 'work/attack_v2.glb'), use_selection=True,
    export_format='GLB', export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
    export_skins=True, export_all_influences=False, export_morph=False, export_reset_pose_bones=True,
    export_anim_slide_to_zero=True, export_image_format='NONE')

if 'render' in sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else False:
    bpy.ops.wm.open_mainfile(filepath=str(HERE / 'work/attack_v2.blend'))
    rig = bpy.data.objects['Wolf_Rig']; sc = bpy.context.scene
    out = HERE / 'review/attack_v2'; out.mkdir(parents=True, exist_ok=True)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
    sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.7, .7, .7)
    sc.world = bpy.data.worlds.new('ReviewWorld'); sc.world.color = (.12, .12, .12)
    sc.render.resolution_x = 300; sc.render.resolution_y = 300; sc.render.resolution_percentage = 100
    cam = bpy.data.objects.new('ReviewCamera', bpy.data.cameras.new('ReviewCamera'))
    sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.6
    floor = bpy.data.objects.new('Floor', bpy.data.meshes.new('Floor'))
    floor.data.from_pydata([(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)], [], [(0, 1, 2, 3)])
    sc.collection.objects.link(floor)
    times = [0, .16, .32, .48, .64, .80, .875, .96, 1.125]
    for name in ['Attack_v1', 'Attack']:
        rig.animation_data.action = bpy.data.actions[name]
        for view, direction in [('side', (1, 0, .12)), ('front', (-.3, -1, .15))]:
            center = Vector((0, -.05, .55)); cam.location = center + Vector(direction) * 4
            cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
            for i, t in enumerate(times):
                frame = t * 24 + 1; sc.frame_set(int(frame), subframe=frame % 1)
                sc.render.filepath = str(out / f'{name}_{view}_{i}.png'); bpy.ops.render.render(write_still=True)
    (out / 'times.json').write_text(json.dumps(times))
