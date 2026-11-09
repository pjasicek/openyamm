"""Upright posture for civilian clips (user review 2026-10-30 of both peasants: shoulders "slumped", "comical", "they
can't be dislocated nor slumped"). The Mixamo idles and walks carry their actor's slump: the clavicles drop 3-5 cm
below rest (Standard Idle, Standing Idle 03 Examine, Standard Walk), the chest leans forward and the neck juts.
Per frame of every listed clip (world frame: the character faces -Y, X is its left), in this order:
1. chest: the Pelvis -> Neck line may lean forward at most LEAN_TOL beyond its rest lean; the excess is taken out by
   rotating B_Spine1 and B_Spine2 (half each) about the lateral axis (the arms and head ride along);
2. neck: the Neck -> Head line likewise, NECK_TOL, on B_Neck; the head keeps its world orientation (gaze unchanged);
3. clavicles: the Clavicle -> UpperArm line stays within [rest - DROP_TOL, rest + RAISE_TOL] in elevation and within
   PROTRACT_TOL of rest in forward angle; the upper arm keeps its world orientation, so the hanging arm does not
   swing into the body.
DRY=1 only reports. Args: -- <in blend> <out blend> [clip ...]  (default Standing Walking Hit Fidget)"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
CLIPS = a[2:] or ['Standing', 'Walking', 'Hit', 'Fidget']
LEAN_TOL = math.radians(float(os.environ.get('LEAN_TOL', '3')))
NECK_TOL = math.radians(float(os.environ.get('NECK_TOL', '5')))
DROP_TOL = math.radians(float(os.environ.get('DROP_TOL', '3')))
RAISE_TOL = math.radians(float(os.environ.get('RAISE_TOL', '6')))
PROTRACT_TOL = math.radians(float(os.environ.get('PROTRACT_TOL', '8')))
DRY = bool(os.environ.get('DRY'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; W = rig.matrix_world
rig.animation_data_create()
X, Z = Vector((1, 0, 0)), Vector((0, 0, 1))


def head(name):
    return W @ rig.pose.bones[name].head


def lean(v):                                          # forward (-Y) tilt of a vector from vertical
    return math.atan2(-v.y, v.z)


def elev(v):
    return math.atan2(v.z, Vector((v.x, v.y)).length)


def protract(v):                                      # forward angle of a sideways vector
    return math.atan2(-v.y, abs(v.x))


def world(pb):
    return W @ pb.matrix


def set_world(pb, M):
    pb.matrix = W.inverted() @ M
    bpy.context.view_layer.update()


def rotate(pb, angle, axis, pivot):
    set_world(pb, Matrix.Translation(pivot) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-pivot) @ world(pb))


rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
REST = {'lean': lean(head('B_Neck') - head('B_Pelvis')), 'neck': lean(head('B_Head') - head('B_Neck'))}
for s in 'LR':
    v = head(f'B_{s}_UpperArm') - head(f'B_{s}_Clavicle')
    REST[s] = (elev(v), protract(v))
PB = rig.pose.bones
for name in CLIPS:
    act = bpy.data.actions.get(name)
    if act is None:
        continue
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    worst = {'lean': 0.0, 'neck': 0.0, 'drop': 0.0, 'raise': 0.0, 'prot': 0.0}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for pb in PB:
            pb.rotation_mode = 'QUATERNION'
        ex = lean(head('B_Neck') - head('B_Pelvis')) - REST['lean'] - LEAN_TOL
        if ex > 0:
            worst['lean'] = max(worst['lean'], ex)
            if not DRY:
                for b in ('B_Spine1', 'B_Spine2'):
                    rotate(PB[b], -ex / 2, X, head(b))     # +angle about +X tips the top forward (-Y)
        ex = lean(head('B_Head') - head('B_Neck')) - REST['neck'] - NECK_TOL
        if ex > 0:
            worst['neck'] = max(worst['neck'], ex)
            if not DRY:
                keep = world(PB['B_Head']).to_3x3()
                rotate(PB['B_Neck'], -ex, X, head('B_Neck'))
                M = keep.to_4x4(); M.translation = head('B_Head'); set_world(PB['B_Head'], M)
        for s in 'LR':
            cl, ua = PB[f'B_{s}_Clavicle'], PB[f'B_{s}_UpperArm']
            v = head(f'B_{s}_UpperArm') - head(f'B_{s}_Clavicle')
            e, p = elev(v), protract(v)
            de = min(0.0, e - (REST[s][0] - DROP_TOL)) or max(0.0, e - (REST[s][0] + RAISE_TOL))
            dp = max(0.0, abs(p - REST[s][1]) - PROTRACT_TOL) * (1 if p > REST[s][1] else -1)
            worst['drop'] = max(worst['drop'], -min(de, 0)); worst['raise'] = max(worst['raise'], max(de, 0))
            worst['prot'] = max(worst['prot'], abs(dp))
            if DRY or (de == 0 and dp == 0):
                continue
            keep = world(ua).to_3x3()
            if de:
                rotate(cl, de, Z.cross(v).normalized(), head(f'B_{s}_Clavicle'))   # +angle lowers the tip
            if dp:                                     # forward is -Y: undo by turning the tip back toward +Y
                rotate(cl, dp * (1 if s == 'L' else -1), Z, head(f'B_{s}_Clavicle'))
            M = keep.to_4x4(); M.translation = head(f'B_{s}_UpperArm'); set_world(ua, M)
        if not DRY:
            for b in ('B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle', 'B_L_UpperArm',
                      'B_R_UpperArm'):
                PB[b].keyframe_insert('rotation_quaternion', frame=f)
    print('POSTURE', name, 'max corrections deg:', {k: round(math.degrees(v), 1) for k, v in worst.items()},
          'dry' if DRY else 'applied')
if not DRY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
