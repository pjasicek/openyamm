"""Arm vertices inside the face per frame of a clip (staff_rig.head_penetration). Args: blend clip."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, clip = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
import staff_rig as sr
act, (f0, f1) = sr.set_action(clip)
rows = []
for f in range(f0, f1 + 1):
    sr.scene.frame_set(f); rows.append((f,) + sr.head_penetration())
print('FACE', clip, [r for r in rows if r[1]] or 'clear')
