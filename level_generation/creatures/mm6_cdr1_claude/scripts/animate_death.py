"""Burning death (engine burn, actors.yml death_effect: burn): rewrite only the Death and Dead actions of the packed
master, keeping every other clip, the mesh, UVs and weights.

As the native dragon: a roaring recoil, a short airborne thrash (fast irregular wing beats, lashing tail, jerking bank
and yaw), then the burning body collapses flat to the ground, wings spread, head and tail down, so the fire shape sinks
into a strip of flame. The lift is one smooth envelope over every frame's floor clearance (running maximum, then moving
average) instead of per-frame anchoring, which would bounce the body on every wing downstroke. Dead holds the last
Death pose and lift. Usage (Blender): animate_death.py [--render DIR] renders side/front key poses instead of saving.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector, Quaternion

P = Path(__file__).resolve().parents[1]
DEATH_FRAMES = 58   # 2.4 s at 24 fps
bpy.ops.wm.open_mainfile(filepath=str(P / 'export/mm6_cdr1.blend'))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
scene = bpy.context.scene
scene.render.fps = 24
axes = {name: bone.matrix_local.to_3x3().inverted() for name, bone in rig.data.bones.items()}
# The active action would override the posed bones.
rig.animation_data.action = None


def ss(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rot(name, axis, angle):
    rig.pose.bones[name].rotation_quaternion @= Quaternion(axes[name] @ Vector(axis), angle)


def lowest():
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    low = min(v.co.z for v in mesh.vertices)
    evaluated.to_mesh_clear()
    return low


def hover(need, window=8):
    peak = [max(need[max(0, i - window):i + window + 1]) for i in range(len(need))]
    return [sum(peak[max(0, i - window):i + window + 1]) / len(peak[max(0, i - window):i + window + 1])
            for i in range(len(peak))]


def pose(t, lift):
    """The death at t seconds; base values match animate_dragon.py's hover (pitch -0.22, neck 0.09, flap 0.35)."""
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis.identity()
    tau = math.tau
    recoil = ss(t / .15) * (1 - ss((t - .5) / .4))
    thrash = ss((t - .15) / .2) * (1 - ss((t - 1.05) / .45))
    fall = ss((t - .9) / 1.1)
    beat = tau * 2.8 * t
    flap = (1 - fall) * (.35 + thrash * (.45 * math.sin(beat) + .10 * math.sin(1.7 * beat + 1)) - .25 * recoil) \
        + fall * .55
    fold = .30 * recoil * (1 - fall) + .08 * thrash * math.sin(beat - .6) + .12 * fall
    pitch = -.22 - .26 * recoil + .06 * thrash * math.sin(tau * 1.9 * t) + .55 * fall
    neck = .09 - .28 * recoil + .12 * thrash * math.sin(tau * 1.5 * t + 1) + .35 * fall
    bank = .14 * thrash * math.sin(tau * 1.3 * t + .5) + .10 * fall
    yaw = .16 * thrash * math.sin(tau * .9 * t)
    jaw = .5 * max(recoil, .6 * thrash * (.5 + .5 * math.sin(tau * 2.2 * t))) + .2 * fall
    tail_amp = 1 + 5 * thrash
    curl = .25 * fall
    rot('Root', (1, 0, 0), pitch)
    rot('Root', (0, 1, 0), bank)
    rig.pose.bones['Root'].location = axes['Root'] @ Vector((0, 0, lift))
    for i in range(1, 4):
        rot(f'Neck{i}', (1, 0, 0), neck / 3)
        rot(f'Neck{i}', (0, 0, 1), yaw / 3)
    rot('Head', (1, 0, 0), -neck * .2)
    rot('Jaw', (1, 0, 0), jaw)
    phase = tau * 1.8 * t
    for i in range(1, 10):
        rot(f'Tail{i}', (0, 0, 1), (.012 + .004 * i) * tail_amp * math.sin(phase - i * .4) + curl * .4)
        rot(f'Tail{i}', (1, 0, 0), .014 * tail_amp * math.sin(phase - i * .4) - .05 * fall)
    for side, sign in [('L', 1), ('R', -1)]:
        rot(side + 'Wing0', (0, 1, 0), sign * flap)
        rot(side + 'Wing1', (0, 1, 0), sign * (.09 * (1 + 2 * thrash) * math.sin(beat - .5)))
        rot(side + 'Wing2', (0, 1, 0), sign * (.06 * (1 + 2 * thrash) * math.sin(beat - .8)))
        rot(side + 'Wing1', (0, 0, 1), sign * fold)
        for limb in ['Fore', 'Hind']:
            rot(side + limb + 'Upper', (1, 0, 0), .035 * math.sin(phase - .7) - .45 * fall)
            rot(side + limb + 'Lower', (1, 0, 0), .05 * math.sin(phase - 1.1) + .35 * fall)
    bpy.context.view_layer.update()


need = []
for frame in range(DEATH_FRAMES + 1):
    pose(frame / 24, 0.0)
    need.append(-lowest())
lifts = hover(need)

if '--render' in sys.argv:
    out = Path(sys.argv[sys.argv.index('--render') + 1])
    out.mkdir(parents=True, exist_ok=True)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x, scene.render.resolution_y = 480, 360
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 4.4
    for frame in range(0, DEATH_FRAMES + 1, 6):
        pose(frame / 24, lifts[frame])
        for view, location in [('side', (6, -0.3, 0.9)), ('front', (0, -6, 0.9))]:
            camera.location = location
            camera.rotation_euler = (Vector((0, -0.3, 0.9)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(out / f'{view}_{frame:02d}.png')
            bpy.ops.render.render(write_still=True)
    raise SystemExit

report = {}
for name, frames in [('Death', DEATH_FRAMES), ('Dead', 24)]:
    old = bpy.data.actions.get(name)
    if old is not None:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data.action = action
    minimum = []
    for frame in range(frames + 1):
        index = frame if name == 'Death' else DEATH_FRAMES
        pose(index / 24, lifts[index])
        for bone in rig.pose.bones:
            bone.keyframe_insert('location', frame=frame)
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            bone.keyframe_insert('scale', frame=frame)
        minimum.append(lowest())
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    assert min(minimum) > -0.001, (name, min(minimum))
    report[name] = {'frames': frames, 'duration': frames / 24, 'min_z': min(minimum)}
rig.animation_data.action = bpy.data.actions['Standing']
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'export/mm6_cdr1.blend'))
for ob in bpy.data.objects:
    ob.select_set(ob.name in ('Body', 'Rig'))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(P / 'work/death_clips.glb'), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
    export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
    export_morph=False, export_image_format='NONE', export_reset_pose_bones=True, export_anim_slide_to_zero=True)
(P / 'review/burn/death_clips.json').write_text(json.dumps(report, indent=2) + '\n')
print('DEATH', json.dumps(report))
