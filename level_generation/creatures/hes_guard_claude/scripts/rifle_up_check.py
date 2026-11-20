"""Rifle orientation gate (user review 2026-10-22): per frame of every clip, the angle between the rifle's up axis
(bone Rifle +Z, up the pistol grip) and world up, its roll (the up axis against the vertical plane through the barrel)
and the barrel pitch. Limits: the Attack's aim (from the end of the raise to 0.2 s after the shot) <= AIM deg, every
held frame of the other clips (both fists on the gun) <= CARRY deg; Death is reported only. Writes
review/rifle_up.json. Args: -- <blend> <clip> [...]"""
import bpy, sys, os, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = json.load(open(os.path.join(HERE, 'work', 'clip_timing.json')))
AIM, CARRY = float(os.environ.get('AIM', '20')), float(os.environ.get('CARRY', '35'))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; UP = Vector((0, 0, 1)); out = {}; ok = True
for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); M = (rig.matrix_world @ rig.pose.bones['Rifle'].matrix).to_3x3().normalized()
        y, z = M @ Vector((0, 1, 0)), M @ Vector((0, 0, 1))
        vert = y.cross(UP).normalized() if y.cross(UP).length > 1e-6 else Vector((1, 0, 0))
        roll = math.degrees(math.asin(max(-1, min(1, z.dot(vert)))))
        rows.append({'f': f, 'up_deg': round(math.degrees(z.angle(UP)), 1), 'roll_deg': round(roll, 1),
                     'pitch_deg': round(math.degrees(math.asin(max(-1, min(1, y.z)))), 1)})
    if c == 'Attack':
        lo = T['Attack']['lead_frames']; hi = int(round((T['Attack']['impact'] + 0.2) * 30))
        sel, lim = [r for r in rows if lo <= r['f'] <= hi], AIM
    elif c == 'Death':
        sel, lim = [], None
    else:
        sel, lim = rows, CARRY
    worst = max((r['up_deg'] for r in sel), default=None)
    passed = None if lim is None else worst <= lim
    ok &= passed is not False
    out[c] = {'limit_deg': lim, 'checked_frames': len(sel), 'up_max_deg': worst, 'pass': passed,
              'roll_abs_max_deg': max(abs(r['roll_deg']) for r in (sel or rows)), 'rows': rows}
    print('RIFLEUP', c, 'limit', lim, 'up max', worst, 'roll max', out[c]['roll_abs_max_deg'], 'PASS' if passed else ('-' if passed is None else 'FAIL'))
json.dump(out, open(os.path.join(HERE, 'review', 'rifle_up.json'), 'w'), indent=1)
print('RIFLEUP all', 'PASS' if ok else 'FAIL')
