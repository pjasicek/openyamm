"""Walking = the angel's flight (native wa..wh: 8 x 125 ms = 1.0 s; side view: body pitched ~45 deg forward, head up
looking ahead, legs trailing behind with bent knees, sword pointing forward, shield held before the chest, wings
beating). There is no foot contact, so the clip is authored over Standing frame 0 (the upright Mixamo idle):
- pelvis pitched forward PITCH deg about its head (+X turns the top toward -Y = forward), +-2 deg with the beat; a bob
  BOB m (the body rises on the downstroke, phase 0 = top of the upstroke) and a constant LIFT so the lowest vertex
  of the trailing legs clears the floor;
- spine arched back 2 x ARCH deg, neck and head raised so the face looks ahead;
- legs: hips extended HIP deg (trailing), knees flexed KNEE deg, ankles pointed ANKLE deg, a small alternating kick
  with the beat (left and right half a cycle apart);
- left arm (shield): the Attack's lead pose (shield arm bent before the body) copied in the chest frame;
- right arm: left as Standing here; author_carry.py then aims the sword forward (carry_flight.json).
The wing beat itself is keyed by wings_anim.py. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
PITCH, ARCH, NECK, HEAD = E('PITCH', 40), E('ARCH', 5), E('NECK', 14), E('HEAD', 14)
HIP, KNEE, ANKLE, KICK = E('HIP', 12), E('KNEE', 55), E('ANKLE', 35), E('KICK', 6)
BOB, FPS, N = E('BOB', 0.03), 30, 30
ADDUCT = E('ADDUCT', 0)                                  # m234: thighs brought together (deg) for a dangling hover
SHIELD_FRAME = int(E('SHIELD_FRAME', 9))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = FPS
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def snapshot(act, f):
    set_act(act); scene.frame_set(f)
    return {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}


stand = snapshot(bpy.data.actions['Standing'], 0)
lead = snapshot(bpy.data.actions['Attack'], SHIELD_FRAME) if not os.environ.get('NO_SHIELD') else None
set_act(None)
SHIELD_ARM = [] if os.environ.get('NO_SHIELD') else [n for n in names if n.startswith('B_L_') and any(k in n for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'))]


def rot_world(pb, deg, axis=(1, 0, 0)):
    """rotate a posed bone (and so its children) about the world axis through its head"""
    bpy.context.view_layer.update()
    M = rig.matrix_world @ pb.matrix
    h = M.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)


def pose(t):
    ph = 2 * math.pi * t
    for pb in rig.pose.bones:
        pb.matrix_basis = (lead if pb.name in SHIELD_ARM else stand)[pb.name].copy()
    pel = rig.pose.bones['B_Pelvis']
    pel.location = pel.location + Vector((0, 0, 0))
    rot_world(pel, PITCH + 2 * math.sin(ph))
    for n in ('B_Spine1', 'B_Spine2'):
        rot_world(rig.pose.bones[n], -ARCH)
    rot_world(rig.pose.bones['B_Neck'], -NECK); rot_world(rig.pose.bones['B_Head'], -HEAD)
    for s, sg in (('L', 1), ('R', -1)):
        k = KICK * math.sin(ph + (0 if s == 'L' else math.pi))
        rot_world(rig.pose.bones[f'B_{s}_Thigh'], HIP + k)
        if ADDUCT:
            rot_world(rig.pose.bones[f'B_{s}_Thigh'], ADDUCT * sg, (0, 1, 0))
        rot_world(rig.pose.bones[f'B_{s}_Calf'], KNEE + 1.5 * k)
        rot_world(rig.pose.bones[f'B_{s}_Foot'], ANKLE)
    bpy.context.view_layer.update()


# lowest vertex over the cycle -> constant lift (5 cm clearance), plus the bob
deps = bpy.context.evaluated_depsgraph_get()
lows = []
for i in range(N):
    pose(i / N)
    deps.update()
    ev = body.evaluated_get(deps); m = ev.to_mesh()
    lows.append(min((body.matrix_world @ v.co).z for v in m.vertices)); ev.to_mesh_clear()
LIFT = 0.05 - min(lows)
act = bpy.data.actions.new('Walking_flight'); act.use_fake_user = True
set_act(act)
for i in range(N + 1):
    t = (i % N) / N
    pose(t)
    pel = rig.pose.bones['B_Pelvis']
    # the bob is a world lift; the pelvis location is in its rest-local frame: convert through its rest matrix
    up = (rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, 0, LIFT + BOB * math.sin(2 * math.pi * t))))
    pel.location = pel.location + up
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=i)
        if pb.name == 'B_Pelvis':
            pb.keyframe_insert('location', frame=i)
set_act(None)
pose(0.0); bpy.context.view_layer.update()
H = lambda n: rig.matrix_world @ rig.pose.bones[n].head
def ang(a, b):
    d = (H(b) - H(a)).normalized(); return round(math.degrees(math.atan2(-d.y, d.z)), 1)   # + = toward forward (-Y)
print('FLIGHTANG trunk', ang('B_Pelvis', 'B_Neck'), 'head', ang('B_Neck', 'B_Head'), 'thigh L', ang('B_L_Thigh', 'B_L_Calf'),
      'shin L', ang('B_L_Calf', 'B_L_Foot'), '(deg from up toward forward; legs measured from up)')
set_act(None)
old = bpy.data.actions.get('Walking')
if old is not None:
    old.name = 'Walking_mixamo'
act.name = 'Walking'
print('FLIGHT frames', N + 1, 'lift cm', round(LIFT * 100, 1), 'lowest before lift cm', round(min(lows) * 100, 1),
      'pitch', PITCH, 'hip', HIP, 'knee', KNEE)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
