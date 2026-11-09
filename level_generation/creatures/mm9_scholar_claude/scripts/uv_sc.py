"""Scholar: body set robe (stole, sleeves), legs, hands, jewellery (hands 1.4x, legs 0.5x); head set = face, eyes, hair + beard, cap (face 1.7x): one head colour per tier. (Wyrde original: head set = face, neck, hair,
circlet and hood (face 1.7x). From PF1's uv_pf.py.
Vertices split at UV seams. Never re-run after an upload went to Meshy. Args: <asm npz> <out npz> <report json>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]; inner = np.zeros(len(tri), bool)
BODY = ['robe', 'legs', 'hands', 'jewel']; HEAD = ['head', 'hair', 'cap']
fc = comp[tri[:, 0]]
FACT = {'hand': 1.4, 'face': 1.7, 'inner': 0.3, 'shin': 0.5}
def group(ns, groups, **opts):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fi = np.where(np.isin(fc, [names.index(n) for n in ns]))[0]
    vs, inv = np.unique(tri[fi], return_inverse=True); t = inv.reshape(-1, 3)
    me = bpy.data.meshes.new('g'); me.from_pydata(co[vs].tolist(), [], t.tolist()); me.update()
    ob = bpy.data.objects.new('g', me); bpy.context.scene.collection.objects.link(ob)
    me.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', vs.tolist()); me.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', fi.tolist())
    for nm, sel in groups.items():
        g = ob.vertex_groups.new(name=nm); g.add(np.where(sel[vs])[0].tolist(), 1.0, 'REPLACE')
    for o in bpy.data.objects: o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    rep = uv_atlas.unwrap(ob, group_factors={k: v for k, v in FACT.items() if k in groups}, fine=250, steps=0, **opts)
    me = ob.data; uvd = me.uv_layers.active.data
    vo = np.zeros(len(me.vertices), np.int32); me.attributes['vo'].data.foreach_get('value', vo)
    fo = np.zeros(len(me.polygons), np.int32); me.attributes['fo'].data.foreach_get('value', fo)
    corners = [[(int(vo[me.loops[l].vertex_index]), uvd[l].uv[0], uvd[l].uv[1]) for l in p.loop_indices] for p in me.polygons]
    print('GROUP', ns[0], len(me.polygons), rep); return fo, corners, rep
rep = {}
isb = lambda *n: np.isin(comp, [names.index(x) for x in n])
fo_b, c_b, rep['body'] = group(BODY, {'hand': isb('hands'), 'shin': isb('legs')}, size=2048)
face = isb('head') & (co[:, 1] < -0.02) & (np.abs(co[:, 0]) < 0.08) & (co[:, 2] > 0.64)
fo_h, c_h, rep['head'] = group(HEAD, {'face': face}, size=1024)
V = {}; pos = []; uv = []; orig = []; T = []; mat = []; part = []; inn = []
def emit(fo, corners, m):
    for f, cs in zip(fo, corners):
        row = []
        for vi, u, v in cs:
            k = (vi, m, round(u, 6), round(v, 6))
            if k not in V: V[k] = len(pos); pos.append(co[vi]); uv.append((u, v)); orig.append(vi); part.append(comp[vi])
            row.append(V[k])
        T.append(row); mat.append(m); inn.append(bool(inner[f]))
emit(fo_b, c_b, 0); emit(fo_h, c_h, 1)
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part), inner=np.array(inn), names=np.array(names), matnames=np.array(['Scholar', 'ScholarHead']))
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVDONE', len(pos), len(T))
