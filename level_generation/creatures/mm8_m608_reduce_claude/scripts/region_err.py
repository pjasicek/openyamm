"""Per-region share of the ladder error: blender -b -P region_err.py -- <ladder.blend> <Cand_xx>. For every 3rd frame of
every clip, both-direction vertex->surface distances, grouped by the dominant bone family of the vertex (source side)
or of the nearest source vertex (candidate side); prints counts over 3 mm and p99 per family."""
import sys, bpy, bmesh, collections, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import kdtree
blend, cn = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cn]
names = {g.index: g.name for g in src.vertex_groups}
def fam(vi):
    gs = [g for g in src.data.vertices[vi].groups if names[g.group] != 'ReduceProtect']
    n = names[max(gs, key=lambda g: g.weight).group] if gs else '?'
    for k, p in (('arm', ('UpperArm', 'Forearm', 'Hand')), ('roller', ('Roller',)), ('head', ('Head',)), ('torso', ('Chest', 'Waist', 'Neck'))):
        if n.startswith(p): return k + ('_' + n.split('_')[-1] if k == 'arm' else '')
    return n
sf = [fam(i) for i in range(len(src.data.vertices))]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.verts.ensure_lookup_table(); return b
acc = collections.defaultdict(list); spots = collections.Counter()
for act in bpy.data.actions:
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f); bs = ev(src); bc = ev(c); ts = BVHTree.FromBMesh(bs); tc = BVHTree.FromBMesh(bc)
        kd = kdtree.KDTree(len(bs.verts))
        for v in bs.verts: kd.insert(v.co, v.index)
        kd.balance()
        for v in bs.verts:
            d = tc.find_nearest(v.co)[3]; acc[sf[v.index]].append(d)
            if d > .003: spots[(sf[v.index], v.index)] += 1
        for v in bc.verts:
            d = ts.find_nearest(v.co)[3]; j = kd.find(v.co)[1]; acc[sf[j]].append(d)
            if d > .003: spots[(sf[j], j)] += 1
        bs.free(); bc.free()
allv = np.concatenate([np.array(x) for x in acc.values()]); n3 = (allv > .003).sum()
print('ALL', len(allv), 'over3mm', n3, 'p99 %.2f' % (np.percentile(allv, 99) * 1000))
for k, x in sorted(acc.items()):
    x = np.array(x); print('FAM', k, len(x), 'over3', int((x > .003).sum()), 'share %.2f' % ((x > .003).sum() / max(n3, 1)), 'p99 %.2f' % (np.percentile(x, 99) * 1000))
rest = {}
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
for (k, vi), n in spots.most_common(15):
    print('SPOT', k, vi, n, tuple(round(x, 3) for x in src.data.vertices[vi].co))
