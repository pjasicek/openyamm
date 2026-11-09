"""(Re)build and weight the fin leaves on a blend whose 'Body' is already weighted and UV'd (the body keeps its UVs and
paint: only 'Fins' changes). The leaf vertices come from build_fins.py.

MM9's swim holds its long fins swept back by a near constant rotation about one pivot each (Xtopfin 40, Xmidfin 30,
Xbotfin 44 degrees): on MM9's few rigid triangles that reads as a lowered fin, but on a long leaf one pivot swings the
far end straight into the body (the rear dorsal sank 4 cm). So:
- dorsal and anal follow the body under them (each vertex the weights of its nearest body vertex: they ripple with the
  spine; the master's rays already lean back);
- caudal lobes (Xttop, Xtmid, Xtbot), pectorals (Xsfin+Xsidefin, +01 on the left) and pelvics (Xbotfin.001, Xbotfin01)
  take MM9's own bones by nearest MM9 vertex, blended from the body weights at the root over ROOT_BLEND metres
  (pectorals at PECTORAL_GAIN).
Args: <in blend> <fins npz> <atlas png> <mm9 rig blend> <out blend> <report json>"""
import bpy, sys, json, os
import numpy as np
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, NPZ, ATLAS, RIG, OUT, REP = argv
ROOT_BLEND = 0.010
PECTORAL_GAIN = 0.6   # MM9's pectoral flap at 60 %: our flank is wider than MM9's and the full flap buries the fin
FINS = {3: ['Xttop', 'Xtmid', 'Xtbot'], 2: ['Xbotfin01'], 12: ['Xbotfin.001'],
        4: ['Xsfin01', 'Xsidefin01'], 14: ['Xsfin', 'Xsidefin']}   # 0 dorsal, 1 anal: body only
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']
bones = [b.name for b in arm.data.bones]; bidx = {b: i for i, b in enumerate(bones)}
with bpy.data.libraries.load(RIG) as (src, dst):
    dst.objects = [n for n in src.objects if n != 'MM9_Rig']
mpos, mlab = [], []
for o in dst.objects:
    if o.type == 'MESH':
        for v in o.data.vertices:
            g = max(v.groups, key=lambda g: g.weight)
            mpos.append(o.matrix_world @ v.co); mlab.append(o.vertex_groups[g.group].name)
mlab = np.array(mlab)


def tree(names):
    ids = [i for i in range(len(mpos)) if mlab[i] in names]
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


# body weights (surface vertices only: eye lenses are piece 1)
me = body.data
gname = {g.index: g.name for g in body.vertex_groups}
piece = np.zeros(len(me.vertices), int)
pa = me.attributes['piece']
for p in me.polygons:
    for v in p.vertices:
        piece[v] = max(piece[v], pa.data[p.index].value)
BW = np.zeros((len(me.vertices), len(bones)))
for v in me.vertices:
    for g in v.groups:
        BW[v.index, bidx[gname[g.group]]] = g.weight
bodyv = np.nonzero(piece == 0)[0]
kb = KDTree(len(bodyv))
for j, i in enumerate(bodyv):
    kb.insert(me.vertices[i].co, j)
kb.balance()

old = bpy.data.objects.get('Fins')
mats = list(old.data.materials) if old else []
if old:
    bpy.data.objects.remove(old)
d = np.load(NPZ)
fm = bpy.data.meshes.new('Fins')
fm.from_pydata([tuple(v) for v in d['v']], [], [tuple(int(i) for i in t) for t in d['t']])
uv = fm.uv_layers.new(name='UVMap')
for li, l in enumerate(fm.loops):
    uv.data[li].uv = tuple(d['uv'][l.vertex_index])
for p in fm.polygons:
    p.use_smooth = True
fins = bpy.data.objects.new('Fins', fm); bpy.context.scene.collection.objects.link(fins)
for m in mats:
    fm.materials.append(m)
fin, root = d['fin'], d['root']
nf = len(fm.vertices)
WF = np.zeros((nf, len(bones)))
trees = {k: tree(v) for k, v in FINS.items()}
for i, v in enumerate(fm.vertices):
    bw = BW[bodyv[kb.find(v.co)[1]]]
    f = int(fin[i])
    if f in trees:
        k, ids = trees[f]
        lab = np.zeros(len(bones)); lab[bidx[mlab[ids[k.find(v.co)[1]]]]] = 1
        s = np.clip((root[i] + 0.002) / ROOT_BLEND, 0, 1); s = s * s * (3 - 2 * s)
        if f in (4, 14):
            s *= PECTORAL_GAIN
        WF[i] = (1 - s) * bw + s * lab
    else:
        WF[i] = bw
fn = [[] for _ in range(nf)]
for e in fm.edges:
    a, b = e.vertices; fn[a].append(b); fn[b].append(a)
for _ in range(3):
    WF = 0.5 * WF + 0.5 * np.array([WF[nb].mean(0) if nb else WF[i] for i, nb in enumerate(fn)])
order = np.argsort(-WF, axis=1)
for i in range(nf):
    keep = order[i, :4]; row = np.zeros(len(bones)); row[keep] = WF[i, keep]; row[row < 0.02] = 0
    WF[i] = row / row.sum()
for b in bones:
    fins.vertex_groups.new(name=b)
for i in range(nf):
    for j in np.nonzero(WF[i])[0]:
        fins.vertex_groups[bones[j]].add([i], float(WF[i, j]), 'REPLACE')
for g in list(fins.vertex_groups):
    if not np.any(WF[:, bidx[g.name]] > 0):
        fins.vertex_groups.remove(g)
fins.parent = arm; fins.matrix_parent_inverse = arm.matrix_world.inverted()
m = fins.modifiers.new('Armature', 'ARMATURE'); m.object = arm
for o in list(dst.objects):
    if o.name in bpy.data.objects:
        bpy.data.objects.remove(o)
rep = {'fin_verts': nf, 'dominant': {bones[j]: int((WF[:, j] > 0.5).sum()) for j in range(len(bones)) if (WF[:, j] > 0).any()}}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIGFINS ' + json.dumps(rep))
