"""PF3 UVs (2026-11-02): the body set is PeasantF1's, copied row for row from F1's work/uv.npz (its layout, vertex splits and order); the head
set (head shell, ears, hood, the new veil and braids) is re-laid with uv_atlas.py into one 1K square (face 1.7x), because the veil and
braids do not fit into F1's head layout. The veil lining shares the outer sheet's UVs (vertex for vertex: the same linen, no atlas cost).
Vertices split at UV seams. Never re-run after the head upload went to Meshy.
Args: <F1 uv npz> <asm f3 npz> <out npz> <report json>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
F1, ASM, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
B = np.load(F1); A = np.load(ASM)
co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]; f3_inner = A['f3_inner']
fc = comp[tri[:, 0]]
n_old = len(B['orig']) and int(B['orig'].max()) + 1
# ---- body rows from F1 (material 0 faces and their vertices: F1 emitted the body first)
bm = B['mat'] == 0; bt = B['tri'][bm]; nb = int(bt.max()) + 1
assert (np.unique(bt) == np.arange(nb)).all(), 'F1 body vertices are not the leading rows'
assert np.allclose(B['co'][:nb], co[B['orig'][:nb]]), 'F1 body positions differ from the asm'
# ---- head group: head, ears(if any), scarf, veil (outer + rim, not the lining), braids
HEAD = [n for n in ('head', 'ears', 'scarf', 'veil', 'braids') if n in names]
hf = np.where(np.isin(fc, [names.index(n) for n in HEAD]) & ~f3_inner)[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
vs, inv = np.unique(tri[hf], return_inverse=True); t = inv.reshape(-1, 3)
me = bpy.data.meshes.new('g'); me.from_pydata(co[vs].tolist(), [], t.tolist()); me.update()
ob = bpy.data.objects.new('g', me); bpy.context.scene.collection.objects.link(ob)
me.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', vs.tolist()); me.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', hf.tolist())
g = ob.vertex_groups.new(name='face'); g.add(np.where(comp[vs] == names.index('head'))[0].tolist(), 1.0, 'REPLACE')
for o in bpy.data.objects: o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
rep = {'head': uv_atlas.unwrap(ob, group_factors={'face': 1.7}, fine=250, steps=0, size=1024)}
me = ob.data; uvd = me.uv_layers.active.data
vo = np.zeros(len(me.vertices), np.int32); me.attributes['vo'].data.foreach_get('value', vo)
fo = np.zeros(len(me.polygons), np.int32); me.attributes['fo'].data.foreach_get('value', fo)
corners = {int(fo[p.index]): [(int(vo[me.loops[l].vertex_index]), uvd[l].uv[0], uvd[l].uv[1]) for l in p.loop_indices] for p in me.polygons}
# ---- veil lining: corners take the outer twin's UV (asm: the lining's vertices follow the outer ones, same count)
kv = names.index('veil'); vv = np.where(comp == kv)[0]; v0 = vv.min()
lin = np.where((fc == kv) & f3_inner)[0]
outer_uv = {}
for f, cs in corners.items():
    for vi, u, v in cs:
        if comp[vi] == kv: outer_uv.setdefault(vi, (u, v))
# the outer sheet's vertex count: the lining starts where the f3_param rows repeat
par = A['f3_param'][vv]
n_out = next(i for i in range(1, len(par)) if np.allclose(par[i], par[0]) and i > 1)
for f in lin:
    corners[int(f)] = [(int(vi), *outer_uv[int(vi) - n_out]) for vi in tri[f]]
# ---- emit: F1 body rows verbatim, then the head set
pos = list(B['co'][:nb]); uv = list(B['uv'][:nb]); orig = list(B['orig'][:nb]); part = list(B['comp'][:nb])
T = list(bt); mat = [0] * len(bt); inn = list(B['inner'][bm])
V = {}
for f in sorted(corners):
    row = []
    for vi, u, v in corners[f]:
        k = (vi, round(u, 6), round(v, 6))
        if k not in V: V[k] = len(pos); pos.append(co[vi]); uv.append((u, v)); orig.append(vi); part.append(comp[vi])
        row.append(V[k])
    T.append(row); mat.append(1); inn.append(bool(f3_inner[f]))
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part),
         inner=np.array(inn), names=np.array(names), matnames=np.array(['PeasantF3', 'PeasantF3Head']))
rep.update(body_rows=int(nb), body_faces=int(len(bt)), head_faces=int(len(corners)), lining_faces=int(len(lin)), outer_veil_verts=int(n_out))
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVDONE', json.dumps(rep, default=float))
