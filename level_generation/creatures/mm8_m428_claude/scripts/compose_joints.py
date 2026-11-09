"""G3: compose the joint set from two independent estimates (Meshy auto-rig and our own mesh measurements).

The dress hides the legs, and Meshy put its knees 17 cm in front of the leg mesh (inside the skirt shell), and its
shoulders, clavicles and spine are asymmetric. So:
- legs: horizontal rings of the hidden leg piece (piece 1) only. Hip height = crotch (lowest single ring) + 0.075 m;
  ankle = narrowest ring between 8 and 25 cm; knee at the source thigh:shin ratio on the hip-ankle line, moved to
  the ring centre at that height; toe = shoe front at sole height.
- wrists: narrowest ring of each hand piece (pieces 3/4) along the forearm axis (Meshy elbow -> fingertip).
- shoulders and elbows: Meshy, mirrored to the mean of both sides (x symmetric, same y/z).
- spine: source heights mapped piecewise-linearly (source pelvis -> our pelvis, source clavicle -> our shoulder
  height), centred on the torso ring at each height; neck/head from the source offsets above the clavicle scaled
  by height.
Writes work/joints_final.json. Args: none."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/step1.blend'))
ob = bpy.data.objects['Body']; me = ob.data
PV = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', PV)
M = json.loads((P / 'work/meshy_joints.json').read_text())['joints']
S = json.loads((P / 'work/source_rest.json').read_text())
H = 1.7; k = H / 2.5766


def piece_bm(ids):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if PV[v.index] not in ids], context='VERTS')
    return bm


def rings(bm0, p, n):
    bm = bm0.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p), plane_no=Vector(n))
    edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in edges:
        a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        comp, st = [], [v]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st.extend(adj[x])
        if len(comp) < 4:
            continue
        cs = set(comp)
        per = sum((e.verts[0].co - e.verts[1].co).length for e in edges if e.verts[0] in cs)
        out.append((np.array([tuple(x.co) for x in comp]).mean(0), per))
    bm.free()
    return out


J = {}
legs = piece_bm({1})
zs = np.arange(0.05, 1.05, 0.01)
lev = [(z, rings(legs, (0, 0, z), (0, 0, 1))) for z in zs]
two = [z for z, r in lev if len([x for x in r if x[1] > 0.08]) >= 2]
crotch = max(two)
hip_z = crotch + 0.035                      # Meshy's own hip estimate: 0.932
print('LEGS crotch z', round(crotch, 3), 'hip z', round(hip_z, 3))
for side, sg in (('L', 1), ('R', -1)):
    def leg_ring(z):
        rs = [r for r in rings(legs, (0, 0, z), (0, 0, 1)) if r[0][0] * sg > 0.02 and r[1] > 0.05]
        return min(rs, key=lambda r: r[1]) if rs else None
    hr = leg_ring(crotch - 0.02)
    hip = np.array([hr[0][0], hr[0][1], hip_z])
    cand = [(z, leg_ring(z)) for z in np.arange(0.08, 0.26, 0.005)]
    cand = [(z, r) for z, r in cand if r is not None]
    za, ra = min(cand, key=lambda zr: zr[1][1])
    ankle = ra[0]
    th, sh = (np.linalg.norm(np.array(S[f'B_{side}_{a}']['head']) - np.array(S[f'B_{side}_{b}']['head']))
              for a, b in (('Thigh', 'Calf'), ('Calf', 'Foot')))
    kz = hip[2] + (ankle[2] - hip[2]) * th / (th + sh)
    kr = leg_ring(kz)
    knee = np.array([kr[0][0], kr[0][1], kz])
    shoe = np.array([tuple(v.co) for v in me.vertices if PV[v.index] == 1 and v.co.z < 0.05 and v.co.x * sg > 0])
    toe = shoe[np.argmin(shoe[:, 1])]
    toe = np.array([ankle[0] + (toe[0] - ankle[0]) * 0.6, ankle[1] + (toe[1] - ankle[1]) * 0.6, 0.02])
    J[f'{side}_Thigh'], J[f'{side}_Calf'], J[f'{side}_Foot'], J[f'{side}_Toe0'] = hip, knee, ankle, toe
    print('LEG', side, 'ankle perimeter cm', round(ra[1] * 100, 1), 'knee ring', round(kr[1] * 100, 1))
# symmetric legs
for b in ('Thigh', 'Calf', 'Foot', 'Toe0'):
    l, r = J[f'L_{b}'], J[f'R_{b}']
    m = (l + r * np.array([-1, 1, 1])) / 2
    J[f'L_{b}'], J[f'R_{b}'] = m, m * np.array([-1, 1, 1])
# arms: Meshy shoulder/elbow mirrored
for b in ('Clavicle', 'UpperArm', 'Forearm'):
    l, r = np.array(M[f'L_{b}']), np.array(M[f'R_{b}'])
    m = (l + r * np.array([-1, 1, 1])) / 2
    J[f'L_{b}'], J[f'R_{b}'] = m, m * np.array([-1, 1, 1])
for side, pid in (('L', 3), ('R', 4)):
    hand = piece_bm({pid})
    pts = np.array([tuple(v.co) for v in hand.verts])
    el = J[f'{side}_Forearm']
    tip = pts[np.argmax(np.linalg.norm(pts - el, axis=1))]
    ax = (tip - el) / np.linalg.norm(tip - el)
    best = None
    for t in np.linspace(0.45, 0.75, 31):
        q = el + (tip - el) * t
        rs = rings(hand, q, ax)
        if not rs:
            continue
        r = min(rs, key=lambda r: np.linalg.norm(r[0] - q))
        if np.linalg.norm(r[0] - q) < 0.05 and (best is None or r[1] < best[1][1]):
            best = (t, r)
    J[f'{side}_Hand'] = best[1][0]
    print('WRIST', side, 't', round(best[0], 3), 'perimeter cm', round(best[1][1] * 100, 1), np.round(best[1][0], 3))
# the mirrored Meshy shoulders sit at the back surface in profile: centre them in the deltoid depth
for sd, sg in (('L', 1), ('R', -1)):
    J[f'{sd}_UpperArm'][1] = 0.02; J[f'{sd}_Forearm'][1] = 0.012
l, r = J['L_Hand'], J['R_Hand']; m = (l + r * np.array([-1, 1, 1])) / 2
J['L_Hand'], J['R_Hand'] = m, m * np.array([-1, 1, 1])
# spine
torso = piece_bm({0})
src_pel, src_cla = S['B_Pelvis']['head'][2], S['B_R_Clavicle']['head'][2]
our_pel = hip_z; our_cla = float(J['R_UpperArm'][2])
def ring_centre(z):
    rs = [r for r in rings(torso, (0, 0, z), (0, 0, 1)) if abs(r[0][0]) < 0.05]
    r = max(rs, key=lambda r: r[1]) if rs else None
    return r[0] if r is not None else np.array([0.0, 0.0, z])
for b in ('Pelvis', 'Spine', 'Spine1', 'Spine2'):
    sz = S[f'B_{b}']['head'][2]
    z = our_pel + (sz - src_pel) / (src_cla - src_pel) * (our_cla - our_pel)
    J[b] = np.array([0.0, 0.0, z])
# torso centre line (the widest ring at chest height includes the sleeves): pelvis on the hip line, the chest a
# little forward (bust), measured neck ring at the neck
J['Pelvis'][1] = J['L_Thigh'][1]; J['Spine'][1] = -0.01; J['Spine1'][1] = -0.015; J['Spine2'][1] = -0.01
# head joint (skull base) at mouth height (mouth pieces 17/18), neck base 8 cm lower (the source offsets from the
# clavicle put the head joint at eye height on this short-necked body)
mouth = float(np.mean([v.co.z for v in me.vertices if PV[v.index] in (17, 18)]))
neck_r = [r for r in rings(torso, (0, 0, mouth - 0.08), (0, 0, 1)) if abs(r[0][0]) < 0.03]
ny = float(min(neck_r, key=lambda r: r[1])[0][1]) if neck_r else -0.02
J['Neck'] = np.array([0.0, ny, mouth - 0.08]); J['Head'] = np.array([0.0, ny + 0.01, mouth])
print('HEAD mouth z', round(mouth, 3), 'neck y', round(ny, 3))
J['L_Clavicle'] = np.array([0.03, -0.01, our_cla - 0.01]); J['R_Clavicle'] = J['L_Clavicle'] * np.array([-1, 1, 1])
out = {'height_m': H, 'joints': {k_: [round(float(x), 5) for x in v] for k_, v in J.items()},
       'selection': 'compose_joints.py: legs from the hidden leg rings, wrists from hand-piece rings, Meshy shoulders '
                    'and elbows mirrored, spine on source heights mapped to our pelvis and shoulder heights.'}
(P / 'work/joints_final.json').write_text(json.dumps(out, indent=2) + '\n')
for k_, v in out['joints'].items():
    print('J', k_, v)
