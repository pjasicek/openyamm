"""Per-bone error of a ladder candidate (REA_CAND, default Cand_80) against the source at a few frames
(REA_FRAMES clip:frame,...): both directions, grouped by the dominant bone of the nearest source vertex."""
import os, bpy, bmesh, numpy as np, collections
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
names = {g.index: g.name for g in src.vertex_groups}
dom = [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); b.faces.ensure_lookup_table(); return b
cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_80')]
for spec in os.environ.get('REA_FRAMES', 'Standing:0,Death:27').split(','):
    clip, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs, bc = ev(src), ev(cand); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
    per = collections.defaultdict(list)
    for v in bs.verts:
        per[dom[v.index]].append(tc.find_nearest(v.co)[3])
    for v in bc.verts:
        _, _, fi, dist = ts.find_nearest(v.co)
        per[dom[bs.faces[fi].verts[0].index]].append(dist)
    rows = sorted(((np.percentile(x, 99) * 1000, max(x) * 1000, len(x), k) for k, x in per.items()), reverse=True)[:12]
    print('REGION', spec, cand.name, ' | '.join(f'{k} p99 {a:.1f} max {b:.1f} n{n}' for a, b, n, k in rows), flush=True)
    bs.free(); bc.free()
