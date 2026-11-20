"""Gate: the lowest point of the carbine and of every plate (Arm_*) and of the body per frame of a clip; a held
prop or plate below the floor (z < -TOL) fails. Args: -- <blend> <clip> [...]  (env TOL m, default 0.01)"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); TOL = float(os.environ.get('TOL', '0.01'))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
obs = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name in ('Body', 'Rifle') or o.name.startswith('Arm_')) and not o.hide_render]
def low(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear(); co = co.reshape(-1, 3)
    return float((co @ np.array(o.matrix_world.to_3x3())[2] + o.matrix_world[2][3]).min())
for clip in a[1:]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); worst = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for o in obs:
            z = low(o)
            if o.name not in worst or z < worst[o.name][0]: worst[o.name] = (z, f)
    sc.frame_set(f1); last = {o.name: low(o) for o in obs}
    bad = {n: (round(z * 100, 1), f) for n, (z, f) in worst.items() if z < -TOL}
    print('PROPFLOOR', clip, 'FAIL' if bad else 'PASS', 'lowest cm', {n: round(z * 100, 1) for n, (z, f) in sorted(worst.items(), key=lambda x: x[1][0])[:4]},
          'last frame lowest cm', round(min(last.values()) * 100, 1), bad)
