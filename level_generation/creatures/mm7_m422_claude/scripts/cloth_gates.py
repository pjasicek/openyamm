"""Cloth gates for the coat skirt (garment 2, robe chains) and the cape (garment 10, sheet chains), every half frame of
every clip (adapted from mm6_thf_claude cloak_poke.py / cloak_stretch.py to this rig's garments):
- stretch: p99 and max edge ratio (posed / rest) of each cloth, and the widest opening (posed - rest edge length, cm);
- skirt poke: leg/boot vertices (garment 15) above the posed skirt hem of their sector (+5 cm) whose horizontal ray
  outward from the pelvis axis meets no skirt face (the leg shows through the closed coat skirt); depth = distance
  to the skirt along the inward ray (cm; a hit further than 10 cm means the ray left through an opening and is not counted);
- cape poke: coat, skirt, collar and leg vertices behind the trunk (in the chest heading) inside the cape's posed
  angular span and above its posed hem in that sector whose ray straight back meets no cape face.
Poke tests are skipped on frames where the chest is tilted more than 45 deg or the pelvis is below 80 % of its rest
height (sitting / lying in Death); sleeves (arm weight >= 0.3) and trousers above the skirt top are not tested.
Writes review/cloth_<tag>.json. Args: -- <blend> <tag> [clip ...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, clips = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
gv = np.array([x.value for x in me.attributes['garment'].data])
rest = np.array([v.co[:] for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
cloth = {'skirt': 2, 'cape': 10}
CE = {k: E[(gv[E[:, 0]] == g) & (gv[E[:, 1]] == g)] for k, g in cloth.items()}
RL = {k: np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1) for k, e in CE.items()}
CF = {k: [tuple(p.vertices) for p in me.polygons if all(gv[i] == g for i in p.vertices)] for k, g in cloth.items()}
gid = {g.index: g.name for g in body.vertex_groups}
armw = np.array([sum(e.weight for e in v.groups if any(t in gid[e.group] for t in ('UpperArm', 'Forearm', 'Hand', 'Clavicle')))
                 for v in me.vertices])
SKIRT_TOP = float(np.percentile(rest[gv == 2, 2], 99)) - 0.03
LEG = np.where((gv == 15) & (rest[:, 2] < SKIRT_TOP))[0]                # trousers inside the coat above the skirt are not tested
BACKV = np.where(np.isin(gv, (1, 2, 6, 15)) & (armw < 0.3))[0]          # sleeves may leave the cape legitimately
PEL0 = rig.data.bones['B_Pelvis'].head_local.z
clips = clips or [x for x in ('Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Fidget') if x in bpy.data.actions]
NSEC = 24


def sector(ang):
    return ((ang + math.pi) / (2 * math.pi) * NSEC).astype(int) % NSEC


res = {}
for cl in clips:
    act = bpy.data.actions[cl]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    w = {}

    def rec(k, v, f):
        if k not in w or v > w[k]['value']:
            w[k] = {'value': round(float(v), 4), 'frame': round(float(f), 1)}
    for f in np.arange(f0, f1 + 1e-6, 0.5):
        sc.frame_set(int(f), subframe=float(f - int(f)))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
        for k, e in CE.items():
            L = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1); r = L / np.maximum(RL[k], 1e-6)
            rec(f'{k}_p99', np.percentile(r, 99), f); rec(f'{k}_max', r.max(), f)
            rec(f'{k}_open_cm', (L - RL[k]).max() * 100, f)
        C = rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix
        Rc = C.to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
        up = Rc @ Vector((0, 0, 1))
        pz = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation.z
        if up.z < math.cos(math.radians(45)) or pz < 0.8 * PEL0:          # lying or sitting (Death)
            continue
        back = Rc @ Vector((0, 1, 0)); back.z = 0; back.normalize()
        pel = np.array((rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation)
        # skirt poke
        T = BVHTree.FromPolygons([tuple(p) for p in P], CF['skirt'])
        sk = np.unique(np.array(CF['skirt']).ravel())
        ang = np.arctan2(P[sk, 0] - pel[0], P[sk, 1] - pel[1]); hem = np.full(NSEC, 9.0)
        np.minimum.at(hem, sector(ang), P[sk, 2])
        la = np.arctan2(P[LEG, 0] - pel[0], P[LEG, 1] - pel[1])
        cand = LEG[P[LEG, 2] > hem[sector(la)] + 0.05]
        n_out, deep, worst_i = 0, 0.0, -1
        for i in cand:
            p = Vector(P[i]); d = Vector((p.x - pel[0], p.y - pel[1], 0))
            if d.length < 1e-4:
                continue
            d.normalize()
            if T.ray_cast(p + d * 1e-4, d, 0.5)[0] is None:
                hit = T.ray_cast(p, -d, 0.5)
                dd = hit[3] if hit[0] is not None else 0.0
                if dd > 0.10:          # the inward ray crossed the whole body: the leg is not at the near skirt wall but
                    continue           # behind an opening (the back vent under the cape), not poking through cloth
                n_out += 1
                if dd > deep:
                    deep = dd; worst_i = i
        rec('skirt_poke_n', n_out, f); rec('skirt_poke_cm', deep * 100, f)
        if os.environ.get('DEBUG') and worst_i >= 0 and deep > 0.05:
            print('POKE', cl, f, 'vert', worst_i, 'rest', np.round(rest[worst_i], 3), 'posed', np.round(P[worst_i], 3), 'pel', np.round(pel, 3), 'depth', round(deep, 3))
        # cape poke
        T2 = BVHTree.FromPolygons([tuple(p) for p in P], CF['cape'])
        cv = np.unique(np.array(CF['cape']).ravel())
        fwd2 = np.array([back.x, back.y]); side = np.array([back.y, -back.x])
        rel = P[:, :2] - pel[:2]
        ca = np.arctan2(rel[cv] @ side, rel[cv] @ fwd2)
        lo, hi = np.percentile(ca, [3, 97]); chem = np.full(NSEC, 9.0)
        np.minimum.at(chem, sector(ca), P[cv, 2])
        ba = np.arctan2(rel[BACKV] @ side, rel[BACKV] @ fwd2)
        sel = BACKV[(rel[BACKV] @ fwd2 > 0.02) & (ba > lo + 0.1) & (ba < hi - 0.1) & (P[BACKV, 2] > chem[sector(ba)] + 0.03)
                    & (P[BACKV, 2] < 1.35 + pel[2] - 1.0)]
        n2 = 0
        for i in sel:
            if T2.ray_cast(Vector(P[i]) + back * 1e-4, back, 0.6)[0] is None:
                n2 += 1
        rec('cape_poke_n', n2, f)
    res[cl] = w
    print('CLOTH', cl.ljust(9), ' '.join(f"{k}={v['value']:.2f}@{v['frame']:.1f}" for k, v in w.items()))
json.dump(res, open(os.path.join(HERE, 'review', f'cloth_{tag}.json'), 'w'), indent=1)
