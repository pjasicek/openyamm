"""Sharp-texture UVs (uv_atlas.py) for the body. One 4K Meshy upload holds three runtime sets:
- Torso (torso, arms, hands, belt, emblem, spikes): bottom half of the square -> runtime 2048x1024;
- Head (head skin above the jaw, hair, horns, eyes, ears, fringe, mouth): top-left quarter -> runtime 1024x1024;
- Legs (hips down to the shoes): top-right quarter -> runtime 1024x1024.
Vertices are split at UV seams ('orig' = asm vertex). Never re-run after an upload went to Meshy.
Args: <asm npz> <body weights npz> <out npz> <report json>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, WF, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
BW = np.load(WF); W = BW['W']; wn = [str(x) for x in BW['names']]
def wsum(pred): return W[:, [i for i, n in enumerate(wn) if pred(n)]].sum(1)
headw = wsum(lambda n: n in ('Bip01 Head', 'Bip01 XhalfHead'))
legw = wsum(lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe0')))
fc = comp[tri[:, 0]]; isn = lambda *n: np.isin(fc, [names.index(x) for x in n])
fh = headw[tri].mean(1); fl = legw[tri].mean(1); fz = co[tri][:, :, 2].mean(1)
HEADF = isn('hair', 'horns', 'eyes', 'ears', 'fringe', 'mouth') | (isn('body') & (fh > 0.5))
LEGF = isn('body') & ~HEADF & (fl > 0.5) & (fz < 0.16)
TORF = ~HEADF & ~LEGF
FACT = {'hand': 1.4, 'face': 1.9, 'hairf': 0.65, 'horn': 0.8}
def group(fi, groups, **opts):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    vs, inv = np.unique(tri[fi], return_inverse=True); t = inv.reshape(-1, 3)
    me = bpy.data.meshes.new('g'); me.from_pydata(co[vs].tolist(), [], t.tolist()); me.update()
    ob = bpy.data.objects.new('g', me); bpy.context.scene.collection.objects.link(ob)
    me.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', vs.tolist())
    me.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', fi.tolist())
    for nm, sel in groups.items():
        g = ob.vertex_groups.new(name=nm); g.add(np.where(sel[vs])[0].tolist(), 1.0, 'REPLACE')
    for o in bpy.data.objects: o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    rep = uv_atlas.unwrap(ob, group_factors={k: v for k, v in FACT.items() if k in groups}, fine=250, steps=0, **opts)
    me = ob.data; uvd = me.uv_layers.active.data
    vo = np.zeros(len(me.vertices), np.int32); me.attributes['vo'].data.foreach_get('value', vo)
    fo = np.zeros(len(me.polygons), np.int32); me.attributes['fo'].data.foreach_get('value', fo)
    corners = [[(int(vo[me.loops[l].vertex_index]), uvd[l].uv[0], uvd[l].uv[1]) for l in p.loop_indices] for p in me.polygons]
    print('GROUP', len(me.polygons), rep)
    return fo, corners, rep
vb = lambda *n: np.isin(comp, [names.index(x) for x in n])
hand = vb('body') & (np.abs(co[:, 0]) > 0.40) & (co[:, 2] < 0.30)
face = vb('body', 'eyes', 'mouth') & (headw > 0.5) & (co[:, 1] < 0.06) & (co[:, 2] < 0.95)
rep = {}
fo_t, c_t, rep['torso'] = group(np.where(TORF)[0], {'hand': hand}, height_share=0.5, size=2048, max_cost=float(os.environ.get('TCOST', '2.0')), roundness=float(os.environ.get('TROUND', '0.5')))
fo_h, c_h, rep['head'] = group(np.where(HEADF)[0], {'face': face, 'hairf': vb('hair'), 'horn': vb('horns')}, size=1024)
fo_l, c_l, rep['legs'] = group(np.where(LEGF)[0], {}, size=1024)
# upload square: torso v 0..0.5 as packed (0..0.5), head u*0.5, v*0.5+0.5, legs u*0.5+0.5, v*0.5+0.5
V = {}; pos = []; uv = []; orig = []; T = []; mat = []; part = []
def emit(fo, corners, m, su, sv, ou, ov):
    for f, cs in zip(fo, corners):
        row = []
        for vi, u, v in cs:
            k = (vi, m, round(u, 6), round(v, 6))
            if k not in V:
                V[k] = len(pos); pos.append(co[vi]); uv.append((u * su + ou, v * sv + ov)); orig.append(vi); part.append(comp[vi])
            row.append(V[k])
        T.append(row); mat.append(m)
emit(fo_t, c_t, 0, 1.0, 1.0, 0.0, 0.0)
emit(fo_h, c_h, 1, 0.5, 0.5, 0.0, 0.5)
emit(fo_l, c_l, 2, 0.5, 0.5, 0.5, 0.5)
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part),
         names=np.array(names), matnames=np.array(['EboraTorso', 'EboraHead', 'EboraLegs']))
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVDONE', len(pos), len(T), 'faces torso/head/legs', int(TORF.sum()), int(HEADF.sum()), int(LEGF.sum()))
