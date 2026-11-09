"""Blade blow analysis like the shared gate (prop_timing): tip = (0.1433, 0, 0.65) and edge axis (-1, 0, 0) in the
ForearmBlade bone frame, forward = -Y. Per frame: tip speed, pointing angle to the target, signed edge lead.
Usage: blender -b -P blade_lead.py -- <blend> <action> [pointing limit deg]"""
import math, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); sc = bpy.context.scene; sc.render.fps = 60
lim = float(a[2]) if len(a) > 2 else 60
rig = bpy.data.objects['Rig']; act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
pb = rig.pose.bones['ForearmBlade']; TIP = Vector((0.1433, 0, 0.65)); EDGE = Vector((-1, 0, 0))
rows = []
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    sc.frame_set(f); M = rig.matrix_world @ pb.matrix
    rows.append((f, M @ TIP, (M.to_3x3() @ EDGE).normalized(), (M.to_3x3() @ TIP).normalized()))
best = None
for (f0, p0, e0, d0), (f1, p1, e1, d1) in zip(rows, rows[1:]):
    v = (p1 - p0) * 60; sp = v.length; d = (d0 + d1).normalized(); point = math.degrees(d.angle(Vector((0, -1, 0))))
    lead = v.dot((e0 + e1).normalized()) / max(sp, 1e-9)
    if f0 % 3 == 0: print(f'  f{f0:3d} t {f0 / 60:.3f} speed {sp:5.2f} pointing {point:5.1f} lead {lead:+.2f}')
    if point <= lim and (best is None or sp > best[1]): best = (f0, sp, lead, point)
print('BLOW frame', best[0], 'time %.4f' % ((best[0] + .5) / 60), 'speed %.2f lead %+.2f pointing %.1f' % best[1:])
