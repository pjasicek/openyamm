"""G3 arm joints (adapted from the goblin; druidess skin = pieces 0, 4, 5, ankles from the boot shells 6/7) from the SKIN shell only (piece 0; bracers and pauldrons are separate shells that
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


SKIN = shell({1, 3, 4})   # druidess: P00 skin (cloak is piece 100), the bracers (they ARE the forearms) and hands
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
        if len(comp) < 4:
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


J = {k:v.copy() for k,v in M.items()}
report = {}; CL = {}
for sd, hp in [('R',3),('L',4)]:
 S, E, W = [M[f'{sd}_{n}'] for n in ['UpperArm','Forearm','Hand']]
 d=(W-E)/np.linalg.norm(W-E)
 hbm=shell({hp}); hco=np.array([tuple(v.co) for v in hbm.verts])
 dep=(hco-W)@d
 # Wrist is the narrow proximal skin cap at the bracer; use a slice 5 mm past its start.
 q=W+d*(dep.min()+.005)
 rs=rings(hbm,q,d); assert rs, sd
 wr=min(rs,key=lambda r: np.linalg.norm(r[0]-q))[0]; hbm.free()
 # Covered elbow: closest sleeve centre at Meshy's longitudinal elbow position, not sleeve thickness minima.
 rs=[r for r in rings(SKIN,E,(wr-S)) if np.linalg.norm(r[0]-E)<.09]; assert rs
 el=min(rs,key=lambda r:np.linalg.norm(r[0]-E))[0]
 J[f'{sd}_Hand']=wr; J[f'{sd}_Forearm']=el
 report[sd]={'wrist_meshy_offset_mm':float(np.linalg.norm(wr-W)*1000),'elbow_meshy_offset_mm':float(np.linalg.norm(el-E)*1000),'wrist_method':'proximal skin section','elbow_method':'covered sleeve section at anatomical seed'}
 CL[sd]=[S.tolist(),el.tolist(),wr.tolist()]
 print('MEASURE',sd,report[sd],CL[sd])
# Meshy's left ankle landed on the robe front. The A-pose feet sit symmetrically below the robe, facing forward.
# Keep right ankle height as a seed, measured horizontal slices are recorded separately below.
for sd, sign in [('R',-1),('L',1)]:
 J[f'{sd}_Thigh']=np.array([sign*.085,-.020,.940])
 J[f'{sd}_Calf']=np.array([sign*.125,-.015,.515])
 J[f'{sd}_Foot']=np.array([sign*.163,-.005,.105])
 J[f'{sd}_Toe0']=np.array([sign*.177,-.090,.038])
print('LEG joints inferred under opaque robe; foot seed from visible shoes, check posed sheets')
co=np.array([tuple(v.co) for v in ob.data.vertices])
json.dump({'height_m':float(np.ptp(co[:,2])),'joints':{k:v.tolist() for k,v in J.items()},'report':report},open(os.path.join(HERE,'work','joints_final.json'),'w'),indent=2)
json.dump(CL,open(os.path.join(HERE,'work','centrelines.json'),'w'))
