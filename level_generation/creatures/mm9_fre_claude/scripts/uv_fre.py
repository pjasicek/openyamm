"""Fre UVs (2026-11-04, Blender): the BODY set is PeasantF4's paid layout row for row (work/f4/uv.npz, its asm indices mapped onto ours:
the body geometry is F4's), so only the HEAD set (head shell, F1's hidden old hood 0.3x, the hair cap, the braid) is re-laid with uv_atlas.py
(face 1.7x). Never re-run after the head upload went to Meshy. Extra args: <f4 asm npz> <f4 uv npz>. PF4 text follows. PF4 UVs (2026-11-02, Blender): both sets re-laid with uv_atlas.py on the PF4 asm (F1's body with the sleeve tubes, the new hood), since
both are repainted by Meshy. Body set (2K): dress, skirt, skirt lining (0.3x), legs (0.5x), arms + hands (1.4x), sleeves (outer, rims,
caps; caps 0.3x). Head set (1K): head shell (face 1.7x), F1's old hood (hidden skull, 0.3x), hood4 (outer and rim). Lining faces (hood4,
sleeve4 linings) take their outer twin face's UVs per corner (the same cloth inside, no atlas cost) and are not unwrapped.
Vertices split at UV seams. Never re-run after an upload went to Meshy. Args: <asm npz> <out npz> <report json>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, REP, A4_, U4_ = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
f4_inner, twin_f, twin_v = D['f4_inner'], D['f4_twin_face'], D['f4_twin_v']
fc = comp[tri[:, 0]]
isf = lambda *n: np.isin(fc, [names.index(x) for x in n])
lining_f = twin_f >= 0                                           # hood/sleeve linings (twins)
BODY_F = isf('dress', 'skirt', 'lining', 'legs', 'hands', 'sleeve4') & ~lining_f
HEAD_F = isf('head', 'scarf', 'hood4', 'braids') & ~lining_f
inner_flag = isf('lining') | (f4_inner & ~lining_f) | isf('scarf')    # F1's skirt lining, the sleeve caps, the hidden old hood: 0.3x
FACT = {'hand': 1.4, 'face': 1.7, 'inner': 0.3, 'shin': 0.5}
def group(fi, groups_f, size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    vs, inv = np.unique(tri[fi], return_inverse=True); t = inv.reshape(-1, 3)
    me = bpy.data.meshes.new('g'); me.from_pydata(co[vs].tolist(), [], t.tolist()); me.update()
    ob = bpy.data.objects.new('g', me); bpy.context.scene.collection.objects.link(ob)
    me.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', vs.tolist()); me.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', fi.tolist())
    for nm, fsel in groups_f.items():
        vsel = np.zeros(len(co), bool); vsel[np.unique(tri[fi[fsel[fi]]])] = True
        g = ob.vertex_groups.new(name=nm); g.add(np.where(vsel[vs])[0].tolist(), 1.0, 'REPLACE')
    for o in bpy.data.objects: o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    rep = uv_atlas.unwrap(ob, group_factors={k: v for k, v in FACT.items() if k in groups_f}, fine=250, steps=0, size=size)
    me = ob.data; uvd = me.uv_layers.active.data
    vo = np.zeros(len(me.vertices), np.int32); me.attributes['vo'].data.foreach_get('value', vo)
    fo = np.zeros(len(me.polygons), np.int32); me.attributes['fo'].data.foreach_get('value', fo)
    corners = {int(fo[p.index]): [(int(vo[me.loops[l].vertex_index]), uvd[l].uv[0], uvd[l].uv[1]) for l in p.loop_indices] for p in me.polygons}
    print('GROUP', len(me.polygons), json.dumps(rep, default=float)[:400]); return corners, rep
rep = {}
# body: F4's corners. F4 asm index -> ours by position (F4's hood rows dropped, every other row kept in order); faces by vertex triple
A4 = np.load(A4_); U4 = np.load(U4_)
names4 = [str(x) for x in A4['names']]; keep4 = A4['comp'] != names4.index('hood4')
map4 = -np.ones(len(A4['co']), int); map4[keep4] = np.arange(keep4.sum())
ftri = {tuple(sorted(t)): i for i, t in enumerate(tri)}
cb = {}; miss = 0
for f4 in np.where(U4['mat'] == 0)[0]:
    rows = U4['tri'][f4]; o4 = U4['orig'][rows]; o = map4[o4]
    i = ftri.get(tuple(sorted(o)))
    if i is None or not BODY_F[i] and not lining_f[i]: miss += 1; continue
    cb[i] = [(int(o[k]), float(U4['uv'][rows[k], 0]), float(U4['uv'][rows[k], 1])) for k in range(3)]
print('BODY from F4', len(cb), 'missing', miss, 'body faces here', int(BODY_F.sum()))
rep['body'] = dict(from_f4=len(cb), missing=miss)
ch, rep['head'] = group(np.where(HEAD_F)[0], {'face': isf('head'), 'inner': inner_flag}, 1024)
# linings: each corner takes the UV its outer twin vertex has in the twin face
for corners, sel in ((cb, BODY_F), (ch, HEAD_F)):
    pass
lin = np.where(lining_f)[0]; nl = 0
for f in lin:
    src = int(twin_f[f]); base = cb if src in cb else ch
    uvmap = {vi: (u, v) for vi, u, v in base[src]}
    base[int(f)] = [(int(vi), *uvmap[int(twin_v[vi])]) for vi in tri[f]]; nl += 1
V = {}; pos = []; uv = []; orig = []; T = []; mat = []; part = []; inn = []
for m, corners in ((0, cb), (1, ch)):
    for f in sorted(corners):
        row = []
        for vi, u, v in corners[f]:
            k = (vi, m, round(u, 6), round(v, 6))
            if k not in V: V[k] = len(pos); pos.append(co[vi]); uv.append((u, v)); orig.append(vi); part.append(comp[vi])
            row.append(V[k])
        T.append(row); mat.append(m); inn.append(bool(isf('lining')[f] or f4_inner[f]))
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part), inner=np.array(inn),
         names=np.array(names), matnames=np.array(['Fre', 'FreHead']))
rep.update(lining_faces=nl, rows=len(pos), faces=len(T))
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVDONE', len(pos), len(T), 'linings', nl)
