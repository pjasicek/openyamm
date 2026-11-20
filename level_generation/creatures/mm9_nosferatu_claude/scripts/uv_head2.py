"""Head set UVs again (the head paint is a free projection, the body's paid layout stays): larger merged charts, gentler density factors. Writes work/uv_v2.npz. Args: <asm npz> <uv_v1 npz> <out npz>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, UV1, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
U = dict(np.load(UV1))
HEAD = ['head', 'eyes', 'teeth', 'plug']; fc = comp[tri[:, 0]]
isb = lambda *n: np.isin(comp, [names.index(x) for x in n])
fi = np.where(np.isin(fc, [names.index(n) for n in HEAD]))[0]
vs, inv = np.unique(tri[fi], return_inverse=True); t = inv.reshape(-1, 3)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('g'); me.from_pydata(co[vs].tolist(), [], t.tolist()); me.update()
ob = bpy.data.objects.new('g', me); bpy.context.scene.collection.objects.link(ob)
me.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', vs.tolist())
sel = {'face': isb('head', 'eyes', 'teeth') & (co[:, 1] < -0.04) & (np.abs(co[:, 0]) < 0.1), 'ear': isb('head') & (np.abs(co[:, 0]) > 0.105), 'back': isb('head') & (co[:, 1] > 0.04)}
for nm, s in sel.items():
    g = ob.vertex_groups.new(name=nm); g.add(np.where(s[vs])[0].tolist(), 1.0, 'REPLACE')
for o in bpy.data.objects: o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
rep = uv_atlas.unwrap(ob, group_factors={'face': 1.45, 'ear': 0.85, 'back': 0.8}, fine=250, steps=0, size=1024, merge_below=int(os.environ.get('MERGE', '32')), max_cost=float(os.environ.get('MAXC', '6')))
print('GROUP head', rep)
me = ob.data; uvd = me.uv_layers.active.data
vo = np.zeros(len(me.vertices), np.int32); me.attributes['vo'].data.foreach_get('value', vo)
keep = U['mat'] == 0; bv = np.unique(U['tri'][keep]); remap = -np.ones(len(U['co']), int); remap[bv] = np.arange(len(bv))
pos = U['co'][bv].tolist(); uv = U['uv'][bv].tolist(); orig = U['orig'][bv].tolist(); part = U['comp'][bv].tolist(); T = remap[U['tri'][keep]].tolist(); mat = [0] * len(T)
V = {}
for p in me.polygons:
    row = []
    for l in p.loop_indices:
        vi = int(vo[me.loops[l].vertex_index]); u, v_ = uvd[l].uv
        k = (vi, round(u, 6), round(v_, 6))
        if k not in V:
            V[k] = len(pos); pos.append(co[vi].tolist()); uv.append((u, v_)); orig.append(vi); part.append(int(comp[vi]))
        row.append(V[k])
    T.append(row); mat.append(1)
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part), names=U['names'], matnames=U['matnames'])
print('UV2', len(pos), len(T))
