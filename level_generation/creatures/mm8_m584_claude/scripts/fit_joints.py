"""Fit wrist and ankle centres from closed skin cross-sections around the Meshy estimates."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from pathlib import Path
blend, mesh_name = sys.argv[sys.argv.index('--') + 1:]
HERE = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects[mesh_name]
BASE = bmesh.new(); BASE.from_mesh(ob.data); BASE.transform(ob.matrix_world)
BASE.verts.ensure_lookup_table()
bmesh.ops.delete(BASE, geom=[v for v in BASE.verts if ob.data.attributes['piece'].data[v.index].value not in (0,1)], context='VERTS')
co = np.array([tuple(v.co) for v in BASE.verts])
H = float(co[:,2].max()-co[:,2].min())
M = json.loads((HERE/'work/meshy_joints.json').read_text())['joints']
J = {k:np.array(v) for k,v in M.items()}
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
        if len(pts) < 4 or any(len(adj[x]) != 2 for x in comp):
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


report = {}
for side in ('R','L'):
    for distal, proximal, span in (('Hand','Forearm',0.035),('Foot','Calf',0.03)):
        name=f'{side}_{distal}'; seed=J[name].copy()
        axis=seed-J[f'{side}_{proximal}'];axis/=np.linalg.norm(axis)
        candidates=[]
        for d in np.linspace(-span,span,29):
            p=seed+axis*d
            r=nearest_ring(p,axis,p)
            if r is not None and np.linalg.norm(r[0]-p)<0.04:
                candidates.append((r[1],r[0],d))
        assert candidates, name
        per,centre,d=min(candidates,key=lambda r:r[0])
        assert per>0.12, (name,per)
        J[name]=centre
        report[name]={'perimeter_cm':float(per*100),'seed_shift_cm':float(np.linalg.norm(centre-seed)*100),'axial_shift_cm':float(d*100)}
    # Centre the elbow at the joint estimate's axial station; avoid confusing muscle bulges with the hinge.
    seed=J[f'{side}_Forearm'].copy()
    axis=J[f'{side}_Hand']-J[f'{side}_UpperArm'];axis/=np.linalg.norm(axis)
    ring=nearest_ring(seed,axis,seed)
    assert ring is not None and np.linalg.norm(ring[0]-seed)<0.06
    J[f'{side}_Forearm']=ring[0]

for k,v in J.items():
    assert np.isfinite(v).all(),k
out={'height_m':H,'joints':{k:v.tolist() for k,v in J.items()},'report':report}
(HERE/'work/joints_final.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('JOINT_RING_FIT',json.dumps(report))
BASE.free()
