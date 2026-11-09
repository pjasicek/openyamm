"""Floor gate: per clip the lowest posed vertex over all frames (min and max of the per-frame lowest point, cm).
Args: -- <blend> <action> [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    lows = []
    for f in range(int(act.frame_range[1]) + 1):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
        lows.append(c.reshape(-1, 3)[:, 2].min())
    print(f'FLOOR {an}: lowest point per frame {100 * min(lows):.1f} .. {100 * max(lows):.1f} cm (last {100 * lows[-1]:.1f})')
