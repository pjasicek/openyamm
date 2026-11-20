"""Floor gate (Blender): lowest posed vertex per clip at 48 Hz (half-frame steps), overall and per v3 part
(0 cdr1 body/wings, 1 grafted head, 2 neck loft, 3 spines), and the frame where it happens.
Usage: blender -b <blend> -P floor_gate.py -- <out.json>"""
import bpy, json, sys
import numpy as np
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; sc = bpy.context.scene
part = o.data.attributes.get('v3part'); P_ = np.array([d.value for d in part.data]) if part else np.zeros(len(o.data.vertices), int)
res = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; best = {}
    for k in range(int((f1 - f0) * 2) + 1):
        fr = f0 + k * 0.5; sc.frame_set(int(fr), subframe=fr % 1)
        dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); me = ev.to_mesh()
        z = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', z); z = z.reshape(-1, 3)[:, 2]; ev.to_mesh_clear()
        for p in np.unique(P_):
            m = float(z[P_ == p].min())
            if str(p) not in best or m < best[str(p)][0]: best[str(p)] = (round(m, 4), fr)
    res[act.name] = {'min_z_by_part': best, 'min_z': min(v[0] for v in best.values())}
json.dump(res, open(out, 'w'), indent=1); print('FLOOR', {k: v['min_z'] for k, v in res.items()})
