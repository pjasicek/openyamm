"""Sharp-texture UVs (claude_shared/uv_atlas.py) of the body atlas on the frozen body mesh (work/asm3.npz; the staff is not in it).
Never re-run after an upload went to Meshy: uv_assemble.py builds the full uv npz from this and the staff (work/asm4.npz).
Material 0 'LichKing': one square atlas for every body part, plus the staff shaft (charts kept free in the upload, painted procedurally after) and
the skull (factor 0.15: an occluder for Meshy's projection only; at runtime the skull keeps the Lich's own UVs). Coat lining faces (inner side of
the coat shell) at 0.4. Material 1 'LichKingHead': the skull and the staff's skull on the Lich's head set (UVs carried from mm9_lich_claude).
Writes uv npz: co, tri, uv (Blender v up), orig, mat, comp, names, matnames, lining (per face), and the body-atlas skull uv for the upload.
Writes per body-atlas face: fo (face index in asm3), corners (vertex, u, v) x3, lining. Args: <asm3 npz> <lich skull npz> <out npz> <report json>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, SK, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
fc = comp[tri[:, 0]]
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
cen = co[tri].mean(1)
rad = cen[:, :2] - [0.0, 0.02]; rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
lining = (fc == names.index('torso')) & (cen[:, 2] < 0.93) & ((fn[:, :2] * rad).sum(1) < -0.2)
print('lining faces', int(lining.sum()))
BODY = [n for n in names if n not in ('sskull', 'staff')]
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
FACT = {'hand': 1.5, 'crown': 1.35, 'inner': 0.4, 'skull': 0.15, 'staff': 0.7}
isb = lambda *n: np.isin(comp, [names.index(x) for x in n])
# vertex groups are per vertex: the lining vertices are those only on lining faces
lin_v = np.zeros(len(co), bool); lin_v[np.unique(tri[lining])] = True; lin_v[np.unique(tri[~lining & (fc == names.index('torso'))])] = False
fi = np.where(np.isin(fc, [names.index(n) for n in BODY]))[0]
fo, cs, rep = group(fi, {'hand': isb('hands'), 'crown': isb('crown'), 'inner': lin_v, 'skull': isb('skull')}, size=2048, margin_px=3)
np.savez(OUT, fo=np.array(fo), corners=np.array(cs, dtype=float), lining=lining[fo])
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('UVDONE', len(fo))
