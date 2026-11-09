"""LOD0 under 15k (PF3 second pass, 2026-11-02): the added veil and braids and F1's skirt lining (hidden inside the skirt) are decimated
by Blender's collapse decimation, which keeps UV seams and interpolates UVs, so the paid head paint and the body paint stay valid. Each part
is built welded by asm vertex (topology across UV seams), its loops carry the UVs, vertices shared with any other part are held (vertex
group weight 0), the face's `inner` flag rides along. Surviving vertices keep their asm index (`orig`), so weights stay; tweak_pf1.py
puts every row back on its asm position. F1's visible body (dress, skirt, head, hood, arms, hands, legs) is untouched.
Args: <uv npz in> <uv npz out> <report json> part=ratio ... [asm=<asm npz in>:<asm npz out>]
With asm=..., every surviving vertex of a decimated part becomes a new asm vertex at its decimated position (the collapse moves vertices and
interpolates the integer asm index, so neither can be trusted); weights_pf3.py then weights it by its part's rules."""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]; ASM = next((x.split('=', 1)[1] for x in a[3:] if x.startswith('asm=')), None)
RATIO = {k: float(v) for k, v in (s.split('=') for s in a[3:] if not s.startswith('asm='))}
if ASM: AIN, AOUT = ASM.split(':'); AS = dict(np.load(AIN)); asm_new = []; n_asm = len(AS['co'])
D = dict(np.load(IN)); co, tri, uv, orig, mat, comp, inner = D['co'], D['tri'], D['uv'], D['orig'], D['mat'], D['comp'], D['inner']
names = [str(x) for x in D['names']]; fc = comp[tri[:, 0]]
keep_f = np.ones(len(tri), bool); new_rows = []; new_faces = []; rep = {}
for part, ratio in RATIO.items():
    pi = names.index(part); fs = np.where(fc == pi)[0]; keep_f[fs] = False
    o_of = orig[tri[fs]]                                   # asm vertex per corner
    verts, inv = np.unique(o_of, return_inverse=True); ft = inv.reshape(-1, 3)
    pos = np.zeros((len(verts), 3)); pos[ft.ravel()] = co[tri[fs]].reshape(-1, 3)
    shared = np.isin(verts, orig[tri[fc != pi]].ravel())   # held: vertices other parts use too
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new(part); me.from_pydata(pos.tolist(), [], ft.tolist()); me.update()
    ul = me.uv_layers.new(name='UVMap'); ul.data.foreach_set('uv', uv[tri[fs]].reshape(-1, 2).ravel())
    me.attributes.new('orig', 'INT', 'POINT').data.foreach_set('value', verts.astype(int).tolist())
    me.attributes.new('inner', 'INT', 'FACE').data.foreach_set('value', inner[fs].astype(int).tolist())
    ob = bpy.data.objects.new(part, me); bpy.context.scene.collection.objects.link(ob)
    vg = ob.vertex_groups.new(name='free'); vg.add(np.where(~shared)[0].tolist(), 1.0, 'REPLACE')
    md = ob.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = ratio; md.vertex_group = 'free'
    md.use_collapse_triangulate = True; md.vertex_group_factor = 1.0
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier='dec')
    me = ob.data; n0 = len(fs)
    # the collapse interpolates integer attributes too, so a surviving vertex's asm index is taken as the nearest original vertex of the part
    _pv = np.array([v.co[:] for v in me.vertices]); _j = np.empty(len(_pv), np.int64); _d = np.empty(len(_pv))
    for _s in range(0, len(_pv), 512):
        _dd = np.linalg.norm(_pv[_s:_s + 512, None, :] - pos[None], axis=2); _j[_s:_s + 512] = _dd.argmin(1); _d[_s:_s + 512] = _dd.min(1)
    ov = verts[_j].astype(np.int64)
    if ASM:
        ov = n_asm + len(asm_new) + np.arange(len(_pv)); asm_new.extend([(tuple(v), pi) for v in _pv])
    rep.setdefault('snap_mm', {})[part] = round(float(_d.max()) * 1000, 2)
    fi = np.zeros(len(me.polygons), np.int64); me.attributes['inner'].data.foreach_get('value', fi)
    uvd = me.uv_layers['UVMap'].data
    for p in me.polygons:
        assert len(p.vertices) == 3
        new_faces.append(([(int(ov[me.loops[l].vertex_index]), tuple(np.round(uvd[l].uv, 7)), tuple(me.vertices[me.loops[l].vertex_index].co)) for l in p.loop_indices],
                          int(mat[fs[0]]), pi, bool(fi[p.index])))
    rep[part] = {'faces_before': int(n0), 'faces_after': len(me.polygons), 'held_vertices': int(shared.sum())}
# rebuild: kept faces and their rows first (row order kept), then the decimated parts
used = np.unique(tri[keep_f]); remap = -np.ones(len(co), np.int64); remap[used] = np.arange(len(used))
C = [co[used]]; UV = [uv[used]]; OR = [orig[used]]; CP = [comp[used]]
T = [remap[tri[keep_f]]]; M = [mat[keep_f]]; IN_ = [inner[keep_f]]
rows = {}; nc, nu, no, ncp, nt, nm, ni = [], [], [], [], [], [], []
base = len(used)
for corners, m, pi, fin in new_faces:
    r = []
    for o, u, p in corners:
        k = (o, u)
        if k not in rows:
            rows[k] = base + len(nc); nc.append(p); nu.append(u); no.append(o); ncp.append(pi)
        r.append(rows[k])
    nt.append(r); nm.append(m); ni.append(fin)
D.update(co=np.vstack(C + [np.array(nc)]), uv=np.vstack(UV + [np.array(nu)]), orig=np.r_[OR[0], np.array(no, np.int64)],
         comp=np.r_[CP[0], np.array(ncp, np.int64)], tri=np.vstack(T + [np.array(nt)]), mat=np.r_[M[0], np.array(nm)], inner=np.r_[IN_[0], np.array(ni, bool)])
np.savez(OUT, **D)
if ASM:
    nn = len(asm_new); AS['co'] = np.vstack([AS['co'], np.array([p for p, _ in asm_new])]); AS['comp'] = np.r_[AS['comp'], np.array([c for _, c in asm_new])]
    if 'f3_param' in AS: AS['f3_param'] = np.vstack([AS['f3_param'], np.full((nn, 2), -1.0)])
    np.savez(AOUT, **AS); rep['asm_vertices_added'] = nn
rep['total_faces'] = int(len(D['tri'])); json.dump(rep, open(REP, 'w'), indent=1); print('REDUCE', json.dumps(rep))
