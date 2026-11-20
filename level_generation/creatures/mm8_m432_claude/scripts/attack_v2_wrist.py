"""Visible wrist bend per frame (forearm direction vs wrist -> finger-root direction, degrees) and two-hand grip
gap: args <blend> <action> [grip json dir relative to the project]. Prints max and the per-frame series."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / args[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
a = bpy.data.actions[args[1]]; rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
def W(n):
    return rig.matrix_world @ rig.pose.bones[n].matrix
def bend(side):
    f, h = W(f'B_{side}_Forearm'), W(f'B_{side}_Hand')
    roots = [W(f'B_{side}_Finger{i}').translation for i in (1, 2, 3, 4) if f'B_{side}_Finger{i}' in rig.pose.bones]
    fd = (h.translation - f.translation).normalized(); hd = (sum(roots, Vector()) / 4 - h.translation).normalized()
    return math.degrees(fd.angle(hd))
rest = {}
for side in 'RL':
    fb, hb = rig.data.bones[f'B_{side}_Forearm'], rig.data.bones[f'B_{side}_Hand']
    roots = [rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in (1, 2, 3, 4) if f'B_{side}_Finger{i}' in rig.data.bones]
    rest[side] = math.degrees((hb.head_local - fb.head_local).angle(sum(roots, Vector()) / 4 - hb.head_local))
import sys as _s
_s.path.insert(0, str(P / 'scripts'))
import armik_v2 as armik
def twist(side):
    fb, hb = rig.data.bones[f'B_{side}_Forearm'], rig.data.bones[f'B_{side}_Hand']
    fr = rig.pose.bones[fb.name].matrix.to_3x3() @ fb.matrix_local.to_3x3().inverted()
    hr = rig.pose.bones[hb.name].matrix.to_3x3() @ hb.matrix_local.to_3x3().inverted()
    _, tw = armik.split_swing_twist((fr.inverted() @ hr).to_quaternion(), (hb.head_local - fb.head_local).normalized())
    return math.degrees(tw)
twists = {s: [] for s in 'RL'}
series = {s: [] for s in 'RL'}
end = int(a.frame_range[1])
for k in range(end * 2 + 1):
    f = k / 2; sc.frame_set(int(f), subframe=f % 1)
    for s in 'RL':
        series[s].append(round(bend(s), 1)); twists[s].append(round(twist(s), 1))
print('WRIST', args[0], args[1], 'rest', {s: round(v, 1) for s, v in rest.items()},
      'max', {s: max(v) for s, v in series.items()})
for s in 'RL':
    print('SERIES', s, series[s])
    print('TWIST', s, twists[s])
