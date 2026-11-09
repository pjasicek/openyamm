"""Prop carry (batch B: the Mage's upright staff in the LEFT hand; originally natm's spear carry) for locomotion/idle clips (the source arms swing or hang; the native carries the spear low, level and
pointing forward). Per frame of each listed action: the right wrist target is a fixed point in the chest (B_Spine2)
frame plus a share of the clip's own wrist motion relative to the chest (keeps the idle's breathing / the walk's
small pump alive); the spear direction is fixed in the PELVIS frame (forward, slightly out and down) blended with a
share of the clip's own hand motion; the hand roll is chosen by least wrist strain with continuity (armik.py).
Writes the action in place. Args: -- <in blend> <out blend> <Action>[:keep] ...   (keep = share of own wrist motion)"""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, common
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
import cfg
_SUF = '' if cfg.C['carry'].get('side', 'R') == 'R' else '_' + cfg.C['carry']['side']
G = json.load(open(os.path.join(common.WORK, f'grip_pose{_SUF}.json')))   # m322: grip_pose_L.json
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
import cfg
CARRY = cfg.C['carry']
SIDE = CARRY.get('side', 'R')
# carry pose (world, at the Standing rest stance; character faces -Y, right = -X): wrist beside and ahead of the right
# hip, forearm angled forward; spear forward, 10 deg out, 8 deg down
WRIST = Vector(CARRY.get('wrist', (-0.27, -0.16, 0.86)))
SG = 1 if SIDE == 'L' else -1                                   # outward = +X for the left hand
def prop_dir(yaw_out, pitch):
    ya, pi_ = math.radians(yaw_out), math.radians(pitch)
    return Vector((SG * math.sin(ya) * math.cos(pi_), -math.cos(ya) * math.cos(pi_), math.sin(pi_)))


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


WORLD = os.environ.get('CARRY_FRAME', 'pelvis') == 'world'   # m322: the female walk's pelvis turns 69 deg about its own axis
ARM = [f'B_{SIDE}_Clavicle', f'B_{SIDE}_UpperArm', f'B_{SIDE}_Forearm', f'B_{SIDE}_Hand']
for item in items:
    parts = item.split(':'); name = parts[0]; keep = float(parts[1]) if len(parts) > 1 else 0.3
    ov = dict(x.split('=') for x in parts[2:])                     # per-clip overrides: yaw=<deg out> pitch=<deg>
    SPEAR = prop_dir(float(ov.get('yaw', CARRY.get('yaw_out', 10))), float(ov.get('pitch', CARRY.get('pitch', -8))))
    wr_ov = Vector([float(v) for v in ov['wrist'].split(',')]) if 'wrist' in ov else WRIST
    act = bpy.data.actions[name]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    # reference: the clip's chest/pelvis/wrist at its first frame defines the carry offsets
    set_act(act); scene.frame_set(f0)
    C0 = armik.W(rig, 'B_Spine2'); P0 = armik.W(rig, 'B_Pelvis'); w0 = armik.W(rig, f'B_{SIDE}_Hand').translation.copy()
    wrist_chest = C0.inverted() @ wr_ov                          # carry point in the chest frame
    spear_pel = P0.to_3x3().normalized().inverted() @ SPEAR
    own0 = C0.inverted() @ w0
    frames_in, stats = [], []
    for f in range(f0, f1 + 1):
        set_act(act); sc_ = scene; sc_.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        C = armik.W(rig, 'B_Spine2'); P = armik.W(rig, 'B_Pelvis')
        own = C.inverted() @ armik.W(rig, f'B_{SIDE}_Hand').translation
        target = C @ (wrist_chest + (own - own0) * keep)
        d = SPEAR.copy() if WORLD else P.to_3x3().normalized() @ spear_pel   # m322: the upright staff stays upright in the world
        frames_in.append({'snap': snap, 'wrist': target, 'dir': d})
    set_act(None)
    # global elbow plane / hand roll (armik.arm_dp): per-frame IK with the clip's own elbow plane flipped the elbow
    # where the source arm straightened (user: running right elbow jerk at 0.23-0.27 s)
    ch = armik.arm_dp(rig, SIDE, frames_in, AX, twist_neutral=30.0, k_twist=0.6, k_dphi=1.0, k_dpsi=0.8)
    import numpy as np
    gk = np.exp(-0.5 * (np.arange(-3, 4) / 2.0) ** 2); gk /= gk.sum()
    def sm(x, cyc):
        x = np.array(x, float)
        pad = np.concatenate([x[-4:-1], x, x[1:4]]) if cyc else np.concatenate([np.repeat(x[:1], 3), x, np.repeat(x[-1:], 3)])
        return np.convolve(pad, gk, 'valid')
    cyc = name in ('Walking', 'Running', 'Standing')
    phi = sm([c['phi'] for c in ch], cyc); psi = sm(np.degrees(np.unwrap(np.radians([c['psi'] for c in ch]))), cyc)
    if cyc:                                                        # loops: the last key repeats the first exactly
        psi = psi - np.round((psi[-1] - psi[0]) / 360.0) * 360.0 * np.linspace(0, 1, len(psi))
        phi[-1], psi[-1] = phi[0], psi[0]
    poses = []
    for i, fr in enumerate(frames_in):
        sw, tw = armik.apply_arm(rig, SIDE, fr['snap'], fr['wrist'], AX, fr['dir'], phi[i], psi[i])
        stats.append((sw, tw))
        poses.append({n: rig.pose.bones[n].matrix_basis.copy() for n in ARM})
    # write back the arm channels
    for i, f in enumerate(range(f0, f1 + 1)):
        set_act(act)
        for n in ARM:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            q = poses[i][n].to_quaternion()
            if i and q.dot(poses[i - 1][n].to_quaternion()) < 0:
                q = -q
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    print(f'CARRY {name}: frames {f1 - f0 + 1}, keep {keep}, wrist swing max {max(s for s, t in stats):.1f} deg, '
          f'hand twist range {min(t for s, t in stats):.1f}..{max(t for s, t in stats):.1f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
