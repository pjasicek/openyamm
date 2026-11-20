"""New head-set UVs for the face repaint (coordinator 2026-11-02: the face sat on 50 small xatlas charts, the midline and nose / lips were
chart borders, and every patch pass fought those seams). The body set is kept exactly (its paid paint stays valid); the head set (head
shell with eyeballs, hair, elf ears) is re-laid with uv_atlas.unwrap(charts='bones') on segment groups: 'face' (the whole front of the
face from the hairline to under the jaw, one disc cut only from the eye openings), 'scalp' (the rest of the head shell), 'hair',
'hairback' (long hair below the nape, 0.6x), 'ears'. The face gets 1.8x density.
Args: <asm npz> <old uv npz> <out uv npz> <report json>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
ASM, OLD, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
A = np.load(ASM); co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]
O = dict(np.load(OLD))
HEAD = [n for n in ('head', 'hair', 'ears') if n in names]
fc = comp[tri[:, 0]]
fi = np.where(np.isin(fc, [names.index(n) for n in HEAD]))[0]
# clean the head set's topology so the face is a disc: drop zero-area midline slivers that the mirror left as back-to-back duplicate pairs
# (non-manifold edges under the chin), then fan-fill the tiny holes at the mouth corners (<= 6 vertices). New faces use existing vertices.
import collections
TH = tri[fi]
# weld head-shell vertices closer than 0.6 mm (the mirror's midline micro-edges under the chin), drop collapsed and duplicate faces
hsv = np.unique(TH[comp[TH[:, 0]] == names.index('head')]); hsv = hsv[(np.abs(co[hsv, 0]) < 0.0015) & (np.abs(co[hsv, 2] - 0.5918) < 0.003) & (co[hsv, 1] < -0.08)]      # the chin's midline cluster only
rep_ = np.arange(len(co))
_dd = np.linalg.norm(co[hsv][:, None] - co[hsv][None], axis=2); _pa = np.argwhere(np.triu(_dd < 6e-4, 1))     # small cluster: brute force
for a, b in _pa:
    ra, rb = hsv[a], hsv[b]
    while rep_[ra] != ra: ra = rep_[ra]
    while rep_[rb] != rb: rb = rep_[rb]
    if ra != rb: rep_[max(ra, rb)] = min(ra, rb)
for i in range(len(rep_)):
    r = i
    while rep_[r] != r: r = rep_[r]
    rep_[i] = r
TH = rep_[TH]
deg_ = (TH[:, 0] == TH[:, 1]) | (TH[:, 1] == TH[:, 2]) | (TH[:, 0] == TH[:, 2])
key = collections.Counter(tuple(sorted(f)) for f in TH)
dup = np.array([key[tuple(sorted(f))] > 1 for f in TH])
ar = np.zeros(len(TH))
print('TOPO welded verts', int((rep_[hsv] != hsv).sum()), 'collapsed faces', int(deg_.sum()), 'duplicate faces', int((dup & ~deg_).sum()))
TH = TH[~deg_ & ~dup]
E = collections.Counter()
for f in TH:
    for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])): E[(a, b)] += 1
bnd = [(a, b) for (a, b) in E if E[(b, a)] == 0]
nxt = {}
for a, b in bnd: nxt.setdefault(b, []).append(a)
used = set(); fills = []
for a, b in bnd:
    if (a, b) in used: continue
    loop = [a, b]; used.add((a, b)); cur = b; ok = True
    while True:
        cand = [x for (y, x) in [(e[0], e[1]) for e in bnd] if y == cur and (y, x) not in used]
        if not cand: ok = False; break
        x = cand[0]; used.add((cur, x))
        if x == loop[0]: break
        loop.append(x); cur = x
        if len(loop) > 8: ok = False; break
    if ok and 3 <= len(loop) <= 6:
        for i in range(1, len(loop) - 1): fills.append([loop[0], loop[i + 1], loop[i]])
print('TOPO filled faces', len(fills))
if fills: TH = np.vstack([TH, np.array(fills)])
bpy.ops.wm.read_factory_settings(use_empty=True)
vs, inv = np.unique(TH, return_inverse=True); t = inv.reshape(-1, 3)
fi = np.arange(len(TH))
me = bpy.data.meshes.new('g'); me.from_pydata(co[vs].tolist(), [], t.tolist()); me.update()
ob = bpy.data.objects.new('g', me); bpy.context.scene.collection.objects.link(ob)
me.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', vs.tolist()); me.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', fi.tolist())
P = co[vs]; cv = comp[vs]
# eyeballs: the head part's small components
hk = names.index('head'); par = np.arange(len(co))
def fd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in tri[comp[tri[:, 0]] == hk]:
    r = fd(a); par[fd(b)] = r; par[fd(c)] = r
hv = np.where(comp == hk)[0]; roots = np.array([fd(v) for v in hv]); big = np.bincount(roots).argmax()
eye = np.zeros(len(co), bool); eye[hv[roots != big]] = True
ev = eye[vs]
face = (cv == hk) & ~ev & (P[:, 1] < -0.035) & (P[:, 2] > 0.574) & (P[:, 2] < 0.742) & (np.abs(P[:, 0]) < 0.068)
groups = {'face': face, 'scalp': (cv == hk) & ~ev & ~face, 'eyes': ev}
if 'hair' in names:
    hp = names.index('hair'); groups['hair'] = (cv == hp) & (P[:, 2] >= 0.56); groups['hairback'] = (cv == hp) & (P[:, 2] < 0.56)
if 'ears' in names: groups['ears'] = cv == names.index('ears')
for nm, sel in groups.items():
    g = ob.vertex_groups.new(name=nm); g.add(np.where(sel)[0].tolist(), 1.0, 'REPLACE')
for o in bpy.data.objects: o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
rep = uv_atlas.unwrap(ob, charts='bones', min_segment=24, max_edge_stretch=8.0, max_density_ratio=4.0, group_factors={'face': 1.8, 'hairback': 0.6}, size=1024, fine=250, steps=0)
me = ob.data; uvd = me.uv_layers.active.data
vo = np.zeros(len(me.vertices), np.int32); me.attributes['vo'].data.foreach_get('value', vo)
fo = np.zeros(len(me.polygons), np.int32); me.attributes['fo'].data.foreach_get('value', fo)
corners = [[(int(vo[me.loops[l].vertex_index]), uvd[l].uv[0], uvd[l].uv[1]) for l in p.loop_indices] for p in me.polygons]
print('HEADUV', rep)
# ---- new npz: the old body set unchanged, the head set replaced
keep = O['mat'] == 0
pos = list(O['co']); uv = list(O['uv']); orig = list(O['orig']); part = list(O['comp'])
T = [list(x) for x in O['tri'][keep]]; mat = [0] * int(keep.sum()); inn = list(O['inner'][keep]) if 'inner' in O else None
V = {}
for f, cs in zip(fo, corners):
    row = []
    for vi, u, v in cs:
        k = (vi, round(u, 6), round(v, 6))
        if k not in V: V[k] = len(pos); pos.append(co[vi]); uv.append((u, v)); orig.append(vi); part.append(comp[vi])
        row.append(V[k])
    T.append(row); mat.append(1)
    if inn is not None: inn.append(False)
O.update(co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part))
if inn is not None: O['inner'] = np.array(inn)
O.pop('textures', None)
np.savez(OUT, **O); json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVHEAD done', len(pos), len(T))
