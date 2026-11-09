"""Rest-mesh fixes of the grafted heads (body faces and every UV stay as retextured).
1. Narrow wide head parts so neighbouring heads clear each other (mm6_hyd_claude graft LAT_SQUEEZE, applied here to
the finished rest mesh so the body faces and every UV stay as retextured): for each head k in SQUEEZE, vertices of
its faces (part k) beyond HALF[k] m from the Head<k> bone's vertical plane are pulled toward it, keeping
HALF + (|lateral| - HALF) x factor.
2. Drop loose head pieces floating more than GAP from every other piece of their head, and loose body pieces high on
the necks (old dorsal spikes of the cut-away heads). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
SQUEEZE = {1: 0.6}           # head 1's bat-wing fins swept through head 2's crest at rest
HALF = {1: 0.10}
GAP = 0.012                # m: a head piece farther than this from every other piece of its head floats
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = ob.data
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
co = np.array([tuple(v.co) for v in me.vertices])
for k, f in SQUEEZE.items():
    vs = np.unique(np.concatenate([list(p.vertices) for p in me.polygons if part[p.index] == k]))
    b = rig.data.bones[f'Head{k}']
    h, t = np.array(b.head_local), np.array(b.tail_local)
    fwd = t - h; fwd[2] = 0; fwd /= np.linalg.norm(fwd)
    lat = np.cross(fwd, [0, 0, 1.0])
    d = (co[vs] - h) @ lat
    excess = np.abs(d) - HALF[k]
    m = excess > 0
    co[vs[m]] -= (np.sign(d[m]) * excess[m] * (1 - f))[:, None] * lat
    print('SQUEEZE head', k, 'moved', int(m.sum()), 'of', len(vs), 'max lateral before', round(float(np.abs(d).max()), 3))
me.vertices.foreach_set('co', co.ravel()); me.update()
# loose head fragments floating clear of their head (detached crest tips and teeth of the Meshy heads)
import bmesh
from mathutils.kdtree import KDTree
bm = bmesh.new(); bm.from_mesh(me); pl = bm.faces.layers.int.get('part')
dropped = 0; doomed = []
for k in range(1, 6):
    faces = [f_ for f_ in bm.faces if f_[pl] == k]
    vs = {v for f_ in faces for v in f_.verts}; seen = set(); comps = []
    for v in vs:
        if v in seen:
            continue
        st = [v]; seen.add(v); comp = [v]
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y in vs and y not in seen:
                    seen.add(y); comp.append(y); st.append(y)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    for i, comp in enumerate(comps[1:], 1):
        rest = [v for c in comps[:i] + comps[i + 1:] for v in c]
        kd = KDTree(len(rest))
        for j, v in enumerate(rest):
            kd.insert(v.co, j)
        kd.balance()
        gap = min(kd.find(v.co)[2] for v in comp)
        if gap > GAP:
            doomed += comp; dropped += 1
# loose body pieces high on the necks: dorsal spikes that sat on the old heads (separate pieces, so the graft's flood fill
# missed them); their copied weights point at the cut-away head and they floated in every clip
bf = [f_ for f_ in bm.faces if f_[pl] == 0]
vs = {v for f_ in bf for v in f_.verts}; seen = set(); comps = []
for v in vs:
    if v in seen:
        continue
    st = [v]; seen.add(v); comp = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y in vs and y not in seen:
                seen.add(y); comp.append(y); st.append(y)
    comps.append(comp)
comps.sort(key=len, reverse=True)
spikes = 0
for comp in comps[1:]:
    if np.mean([v.co.z for v in comp]) > 1.05 and len(comp) < 200:
        doomed += comp; spikes += 1
print('NECK SPIKES dropped', spikes)
bmesh.ops.delete(bm, geom=doomed, context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
print('FRAGMENTS dropped', dropped)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
