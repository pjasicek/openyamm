"""D-118 numeric gates on every clip of work/anim_v1.blend (or the blend named after --), every frame:
  floor    lowest vertex (cm, world) and lowest core vertex (body, head, thighs; playbook target >= -1.5 cm)
  rise     how far the hind-leg pieces rise above their rest top in the Body bone's frame (cm; the thighs over the
           back were +20..+30; gate <= 6)
  stretch  largest elongation of one hind-leg edge (cm; the torn lobes of the first build reach 9-45; gate <= 6)
  tongue   how far the tongue reaches outside the body piece in clips where it is kept in (Standing, Walking,
           Running, Hit, Death, Dead; cm; the resting tongue sits 3.5 cm deep in the lip crease, so the gate is <= 4)
  over     how far the highest hind-leg vertex rises above the back over the hips (body frame, the rest back top;
           cm; gate <= 0: the thighs never show over the back)
  The rise and over gates apply to the upright clips only (Death and Dead splay the legs on purpose).
Prints one GATE line per clip and writes review/repair_gates.json."""
import bpy, bmesh, os, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
blend = a[0] if a else 'anim_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
rig = bpy.data.objects['Toad_Rig']; mesh = bpy.data.objects['Toad']; tongue = bpy.data.objects['Tongue']
me = mesh.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
NV = len(me.vertices)
comp = np.full(NV, -1); nc = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = nc
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0:
                comp[o.index] = nc; st.append(o)
    nc += 1
names = [g.name for g in mesh.vertex_groups]
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
body_k = int(np.argmax(np.bincount(comp)))
legs = []
for k in range(nc):
    idx = np.where(comp == k)[0]
    if np.mean([n.endswith(('_L', '_R')) and n.startswith(('Thigh', 'Shin', 'Foot', 'Toes')) for n in dom[idx]]) > 0.5:
        legs.append(idx)
leg = np.concatenate(legs)
legset = np.zeros(NV, bool); legset[leg] = True
edges = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges if legset[e.verts[0].index]])
rest = np.array([v.co[:] for v in me.vertices])
rest_len = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
LIMB = np.array([n.startswith(('Hand', 'Toes', 'Foot', 'ForeArm')) for n in dom])
body_rest = rig.data.bones['Body'].matrix_local
leg_top = rest[leg, 2].max()
bodyv = np.where(comp == body_k)[0]
back_top = rest[bodyv][rest[bodyv, 1] > 0.0, 2].max()     # the back over the hips, rest
KEEP_IN = {'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Dead'}
sc = bpy.context.scene
out = {}
for act in [x for x in bpy.data.actions if x.use_fake_user]:
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    r = {'low': 9, 'core_low': 9, 'rise': -9, 'over': -9, 'stretch': 0, 'tongue_out': 0, 'worst': {}}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = mesh.evaluated_get(dg); m = ev.to_mesh()
        co = np.empty(NV * 3); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        Mw = np.array(mesh.matrix_world)
        cw = co @ Mw[:3, :3].T + Mw[:3, 3]
        low = cw[:, 2].min(); core = cw[~LIMB, 2].min()
        # hind legs in the Body bone's rest frame
        pb = rig.pose.bones['Body'].matrix
        to_rest = np.array(body_rest @ pb.inverted())
        lr = co[leg] @ to_rest[:3, :3].T + to_rest[:3, 3]
        rise = lr[:, 2].max() - leg_top
        over = lr[:, 2].max() - back_top
        plen = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1)
        st = (plen - rest_len).max()                    # largest elongation of one edge (m)
        tout = 0
        if act.name in KEEP_IN:
            bvh = BVHTree.FromPolygons([v.co.copy() for v in m.vertices],
                                       [p.vertices[:] for p in m.polygons if comp[p.vertices[0]] == body_k])
            tev = tongue.evaluated_get(dg).to_mesh()
            for v in tev.vertices:
                hit = bvh.find_nearest(v.co)
                if hit[0] is not None:
                    tout = max(tout, (v.co - hit[0]).dot(hit[1]))
            tongue.evaluated_get(dg).to_mesh_clear()
        ev.to_mesh_clear()
        for key, val, better in (('low', low, min), ('core_low', core, min), ('rise', rise, max),
                                 ('stretch', st, max), ('tongue_out', tout, max), ('over', over, max)):
            if better(r[key], val) == val and val != r[key]:
                r['worst'][key] = f
            r[key] = better(r[key], val)
    res = {'low_cm': round(r['low'] * 100, 2), 'core_low_cm': round(r['core_low'] * 100, 2),
           'rise_cm': round(r['rise'] * 100, 1), 'over_cm': round(float(r['over']) * 100, 1), 'stretch_cm': round(float(r['stretch']) * 100, 1),
           'tongue_out_cm': round(float(r['tongue_out']) * 100, 2), 'worst_frame': r['worst']}
    ok = (res['core_low_cm'] >= -1.5 and res['low_cm'] >= -1.5 and res['stretch_cm'] <= 6
          and (res['over_cm'] <= 0 or act.name in ('Death', 'Dead')) and res['tongue_out_cm'] <= 4)
    res['pass'] = bool(ok)
    out[act.name] = res
    print('GATE', act.name, 'PASS' if ok else 'FAIL', {k: (float(v) if isinstance(v, np.floating) else v)
                                                        for k, v in res.items()}, flush=True)
json.dump(out, open(os.path.join(HERE, 'review', 'repair_gates.json' if blend == 'anim_v1.blend'
                                 else f'repair_gates_{os.path.splitext(blend)[0]}.json'), 'w'), indent=1)
