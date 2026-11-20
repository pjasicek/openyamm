"""Edge stretch per frame for one clip: p99.9 and the worst edges with their weights.
Usage: stretch_probe.py -- <blend> <clip> [frames...]"""
import bpy, numpy as np, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); clip = a[1] if len(a) > 1 else 'Standing'
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; sc = bpy.context.scene
rest = np.array([v.co[:] for v in o.data.vertices]); e = np.array([ed.vertices[:] for ed in o.data.edges])
L = np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1); names = {g.index: g.name for g in o.vertex_groups}
rig.animation_data.action = bpy.data.actions[clip]; lo, hi = map(int, rig.animation_data.action.frame_range)
frames = [int(f) for f in a[2:]] or list(range(lo, hi + 1, 2))
for f in frames:
    sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.array([v.co[:] for v in m.vertices]); ev.to_mesh_clear()
    r = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1) / np.maximum(L, 1e-9)
    j = int(np.argmax(r)); v = e[j][0]
    print(f'{clip} f{f:3d} p999 {np.quantile(r, .999):.2f} max {r[j]:.2f} n>1.5 {(r > 1.5).sum():4d} worst at {rest[v].round(3)}',
          {names[g.group]: round(g.weight, 2) for g in o.data.vertices[v].groups})
