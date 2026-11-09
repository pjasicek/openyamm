"""Per clip: min z of the posed mesh over all frames, and the max bounding height (for the collision box check)."""
import bpy
import numpy as np
rig = bpy.data.objects['Ckt_Rig']; mesh = bpy.data.objects['Cockatrice']
for a in bpy.data.actions:
    rig.animation_data.action = a
    lo, hi = 9, -9
    for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg)
        z = np.array([v.co.z for v in ev.data.vertices]) if len(ev.data.vertices) else np.zeros(1)
        lo, hi = min(lo, z.min()), max(hi, z.max())
    print('MINZ', a.name, round(lo, 4), 'maxz', round(hi, 4))
