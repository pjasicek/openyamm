"""Source-informed Couatl motion: travelling ground wave, controlled feather wings and a hinged jaw.
Full run: work/rig_v3.blend -> work/anim_v3.blend with every clip and pilot renders. Rebake of selected clips into the
production master (old actions replaced, other clips untouched): COUATL_BASE=work/uv_master_v2.blend
COUATL_OUT=work/uv_master_v3.blend COUATL_CLIPS=Attack."""
import json
import math
import os
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

P = Path(__file__).resolve().parents[1]
BASE = os.environ.get('COUATL_BASE', 'work/rig_v3.blend')
OUT = os.environ.get('COUATL_OUT', 'work/anim_v3.blend')
ONLY = set(os.environ['COUATL_CLIPS'].split(',')) if os.environ.get('COUATL_CLIPS') else None
bpy.ops.wm.open_mainfile(filepath=str(P / BASE))
D = json.loads((P / 'work/rig.json').read_text())
J = np.array(D['joints'])
R = np.array(D['radius'])
K = D['root']
NAMES = D['names']
L = np.linalg.norm(np.diff(J, axis=0), axis=1)
rig = bpy.data.objects['Couatl_Rig']
mesh = bpy.data.objects['Couatl']
scene = bpy.context.scene
scene.render.fps = FPS = 24
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
neck = list(range(K, len(NAMES)))
tail = list(range(K - 1, -1, -1))
rig.animation_data_create()

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)

def envelope(t, start, peak, hold, end):
    return smooth((t-start)/(peak-start)) * (1-smooth((t-hold)/(end-hold)))

def frames(points):
    result = {}
    old_t = old_n = None
    for i in neck:
        tangent = Vector(points[i+1] - points[i]).normalized()
        normal = Vector((1, 0, 0)) if old_t is None else old_t.rotation_difference(tangent) @ old_n
        normal = (normal - tangent*normal.dot(tangent)).normalized()
        result[i] = Matrix((tangent, normal, tangent.cross(normal))).transposed()
        old_t, old_n = tangent, normal
    for i in tail:
        tangent = Vector(points[i] - points[i+1]).normalized()
        normal = Vector((0, 0, 1)).cross(tangent).normalized()
        result[i] = Matrix((tangent, normal, tangent.cross(normal))).transposed()
    return result

rest_frames = frames(J)

def parameters(role, t):
    p = dict(pitch=0., yaw=0., head_pitch=0., jaw=0., flap=0., fan=0., wave=0.035,
             phase=t/2, tail_lift=0., collapse=0., roll=0., rear=0., strike=0.)
    if role in ('Standing', 'Walk', 'Run'):
        period = {'Standing':2., 'Walk':.875, 'Run':.625}[role]
        phase = 2*math.pi*t/period
        moving = role != 'Standing'
        p.update(phase=t/period, wave=.32 if moving else .035,
                 yaw=.04*math.sin(phase), pitch=.08 if moving else .015*math.sin(phase),
                 head_pitch=-.06 if moving else 0,
                 flap=(.16 if moving else .035)*math.sin(phase),
                 fan=(.09 if moving else .02)*math.sin(phase-.5))
    elif role == 'Attack':
        # Native m408aa-ah: rear up high on the lifted fore-body with the jaws gaping, strike forward and down to the
        # ground in front (impact at 0.9 s), recover to the held pose. The body arc (ARC_*) replaces the neck pitch.
        rear = envelope(t, 0., .38, .6, .9)
        strike = envelope(t, .6, .9, .93, 1.2)
        p.update(rear=rear, strike=strike, jaw=.75*rear+.3*strike, flap=-.3*rear+.2*strike, fan=-.1*rear,
                 tail_lift=.07*rear)
    elif role == 'Cast':
        rear = envelope(t, 0., .35, .65, .9)
        strike = envelope(t, .65, .9, .96, 1.25)
        p.update(pitch=-.2*rear+.12*strike, head_pitch=-.45*rear, jaw=.62*rear+.35*strike, flap=-.28*rear,
                 fan=-.08*rear, tail_lift=.07*rear, yaw=.045*math.sin(t*8))
    elif role == 'Hit':
        recoil = envelope(t, 0, .125, .25, .75)
        p.update(pitch=-.35*recoil, yaw=.22*recoil, head_pitch=-.2*recoil,
                 jaw=.2*recoil, flap=.1*recoil, tail_lift=.1*recoil)
    elif role == 'Fidget':
        p['tail_lift'] = .28*envelope(t, 0, .3, .8, 1.125)*(1+.12*math.sin(t*28))
        p['flap'] = .03*math.sin(t*math.tau/1.125)
    elif role in ('Death', 'Dead'):
        t = .875 if role == 'Dead' else t
        recoil = envelope(t, 0, .25, .42, .65)
        p.update(pitch=-.4*recoil, jaw=.65*recoil, flap=-.25*recoil,
                 tail_lift=.16*recoil, collapse=smooth((t-.4)/.4),
                 roll=0., phase=t/2)
    elif role == 'Stress':
        p.update(pitch=.5*math.sin(t*math.tau), yaw=.4*math.sin(t*math.tau),
                 jaw=.7*smooth(t/.3), flap=.55*math.sin(t*math.tau), fan=.18*math.sin(t*math.tau))
    return p

# Attack body arc: absolute elevation (degrees above the forward horizontal, past 90 leaning back) of every segment
# from the ground anchor point ARC_ANCHOR (Tail_06) to the head tip, at the full rear and at the full strike.
ARC_ANCHOR = 14
ARC_REAR = [5, 15, 32, 50, 65, 75, 82, 87, 90, 92, 95, 98, 95, 60]
ARC_STRIKE = [3, 8, 18, 30, 45, 55, 55, 50, 35, 10, -15, -45, -70, -60]

def arc(points, p):
    """Lift the fore-body and neck from the anchor: each segment turns about X from its held direction towards the
    rear/strike elevation; the tail behind the anchor stays on the ground, so the neck base moves back as it rises."""
    held = points.copy()
    for k, i in enumerate(range(ARC_ANCHOR, len(points)-1)):
        v = Vector(held[i+1]-held[i])
        elevation = math.degrees(math.atan2(v.z, -v.y))
        delta = p['rear']*(ARC_REAR[k]-elevation) + p['strike']*(ARC_STRIKE[k]-elevation)
        v = Matrix.Rotation(-math.radians(delta), 3, 'X') @ v
        target = points[i] + np.array(v)
        if target[2] < R[i+1]:
            dz = np.clip(R[i+1]-points[i, 2], -L[i]*.99, L[i]*.99)
            horizontal = np.array([v.x, v.y, 0.])
            horizontal /= max(1e-8, np.linalg.norm(horizontal))
            target = points[i] + horizontal*math.sqrt(L[i]**2-dz**2) + [0, 0, dz]
        points[i+1] = target

def pose(role, t):
    p = parameters(role, t)
    points = J.copy()
    for k, i in enumerate(neck):
        fraction = (k+1)/len(neck)
        tangent = Vector(J[i+1]-J[i]).normalized()
        if k < 2:
            tangent = Vector((0,-1,0)).lerp(tangent, (k+1)/3).normalized()
        pitch = p['pitch']*fraction + (p['head_pitch'] if i == len(NAMES)-1 else 0)
        tangent = Matrix.Rotation(p['yaw']*fraction, 3, 'Z') @ Matrix.Rotation(pitch, 3, 'X') @ tangent
        if p['collapse']:
            flat = Vector((.1*math.sin(k*.7), -1, -.18)).normalized()
            tangent = tangent.lerp(flat, p['collapse']).normalized()
        target = points[i] + np.array(tangent)*L[i]
        floor = min(R[i+1], .06) if p['collapse'] else R[i+1]
        if target[2] < floor:
            dz = np.clip(floor-points[i, 2], -L[i]*.99, L[i]*.99)
            horizontal = np.array([tangent.x, tangent.y, 0.])
            horizontal /= max(1e-8, np.linalg.norm(horizontal))
            target = points[i] + horizontal*math.sqrt(L[i]**2-dz**2) + [0, 0, dz]
        points[i+1] = target
    distance = 0.
    total = sum(L[:K])
    for i in tail:
        distance += L[i]
        v = distance/total
        heading = p['wave']*math.sin(math.tau*(v*1.35-p['phase']))*smooth(v/.2)
        height = R[i]+p['tail_lift']*smooth((v-.62)/.38)
        dz = float(np.clip(height-points[i+1,2], -.8*L[i], .8*L[i]))
        horizontal = math.sqrt(L[i]**2-dz**2)
        points[i] = points[i+1] + [math.sin(heading)*horizontal, math.cos(heading)*horizontal, dz]
    if p['rear'] or p['strike']:
        arc(points, p)
    fitted = frames(points)
    matrices = {}
    for i, name in enumerate(NAMES):
        rotate = fitted[i] @ rest_frames[i].transposed()
        if name == 'Head' and p['roll']:
            rotate = Matrix.Rotation(p['roll'], 3, 'Y') @ rotate
        m = (rotate @ rest[name].to_3x3()).to_4x4()
        m.translation = Vector(points[i+1] if i<K else points[i])
        matrices[name] = m
    for side, sign in [('L', 1), ('R', -1)]:
        for name, angle in [('WingRoot', p['flap']), ('WingMid', p['fan']),
                            ('WingFan', p['fan']*.5)]:
            key = f'{name}_{side}'
            parent = rig.data.bones[key].parent.name
            delta = matrices[parent] @ rest[parent].inverted()
            pivot = rest[key].translation
            local = Matrix.Translation(pivot) @ Matrix.Rotation(sign*angle, 4, 'Y') @ Matrix.Translation(-pivot)
            matrices[key] = delta @ local @ rest[key]
    pivot = rest['Crest'].translation
    matrices['Crest'] = (matrices['Head'] @ rest['Head'].inverted() @ Matrix.Translation(pivot)
                         @ Matrix.Rotation(-1.35*p['collapse'], 4, 'X') @ Matrix.Translation(-pivot) @ rest['Crest'])
    pivot = rest['Jaw'].translation
    matrices['Jaw'] = (matrices['Head'] @ rest['Head'].inverted() @ Matrix.Translation(pivot)
                       @ Matrix.Rotation(p['jaw'], 4, 'X') @ Matrix.Translation(-pivot) @ rest['Jaw'])
    # bones added after the motion pass (MouthSocket) stay rigid to their parent and carry no keys
    posed = [bone for bone in rig.pose.bones if bone.name in matrices]
    for bone in posed:
        basis = rest[bone.name].inverted() @ matrices[bone.name]
        if bone.parent:
            parent = bone.parent.name
            basis = ((rest[parent].inverted() @ rest[bone.name]).inverted()
                     @ matrices[parent].inverted() @ matrices[bone.name])
        bone.matrix_basis = basis
    bpy.context.view_layer.update()
    # Fit the complete body surface to the ground; report the correction instead of hiding it.
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    coords = np.array([tuple(v.co) for v in evaluated.data.vertices])
    correction = max(0., -float(coords[:, 2].min()))
    if correction:
        bone = rig.pose.bones['Root']
        m = matrices['Root'].copy()
        m.translation.z += correction
        bone.matrix_basis = rest['Root'].inverted() @ m
        bpy.context.view_layer.update()
    return correction, posed

CLIPS = {'Standing':(2., True), 'Walk':(.875, True), 'Run':(.625, True),
         'Attack':(1.25, False), 'Cast':(1.25, False), 'Hit':(.75, False),
         'Fidget':(1.125, False), 'Death':(.875, False), 'Dead':(1., False), 'Stress':(1., False)}
report = {}
for name, (seconds, loop) in CLIPS.items():
    if ONLY is not None and name not in ONLY:
        continue
    rig.animation_data.action = None
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    corrections = []
    prior = {}
    for frame in range(round(seconds*FPS)+1):
        rig.animation_data.action = None
        scene.frame_set(frame)
        for bone in rig.pose.bones:
            bone.matrix_basis.identity()
        correction, posed = pose(name, (frame/FPS)%seconds if loop else frame/FPS)
        corrections.append(correction)
        samples = {b.name:(b.location.copy(), b.rotation_quaternion.copy()) for b in posed}
        rig.animation_data.action = action
        for bone in posed:
            position, rotation = samples[bone.name]
            if bone.name in prior and rotation.dot(prior[bone.name])<0:
                rotation.negate()
            prior[bone.name] = rotation.copy()
            bone.location, bone.rotation_quaternion = position, rotation
            bone.keyframe_insert('location', frame=frame)
            bone.keyframe_insert('rotation_quaternion', frame=frame)
        assert all(np.isfinite(tuple(b.location)).all() for b in rig.pose.bones)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = "LINEAR"
    report[name] = dict(seconds=seconds, frames=round(seconds*FPS), loop=loop,
                        max_ground_correction=max(corrections))
    print('CLIP', name, report[name])
if ONLY is not None:
    report = {**json.loads((P/'work/clip_manifest.json').read_text()), **report}
(P/'work/clip_manifest.json').write_text(json.dumps(report, indent=2)+'\n')
rig.animation_data.action = bpy.data.actions['Standing']
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/OUT))
if ONLY is None:
    # Pilot review includes the curve, wing and jaw extremes before material production.
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.show_cavity = True
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (.55,.65,.72)
    scene.world = bpy.data.worlds.new('ReviewWorld')
    scene.world.color = (.07,.07,.07)
    scene.render.resolution_x = scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0,0,-0.012))
    plane = bpy.context.object
    plane.color = (.18,.18,.18,1)
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 3.0
    for name, time in [('Standing',0),('Walk',.21),('Attack',.38),('Attack',.9),('Death',.875),('Stress',.25)]:
        rig.animation_data.action = bpy.data.actions[name]
        scene.frame_set(int(time*FPS), subframe=time*FPS-int(time*FPS))
        for view, direction in [('quarter',(1,-1.7,.7)),('side',(1,0,.05))]:
            center = Vector((0,.6,.45))
            cam.location = center+Vector(direction).normalized()*6
            cam.rotation_euler = (center-cam.location).to_track_quat('-Z','Y').to_euler()
            scene.render.filepath = str(P/f'review/pilot_{name}_{time:.3f}_{view}.png')
            bpy.ops.render.render(write_still=True)
