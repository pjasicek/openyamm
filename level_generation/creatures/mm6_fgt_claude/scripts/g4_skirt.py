"""G4 for the skirt strips (gob2 review 1: middle strips stretched between the legs in the wide cast stance): per
action the max and p99 edge stretch over the strip pieces (weights_fix.py STRIPS rule) and the worst strip.
Args: -- <blend> action [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
STRIPS = {16,17,18,19,20,21,22,23,24,25,28,30,31,33,34,36,38}
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[np.isin(pv[E[:, 0]], list(STRIPS))]
rest = np.array([tuple(v.co) for v in me.vertices]); rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    worst = (0, 0, 0, None)
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(rl, 1e-6)
        i = int(np.argmax(r))
        if r[i] > worst[0]:
            worst = (float(r[i]), float(np.percentile(r, 99)), f, int(pv[E[i, 0]]))
    print(f'SKIRT {an:9s} max {worst[0]:.2f}x (p99 {worst[1]:.2f}) at frame {worst[2]}, strip piece {worst[3]}')
