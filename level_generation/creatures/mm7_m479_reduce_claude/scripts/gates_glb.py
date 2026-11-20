"""The production Treant gates (../mm7_m479_claude/scripts/gates.py) on an exported GLB's LOD0 (mesh node M479), every
frame of every clip at 30 fps:
  floor     lowest posed vertex (target >= -0.015 m);
  stretch   largest edge length / rest length, with the worst vertex's dominant bone (Death/Dead reported only);
  limbs     clearance between bone segments of different crown sectors and the Spire (rig only: identical for the
            same rig and clips, recomputed here as the production gate measured it);
  mouth     closed mouth (Standing): lower-lip top above the lowest upper-tooth tip, and tooth front behind lip front,
            within |x| < 0.15 m;
  strands   (added) the largest distance between any two vertices that coincide in the rest pose (split seams, welded
            UV seams) over every frame: touching strand pieces must move together, 0 = no tear.
Labels (lower lip piece 15, upper teeth part 1) come from the production master by nearest rest vertex
(work/master_pieces.npz), then the majority label of each connected piece (new vertices of a decimated tooth).
Usage: blender -b -P gates_glb.py -- <glb> <label>  -> work/gates_<label>.json"""
import bpy, sys, os, json, itertools
import numpy as np
from mathutils import kdtree
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = bpy.data.objects['M479']; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); me = body.data
LIMB_MIN = 0.12
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
m = np.load(os.path.join(HERE, 'work', 'master_pieces.npz'))
T = kdtree.KDTree(len(m['co']))
for i, c in enumerate(m['co']):
    T.insert(c, i)
T.balance(); nn = np.array([T.find(c)[1] for c in rest]); pv = m['piece'][nn]; pa = m['part'][nn]
E = np.array([tuple(e.vertices) for e in me.edges]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
vn = [g.name for g in body.vertex_groups]
dom = np.array([vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
lip = pv == 15
T2 = kdtree.KDTree(len(rest))
for i, c in enumerate(rest):
    T2.insert(c, i)
T2.balance()
pairs_co = np.array(sorted({(i, j) for i, c in enumerate(rest) for _, j, _ in T2.find_range(c, 1e-6) if j > i}), int).reshape(-1, 2)
# labels per connected piece (majority of the nearest master labels), so a new vertex of a decimated tooth takes its
# tooth's label instead of a neighbouring piece's
par = np.arange(len(rest))
def find(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for a, b in list(E) + list(pairs_co):
    ra, rb = find(int(a)), find(int(b))
    if ra != rb:
        par[ra] = rb
comp = np.array([find(i) for i in range(len(rest))])
for c in np.unique(comp):
    ids = comp == c
    pv[ids] = np.bincount(pv[ids] - pv.min()).argmax() + pv.min() if pv[ids].min() >= 0 else pv[ids]
    pa[ids] = np.bincount(pa[ids]).argmax()
lip = pv == 15
segs = [b.name for b in rig.pose.bones if b.name.startswith('Limb')] + ['Spire']


def seg_dist(a0, a1, b0, b1):
    best = 1e9
    for t in np.linspace(0, 1, 9):
        p = a0 + (a1 - a0) * t; d = b1 - b0
        u = np.clip((p - b0) @ d / max(d @ d, 1e-9), 0, 1); best = min(best, np.linalg.norm(p - (b0 + d * u)))
    return best


def bone_segs():
    return {n: (np.array(rig.matrix_world @ rig.pose.bones[n].head), np.array(rig.matrix_world @ rig.pose.bones[n].tail))
            for n in segs}


pairs = [(a, b) for a, b in itertools.combinations(segs, 2) if a.split('_')[0] != b.split('_')[0]]
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
S0 = bone_segs(); rest_d = {p: seg_dist(*S0[p[0]], *S0[p[1]]) for p in pairs}
report = {'triangles': sum(len(p.vertices) - 2 for p in me.polygons), 'coincident_pairs': int(len(pairs_co))}
for act in ('Standing', 'Attack', 'Hit', 'Death', 'Dead'):
    A = bpy.data.actions[next(a.name for a in bpy.data.actions if a.name.startswith(act) and not a.name.startswith(act + '_') or a.name == act)]
    rig.animation_data.action = A
    if len(A.slots):
        rig.animation_data.action_slot = A.slots[0]
    f0, f1 = (int(round(x)) for x in A.frame_range)
    floor = (9, 0); stretch = (0, 0, ''); limb = (9, None, 0, 0); mouth = None; tear = (0.0, 0)
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); mm = ev.to_mesh()
        P = np.empty(len(mm.vertices) * 3); mm.vertices.foreach_get('co', P); ev.to_mesh_clear(); P = P.reshape(-1, 3)
        P = P @ np.array(body.matrix_world)[:3, :3].T + np.array(body.matrix_world)[:3, 3]
        z = float(P[:, 2].min())
        if z < floor[0]:
            floor = (z, f)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        i = int(np.argmax(r))
        if r[i] > stretch[0]:
            stretch = (float(r[i]), f, dom[E[i, 0]])
        if len(pairs_co):
            t = float(np.linalg.norm(P[pairs_co[:, 0]] - P[pairs_co[:, 1]], axis=1).max())
            if t > tear[0]:
                tear = (t, f)
        if act not in ('Death', 'Dead'):
            S = bone_segs()
            for p in pairs:
                d = seg_dist(*S[p[0]], *S[p[1]]); lim = min(LIMB_MIN, 0.8 * rest_d[p]); margin = d - lim
                if margin < limb[0]:
                    limb = (margin, p, d, rest_d[p])
        if act == 'Standing':
            centre = np.abs(P[:, 0]) < 0.15
            tip = P[(pa == 1) & centre][:, 2].min(); liptop = P[lip & centre][:, 2].max()
            front_lip = P[lip & centre][:, 1].min(); tooth_y = P[(pa == 1) & centre][:, 1].min()
            v = (float(liptop - tip), float(tooth_y - front_lip))
            mouth = v if mouth is None or v[0] < mouth[0] else mouth
    rep = {'frames': f1 - f0 + 1, 'floor_min_z': round(floor[0], 4), 'floor_frame': floor[1],
           'max_edge_stretch': round(stretch[0], 2), 'stretch_frame': stretch[1], 'stretch_bone': stretch[2],
           'coincident_max_gap_mm': round(tear[0] * 1000, 3)}
    if act not in ('Death', 'Dead'):
        rep['limb_clearance_margin'] = round(limb[0], 3)
        rep['limb_closest_pair'] = list(limb[1]) if limb[1] else None
        rep['limb_closest_d'] = round(limb[2], 3); rep['limb_pair_rest_d'] = round(limb[3], 3)
    if mouth:
        rep['closed_mouth_lip_over_tooth_tip_m'] = round(mouth[0], 3); rep['tooth_behind_lip_front_m'] = round(mouth[1], 3)
    report[act] = rep
    print('GATE', label, act, json.dumps(rep), flush=True)
json.dump(report, open(os.path.join(HERE, 'work', f'gates_{label}.json'), 'w'), indent=1)
print('GATES', label, 'triangles', report['triangles'], 'coincident pairs', report['coincident_pairs'])
