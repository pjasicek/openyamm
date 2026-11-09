"""Sharp-texture UVs (uv_atlas.py) on the frozen mesh. Upper set (torso, yokes, pauldrons, belt, buckle, hands) in the top half of the square, lower set (legs, boots, shoes, greaves, flaps, panels, bracers: they differ per tier too) in the
bottom half: one Meshy 4K upload, and at runtime two 2048x1024 images so a tier can own only the lower half. Head set (head, crown, eyes) in its own square. Vertices split at UV seams.
Never re-run after an upload went to Meshy. Args: <asm npz> <out npz> <report json>"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
UP = ['torso', 'yokeF', 'yokeB', 'pauldrons', 'belt', 'buckle', 'hands']; LOW = ['legs', 'boots', 'shoes', 'greaves', 'flapF', 'flapB', 'panelF', 'panelB', 'bracers']; HEAD = ['head', 'crown', 'eyes']
fc = comp[tri[:, 0]]
def group(ns, groups, **opts):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fi = np.where(np.isin(fc, [names.index(n) for n in ns]))[0]
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
    corners = []
    for p in me.polygons:
        corners.append([(int(vo[me.loops[l].vertex_index]), uvd[l].uv[0], uvd[l].uv[1]) for l in p.loop_indices])
    print('GROUP', ns[0], len(me.polygons), rep)
    return fo, corners, rep
FACT = {'hand': 1.5, 'face': 1.7, 'flap': 0.55, 'inner': 0.6}
rep = {}
isb = lambda *n: np.isin(comp, [names.index(x) for x in n])
hand = isb('hands')
fo_u, c_u, rep['up'] = group(UP, {'hand': hand}, height_share=0.5, size=2048)
fo_l, c_l, rep['low'] = group(LOW, {}, height_share=0.5, size=2048)
face = isb('head', 'eyes') & (co[:, 1] < 0.03) & (co[:, 2] > 1.66)
flap = isb('head') & (co[:, 1] > 0.045)
fo_h, c_h, rep['head'] = group(HEAD, {'face': face, 'flap': flap}, size=1024)
# rows: mat 0 up, 1 low, 2 head
V = {}; pos = []; uv = []; orig = []; T = []; mat = []; part = []
def emit(fo, corners, m, off):
    for f, cs in zip(fo, corners):
        row = []
        for vi, u, v in cs:
            k = (vi, m, round(u, 6), round(v, 6))
            if k not in V:
                V[k] = len(pos); pos.append(co[vi]); uv.append((u, v + off)); orig.append(vi); part.append(comp[vi])
            row.append(V[k])
        T.append(row); mat.append(m)
emit(fo_u, c_u, 0, 0.5); emit(fo_l, c_l, 1, 0.0); emit(fo_h, c_h, 2, 0.0)
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part), names=np.array(names), matnames=np.array(['SorcererUp', 'SorcererLow', 'SorcererHead']))
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVDONE', len(pos), len(T))
