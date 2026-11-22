"""Move a wrist by an offset in the chest frame over a frame window (smooth sine envelope), solving the arm with the
minimal-change IK (armik.solve, elbow plane carried, hand world orientation kept). Used where a source clip's hand
passes into the body (witch Attack follow-through: the right claw swept into her left hip, G6 5.8 cm at frame 39).
Args: -- <in blend> <out blend> <Action>:<L|R>:<f_start>:<f_peak>:<f_end>:<dx>,<dy>,<dz> ...  (offset in metres, chest frame
at rest = world: +x her left, -y forward, +z up)"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for it in items:
    name, side, fs, fp, fe, off = it.split(':'); fs, fp, fe = int(fs), int(fp), int(fe)
    off = Vector([float(x) for x in off.split(',')])
    act = bpy.data.actions[name]; rig.animation_data_create()
    ARM = [f'B_{side}_Clavicle', f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand']
    keys = {}
    for f in range(fs, fe + 1):
        w = math.sin(math.pi / 2 * (f - fs) / max(fp - fs, 1)) if f <= fp else math.cos(math.pi / 2 * (f - fp) / max(fe - fp, 1))
        w = max(0.0, w) ** 2
        rig.animation_data.action = act
        if len(act.slots): rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        rig.animation_data.action = None
        for n, m in snap.items():
            rig.pose.bones[n].matrix_basis = m
        bpy.context.view_layer.update()
        C = armik.W(rig, 'B_Spine2').to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().normalized().inverted()
        T = armik.W(rig, f'B_{side}_Hand').translation + C @ (off * w)
        armik.solve(rig, side, T)
        keys[f] = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARM}
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    for f, ks in keys.items():
        for n, q in ks.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action = None
    print(f'ARMPUSH {name} {side} frames {fs}-{fp}-{fe} offset {tuple(round(x, 3) for x in off)}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
