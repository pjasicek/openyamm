"""Frame-to-frame jumps of the arm chain and staff in a clip: world rotation change (deg) between consecutive keys of
Right/Left Arm, ForeArm, Hand, and the staff axis. Args: blend clip."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
blend, clip = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
import staff_rig as sr
act, (f0, f1) = sr.set_action(clip)
names = [s + b for s in ('Right', 'Left') for b in ('Arm', 'ForeArm', 'Hand')]
prev = None
for f in range(f0, f1 + 1):
    sr.scene.frame_set(f)
    cur = {n: (sr.AW @ sr.B(n).matrix).to_quaternion() for n in names}
    ax = (sr.AW @ sr.B('StaffTip').head - sr.AW @ sr.B('Staff').head).normalized()
    if prev:
        jumps = {n[:1] + n[-4:]: round(min(a_, 360 - a_)) for n in names for a_ in [math.degrees(prev[0][n].rotation_difference(cur[n]).angle)]}
        print('JUMP', f, 'staff', round(math.degrees(prev[1].angle(ax))), jumps)
    prev = (cur, ax)
