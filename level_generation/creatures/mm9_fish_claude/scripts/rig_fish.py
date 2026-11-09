"""Weight the reduced fish (Body: body + eye lenses, Fins: fin leaves) to the original MM9 FISH.abc skeleton.

- Body: each vertex takes the bone of the nearest MM9 body vertex among the axial/head bones (XCENTER, Xbody, Xtail,
  Xtmid, and Xmouth/Xjaw only within 18 mm of the snout tip, as MM9's lips; the MM9 skin is rigid, one bone per vertex), then diffuses along the mesh (DIFFUSE iterations).
  Eye lenses are rigid with their nearest body vertex.
- Fins: the MM9 fin bones by nearest MM9 vertex of that fin (dorsal Xtopfin/Xmidfin, anal Xbotfin, caudal
  Xttop/Xtmid/Xtbot, pectorals Xsfin+Xsidefin (right, -x) / Xsfin01+Xsidefin01 (left), pelvics Xbotfin.001 (right) /
  Xbotfin01 (left)), blended from the body weights at the root (the buried band) over ROOT_BLEND metres of fin, so
  each leaf leaves the body without a seam; a short diffusion over the leaf grid.
- Four influences, normalised. MM9 meshes removed; armature modifier on both.
Args: <reduced blend> <mm9 rig blend> <out blend> <report json>"""
import bpy, sys, json, os
import numpy as np
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, RIG, OUT, REP = argv
DIFFUSE = int(os.environ.get('RIG_DIFFUSE', '12'))
ROOT_BLEND = 0.010
CORE = ['XCENTER', 'Xbody', 'Xtail', 'Xtmid', 'Xmouth', 'Xjaw']
FINS = {0: ['Xtopfin', 'Xmidfin'], 1: ['Xbotfin'], 2: ['Xbotfin01'], 3: ['Xttop', 'Xtmid', 'Xtbot'],
        4: ['Xsfin01', 'Xsidefin01'], 12: ['Xbotfin.001'], 14: ['Xsfin', 'Xsidefin']}
# fin ids: build_fins.py order dorsal 0, anal 1, pelvic 2, caudal 3, pectoral 4; +10 = the mirrored (right, -x) copy

bpy.ops.wm.open_mainfile(filepath=IN)
with bpy.data.libraries.load(RIG) as (src, dst):
    dst.objects = list(src.objects)
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
arm = bpy.data.objects['MM9_Rig']
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
mpos, mlab = [], []
for o in dst.objects:
    if o.type != 'MESH':
        continue
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


body = bpy.data.objects['Body']; fins = bpy.data.objects['Fins']
me = body.data
n = len(me.vertices)
piece = np.zeros(n, int)
pa = me.attributes['piece']
for p in me.polygons:
    for v in p.vertices:
        piece[v] = max(piece[v], pa.data[p.index].value)
kc, idc = tree(CORE)
kh, idh = tree([b for b in CORE if b not in ('Xmouth', 'Xjaw')])
SNOUT = min(v.co.y for v in me.vertices) + 0.018   # MM9's Xmouth/Xjaw carry only the lips (4 vertices each)
W = np.zeros((n, len(bones)))
for i, v in enumerate(me.vertices):
    k, ids = (kc, idc) if v.co.y < SNOUT else (kh, idh)
    W[i, bidx[mlab[ids[k.find(v.co)[1]]]]] = 1
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
for _ in range(DIFFUSE):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    W = np.where((piece == 0)[:, None], 0.5 * W + 0.5 * avg, W)
bodyv = np.nonzero(piece == 0)[0]
kb = KDTree(len(bodyv))
for j, i in enumerate(bodyv):
    kb.insert(me.vertices[i].co, j)
kb.balance()
for i in np.nonzero(piece == 1)[0]:
    W[i] = 0
# each eye lens rigid: the weights of the body vertex nearest to its centre
for side in (1, -1):
    ids = [i for i in np.nonzero(piece == 1)[0] if me.vertices[i].co.x * side > 0]
    c = sum((me.vertices[i].co for i in ids), me.vertices[ids[0]].co * 0) / len(ids)
    W[ids] = W[bodyv[kb.find(c)[1]]]

fm = fins.data
nf = len(fm.vertices)
fin = np.array([d.value for d in fm.attributes['fin'].data])
root = np.array([d.value for d in fm.attributes['root'].data])
WF = np.zeros((nf, len(bones)))
ftrees = {k: tree(v) for k, v in FINS.items()}
for i, v in enumerate(fm.vertices):
    k, ids = ftrees[int(fin[i])]
    lab = np.zeros(len(bones)); lab[bidx[mlab[ids[k.find(v.co)[1]]]]] = 1
    bw = W[bodyv[kb.find(v.co)[1]]]
    s = np.clip((root[i] + 0.002) / ROOT_BLEND, 0, 1)
    s = s * s * (3 - 2 * s)
    WF[i] = (1 - s) * bw + s * lab
fn = [[] for _ in range(nf)]
for e in fm.edges:
    a, b = e.vertices; fn[a].append(b); fn[b].append(a)
for _ in range(3):
    WF = 0.5 * WF + 0.5 * np.array([WF[nb].mean(0) if nb else WF[i] for i, nb in enumerate(fn)])


def write(ob, W):
    order = np.argsort(-W, axis=1)
    for i in range(len(W)):
        keep = order[i, :4]; row = np.zeros(len(bones)); row[keep] = W[i, keep]; row[row < 0.02] = 0
        W[i] = row / row.sum()
    for b in bones:
        ob.vertex_groups.new(name=b)
    for i in range(len(W)):
        for j in np.nonzero(W[i])[0]:
            ob.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
    for g in list(ob.vertex_groups):
        if not np.any(W[:, bidx[g.name]] > 0):
            ob.vertex_groups.remove(g)
    ob.parent = arm
    ob.matrix_parent_inverse = arm.matrix_world.inverted()
    m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = arm
    return {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}


rep = {'body_dominant': write(body, W), 'fins_dominant': write(fins, WF), 'body_verts': n, 'fin_verts': nf}
for o in list(dst.objects):
    if o.type == 'MESH':
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
