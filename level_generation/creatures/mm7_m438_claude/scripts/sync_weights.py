"""Carry the gated chain's skin weights into the textured master (user review 2026-10-20: the skirt weights changed
after the texture chain; sync_actions.py only carries clips). The Body meshes must match vertex for vertex (count and
rest positions within 0.1 mm); every vertex group of <dst>'s Body is replaced by <src>'s.
Args: -- <src blend (work/rig_v5.blend)> <dst blend (work/rig_v6.blend)>"""
import bpy, sys, os
import numpy as np
src, dst = (os.path.abspath(p) for p in sys.argv[sys.argv.index('--') + 1:][:2])
bpy.ops.wm.open_mainfile(filepath=dst)
body = bpy.data.objects['Body']; me = body.data
with bpy.data.libraries.load(src, link=False) as (data_from, data_to):
    data_to.objects = ['Body']
sb = data_to.objects[0]; sm = sb.data
n = len(me.vertices)
a = np.empty(n * 3); me.vertices.foreach_get('co', a)
if len(sm.vertices) != n:
    raise SystemExit(f'SYNCW vertex count differs: {len(sm.vertices)} vs {n}')
b = np.empty(n * 3); sm.vertices.foreach_get('co', b)
dmax = float(np.abs(a - b).max())
if dmax > 1e-4:
    raise SystemExit(f'SYNCW rest positions differ by {dmax * 1000:.2f} mm')
names = [g.name for g in sb.vertex_groups]
old = {}
for v in me.vertices:
    for e in v.groups:
        old[(v.index, body.vertex_groups[e.group].name)] = e.weight
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {nm: body.vertex_groups.new(name=nm) for nm in names}
changed = 0; pv = np.zeros(n, np.int32); sm.attributes['piece'].data.foreach_get('value', pv); per = {}
for v in sm.vertices:
    for e in v.groups:
        nm = names[e.group]; groups[nm].add([v.index], e.weight, 'REPLACE')
        if abs(old.get((v.index, nm), 0.0) - e.weight) > 1e-4:
            changed += 1; per[int(pv[v.index])] = per.get(int(pv[v.index]), 0) + 1
bpy.data.objects.remove(sb)
print(f'SYNCW {n} vertices, {len(names)} groups, weights changed {changed} (per piece {dict(sorted(per.items()))}), rest match {dmax * 1000:.3f} mm')
bpy.ops.wm.save_as_mainfile(filepath=dst)
