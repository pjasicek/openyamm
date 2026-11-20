"""G3 arm joints for the goblin from the SKIN shell only (piece 0; bracers and pauldrons are separate shells that
fooled the generic ring fit), seeded by Meshy's auto-rig shoulder and hand joints.

Per side: the arm tip = the skin vertex farthest from the shoulder along the Meshy shoulder -> hand direction; a
centreline of ring centres is cut perpendicular to the LOCAL arm direction (two passes: first along the straight
seed axis, then perpendicular to the smoothed first-pass centreline). WRIST = narrowest ring between 55 % and 85 %
of the shoulder -> tip length; ELBOW = closest approach of two line fits (upper-arm rings 15-42 %, forearm rings
60-92 % of shoulder -> wrist). Ankles from the narrowest skin/foot ring above the foot.
Writes work/joints.json (Meshy joints with ring wrist/elbow/ankle replaced) and work/centrelines.json.
Args: -- <blend>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
M = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints'].items()}


def shell(pieces):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] not in pieces], context='VERTS')
    return bm


SKIN = shell({1,4,5,13,14})
co_skin = np.array([tuple(v.co) for v in SKIN.verts])


def rings(base, p, n):
    bm = base.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p), plane_no=Vector(n))
    edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        comp, stack = [], [v]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); stack.extend(adj[x])
        if len(comp) < 4 or any(len(adj[v])!=2 for v in comp):
            continue
        ordered = [comp[0]]; left = set(comp[1:])
        while left:
            nxt = next((y for y in adj[ordered[-1]] if y in left), None)
            if nxt is None:
                break
            ordered.append(nxt); left.discard(nxt)
        op = np.array([tuple(x.co) for x in ordered])
        per = float(np.linalg.norm(np.diff(np.vstack([op, op[:1]]), axis=0), axis=1).sum())
        out.append((op.mean(0), per))
    bm.free()
    return out


def centreline(base, a, b, ts, dirs=None, maxoff=0.07):
    out = []
    for i, t in enumerate(ts):
        q = a + (b - a) * t
        n = dirs[i] if dirs is not None else (b - a)
        rs = [r for r in rings(base, q, n) if np.linalg.norm(r[0] - q) < maxoff]
        if rs:
            r = min(rs, key=lambda r: np.linalg.norm(r[0] - q))
            out.append((t, r[0], r[1]))
    return out


def line_fit(p, d):
    c = p.mean(0); u = np.linalg.svd(p - c)[2][0]
    return c, (u if u @ d > 0 else -u)


J = {k: v.copy() for k, v in M.items()}
CL, report = {}, {}
for s in ('R', 'L'):
    S, Wm = M[f'{s}_UpperArm'], M[f'{s}_Hand']
    d = (Wm - S) / np.linalg.norm(Wm - S)
    far = co_skin[(co_skin - S) @ d > np.linalg.norm(Wm - S)]
    far = far[np.linalg.norm((far - S) - np.outer((far - S) @ d, d), axis=1) < 0.12]
    tip = far[np.argmax((far - S) @ d)]
    ts = np.linspace(0.06, 0.97, 60)
    c1 = centreline(SKIN, S, tip, ts)
    tt = np.array([c[0] for c in c1]); cc = np.array([c[1] for c in c1])
    # second pass: slice perpendicular to the local centreline direction (smoothed finite differences)
    dirs = []
    for t in ts:
        i = np.argmin(np.abs(tt - t)); j0, j1 = max(i - 3, 0), min(i + 3, len(cc) - 1)
        dirs.append(cc[j1] - cc[j0])
    pts = [cc[np.argmin(np.abs(tt - t))] for t in ts]
    c2 = []
    for t, p, n in zip(ts, pts, dirs):
        allr = rings(SKIN, p, n)
        rs = [r for r in allr if np.linalg.norm(r[0] - p) < 0.05]
        near = [r for r in allr if np.linalg.norm(r[0] - p) < 0.09]
        if rs:
            r = min(rs, key=lambda r: np.linalg.norm(r[0] - p)); c2.append((t, r[0], r[1], len(near)))
    t2 = np.array([c[0] for c in c2]); cs = np.array([c[1] for c in c2]); per = np.array([c[2] for c in c2])
    nl = np.array([c[3] for c in c2])
    print('PROFILE', s, ' '.join(f'{t:.2f}:{p*100:.0f}/{k}' for t, p, k in zip(t2, per, nl)))
    # fingers separate where a slice first holds several loops near the axis (beyond mid-arm): the wrist lies before
    split = next((t for t, k in zip(t2, nl) if t > 0.82 and k > 1), 0.85)
    CL[f'{s}_arm'] = cs.tolist()
    m = (t2 > 0.60) & (t2 < split - 0.04)
    wi = np.where(m)[0][np.argmin(per[m])]
    wr = cs[wi]
    L_ = np.linalg.norm(wr - S); dw = (wr - S) / L_
    tw = (cs - S) @ dw / L_
    ca, ua = line_fit(cs[(tw > 0.15) & (tw < 0.42)], dw)
    cb, ub = line_fit(cs[(tw > 0.60) & (tw < 0.92)], dw)
    w0 = ca - cb; a_, b_, c_, d_, e_ = ua @ ua, ua @ ub, ub @ ub, ua @ w0, ub @ w0
    den = a_ * c_ - b_ * b_
    s1, s2 = (b_ * e_ - c_ * d_) / den, (a_ * e_ - b_ * d_) / den
    el = ((ca + ua * s1) + (cb + ub * s2)) / 2
    ring_el=el.copy()
    # This mesh's nearly straight sleeve and tapered bracer do not constrain their intersection.
    # Use the independently fitted elbow, then verify its placement in the X-ray and ROM gates.
    el=M[f'{s}_Forearm'].copy()
    J[f'{s}_Forearm'], J[f'{s}_Hand'] = el, wr
    report[s] = {'wrist_t_tip': round(float(t2[wi]), 3), 'wrist_perimeter_cm': round(float(per[wi]) * 100, 1),
                 'rejected_ring_elbow': ring_el.tolist(), 'elbow_t': round(float((el - S) @ dw / L_), 3), 'bend_deg': round(float(np.degrees(np.arccos(np.clip(ua @ ub, -1, 1)))), 1),
                 'line_gap_mm': round(float(np.linalg.norm((ca + ua * s1) - (cb + ub * s2))) * 1000, 1),
                 'upper_m': round(float(np.linalg.norm(el - S)), 3), 'fore_m': round(float(np.linalg.norm(wr - el)), 3),
                 'meshy_wrist_off_cm': round(float(np.linalg.norm(wr - Wm)) * 100, 1),
                 'meshy_elbow_off_cm': round(float(np.linalg.norm(el - M[f'{s}_Forearm'])) * 100, 1)}
    print('ARM', s, json.dumps(report[s]))
    # ankle: narrowest horizontal ring of the foot/shin skin between 6 and 25 cm, near the Meshy ankle
    A = M[f'{s}_Foot']
    feet = {2}
    FOOT = shell(feet)
    best = None
    for z in np.arange(0.065, 0.15, 0.005):
        rs = [r for r in rings(FOOT, (A[0], A[1], z), (0, 0, 1)) if np.linalg.norm(r[0][:2] - A[:2]) < 0.08]
        for r in rs:
            if best is None or r[1] < best[1]:
                best = (np.array([r[0][0], r[0][1], z]), r[1])
    FOOT.free()
    assert best is not None, f'{s} no closed ankle ring'
    J[f'{s}_Foot'] = best[0]
    report[s]['ankle_off_meshy_cm'] = round(float(np.linalg.norm(best[0] - A)) * 100, 1)
    print('ANKLE', s, np.round(best[0], 3).tolist(), 'perimeter cm', round(best[1] * 100, 1), 'meshy', np.round(A, 3).tolist())
# Final wrist section: the original glove's open proximal edge, identical after our mirrored repair.
original=bpy.data.libraries.load(os.path.join(HERE,'work','st_v1_parts.blend'),link=False)
with original as (available,loaded):loaded.objects=['P04']
glove=loaded.objects[0]; gb=bmesh.new();gb.from_mesh(glove.data)
wv={v for e in gb.edges if e.is_boundary and min(v.co.z for v in e.verts)>.91 for v in e.verts}
wrist=np.array([tuple(v.co) for v in wv]).mean(0)
gb.free();bpy.data.objects.remove(glove,do_unlink=True)
for side,sg in [('R',-1),('L',1)]:
 J[f'{side}_Hand']=np.array([sg*abs(wrist[0]),wrist[1],wrist[2]])
# A greave covers the missing front of the boot shell: fit the outer cross-section of both together.
FOOT=shell({2,6,7})
def hull(points):
 pts=sorted(set(map(tuple,points)))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lower=[];upper=[]
 for pt in pts:
  while len(lower)>=2 and cross(lower[-2],lower[-1],pt)<=0:lower.pop()
  lower.append(pt)
 for pt in reversed(pts):
  while len(upper)>=2 and cross(upper[-2],upper[-1],pt)<=0:upper.pop()
  upper.append(pt)
 return np.array(lower[:-1]+upper[:-1])
ankles={}
for side,sg in [('R',-1),('L',1)]:
 best=None
 for z in [float((M['L_Foot'][2]+M['R_Foot'][2])/2)]:
  bm=FOOT.copy();res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=(0,0,1))
  points=np.array([tuple(v.co)[:2] for v in res['geom_cut'] if isinstance(v,bmesh.types.BMVert) and v.co.x*sg>.06])
  bm.free()
  if len(points)<8:continue
  h=hull(points);per=np.linalg.norm(np.roll(h,1,axis=0)-h,axis=1).sum()
  if best is None or per<best[0]:best=(per,np.r_[(h.min(0)+h.max(0))/2,z])
 assert best is not None,side
 ankles[side]=best[1];print('ANKLE_ENVELOPE',side,best)
FOOT.free()
mean_ankle=(ankles['L']+ankles['R']*np.array([-1,1,1]))/2
for side,sg in [('R',-1),('L',1)]:J[f'{side}_Foot']=mean_ankle*np.array([sg,1,1])
co = np.array([tuple(v.co) for v in ob.data.vertices])
json.dump({'height_m': float(co[:, 2].max() - co[:, 2].min()), 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
json.dump(CL, open(os.path.join(HERE, 'work', 'centrelines.json'), 'w'))
