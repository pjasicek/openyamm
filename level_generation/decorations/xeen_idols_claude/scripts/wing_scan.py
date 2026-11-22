"""Scan the devil's clips for symmetric, raised wing poses (wing bone tails mirrored across x)."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing
from mathutils import Vector
src = sys.argv[sys.argv.index('--') + 1]
arm, body = posing.import_creature(src)
names = ['XwingA', 'XwingB', 'XwingC', 'XwingD', 'XwarmB', 'XwarmC', 'Xwing']
rows = []
for act in bpy.data.actions:
    f0, f1 = act.frame_range
    f = f0
    while f <= f1:
        posing._set_action(arm, act.name, f)
        mw = arm.matrix_world
        asym, span, top, back = 0, 0, 0, 0
        for n in names:
            a = mw @ arm.pose.bones[n].head
            b = mw @ arm.pose.bones[n + "01"].head
            asym = max(asym, (a - Vector((-b.x, b.y, b.z))).length)
            span = max(span, abs(a.x - b.x)); top = max(top, a.z, b.z); back = max(back, a.y, b.y)
        rows.append((asym, act.name, f, span, top, back))
        f += 1
rows.sort()
for r in rows[:60]:
    print('SCAN asym %.2f %s %g span %.2f top %.2f back %.2f' % r)
