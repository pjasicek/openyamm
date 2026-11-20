import bpy,bmesh,sys,os,json
BODY_KIND = os.environ['KEPT_BODY']
assert BODY_KIND in ('male', 'female')
BODY_ID = 'm' if BODY_KIND == 'male' else 'f'
BODY_VERSION = 'v2' if BODY_ID == 'm' else 'v1'
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/f'work/kept_{BODY_ID}_clean_{BODY_VERSION}.blend'))
body=bpy.data.objects['Body'];BASE=bmesh.new();BASE.from_mesh(body.data)
M=json.loads((P/f'work/kept_{BODY_ID}_meshy_joints.json').read_text())['joints']
R=json.loads((P/f'work/kept_{BODY_ID}_ring_joints.json').read_text())['joints']
J={k:np.array(v) for k,v in M.items()};report={}
def rings(p, n):
    """Closed loops of the mesh cut by the plane (p, n): list of (centroid, perimeter, points)."""
    bm = BASE.copy()
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
        pts = np.array([tuple(x.co) for x in comp])
        if len(pts) < 4:
            continue
        ordered = [comp[0]]; left = set(comp[1:])
        while left:
            nxt = next((y for y in adj[ordered[-1]] if y in left), None)
            if nxt is None:
                break
            ordered.append(nxt); left.discard(nxt)
        op = np.array([tuple(x.co) for x in ordered])
        per = float(np.linalg.norm(np.diff(np.vstack([op, op[:1]]), axis=0), axis=1).sum())
        out.append((pts.mean(0), per, pts))
    bm.free()
    return out


def nearest_ring(p, n, target):
    rs = rings(p, n)
    if not rs:
        return None
    return min(rs, key=lambda r: np.linalg.norm(r[0] - target))



for side in ('L','R'):
    if BODY_ID=='f':
        J[side+'_Hand']=np.array(R[side+'_Hand'])
    else:
        wrist=J[side+'_Hand'];axis=wrist-J[side+'_Forearm'];axis/=np.linalg.norm(axis)
        candidates=[nearest_ring(wrist+axis*t,axis,wrist+axis*t) for t in np.linspace(-.025,.025,21)]
        candidates=[r for r in candidates if r is not None and np.linalg.norm(r[0]-wrist)<.04]
        assert candidates, side
        J[side+'_Hand']=min(candidates,key=lambda r:r[1])[0]
    ankle=J[side+'_Foot'];ring=nearest_ring(ankle,(0,0,1),ankle)
    assert ring is not None and np.linalg.norm(ring[0]-ankle)<.06
    J[side+'_Foot']=ring[0]
    report[side]={'wrist_shift_mm':float(np.linalg.norm(J[side+'_Hand']-M[side+'_Hand'])*1000),
                  'ankle_shift_mm':float(np.linalg.norm(J[side+'_Foot']-ankle)*1000),
                  'ankle_height_m':float(ankle[2]),'rejected_boot_neck_height_m':R[side+'_Foot'][2]}
assert all(np.isfinite(v).all() for v in J.values())
out={'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report,'status':'composed_pending_xray_review'}
(P/f'work/{BODY_KIND}/joints_final.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
