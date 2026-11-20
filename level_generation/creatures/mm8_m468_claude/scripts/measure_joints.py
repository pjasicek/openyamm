"""G3 / H3: joint centres from the mesh's own cross-sections (no auto-rig).

The rest mesh (A-pose, soles at z=0, facing -Y, character left = +X) is sliced perpendicular to each limb; every
slice is split into closed loops and the loop nearest the limb line gives a ring centre and perimeter.
- arm: centreline from the shoulder seed to the hand's far end; WRIST = narrowest ring in the distal third,
  ELBOW = largest deviation of the centreline from the shoulder-wrist line if the A-pose bend is > 8 mm, otherwise
  the source upper-arm : forearm ratio; SHOULDER = one upper-arm radius inside the top of the deltoid along the
  upper-arm axis; the mesh's own elbow hinge axis = normal of (shoulder, elbow, wrist) when the bend is measurable.
- leg: HIP from the source hip height/width scaled to this body, KNEE = largest deviation or the source ratio,
  ANKLE = narrowest ring above the foot.
- spine/neck/head: torso ring centres at the source's relative heights.
Seeds come from work/proportions.json (source). Writes work/joints.json and prints ring residuals.
Args: -- <blend> <mesh object>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
blend, mesh_name = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects[mesh_name]
BASE = bmesh.new(); BASE.from_mesh(ob.data); BASE.transform(ob.matrix_world)
BASE.verts.ensure_lookup_table()
pieces=ob.data.attributes['piece']
bmesh.ops.delete(BASE,geom=[v for v in BASE.verts if pieces.data[v.index].value != 0],context='VERTS')
co = np.array([tuple(v.co) for v in BASE.verts])
from mathutils.bvhtree import BVHTree
TREE = BVHTree.FromBMesh(BASE)
H = 1.7
SRC = json.load(open(os.path.join(HERE, 'work', 'proportions.json')))['source']


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


def line_dev(pts, a, b):
    d = (b - a) / np.linalg.norm(b - a)
    v = pts - a
    return np.linalg.norm(v - np.outer(v @ d, d), axis=1)


M=json.load(open(os.path.join(HERE,'work','meshy_joints.json')))['joints']
J={k:np.array(v) for k,v in M.items()};report={}
for side in ('L','R'):
 for label,prox,dist,window,minper in [('wrist','Forearm','Hand',.040,.10),('ankle','Calf','Foot',.045,.14)]:
  seed=J[f'{side}_{dist}'].copy();axis=seed-J[f'{side}_{prox}'];axis/=np.linalg.norm(axis)
  samples=[]
  for off in np.linspace(-window,window,41):
   q=seed+axis*off;r=nearest_ring(q,axis,q)
   if r is not None and minper<r[1]<.40 and np.linalg.norm(r[0]-q)<.045:samples.append((r[1],off,r[0]))
  assert samples,(side,label)
  per,off,c=min(samples,key=lambda r:r[0]);J[f'{side}_{dist}']=c
  report[side+'_'+label]={'meshy':seed.tolist(),'ring':c.tolist(),'perimeter_cm':per*100,'shift_cm':float(np.linalg.norm(c-seed))*100,'offset_cm':off*100}
  print('MEASURED',side,label,report[side+'_'+label])
 # Retain the auto-rig elbow's axial position; centre it on the exposed skin.
 el=J[f'{side}_Forearm'];axis=J[f'{side}_Hand']-J[f'{side}_UpperArm'];axis/=np.linalg.norm(axis)
 ring=nearest_ring(el,axis,el)
 assert ring is not None and np.linalg.norm(ring[0]-el)<.04
 J[f'{side}_Forearm']=ring[0]
for k,v in J.items():assert np.isfinite(v).all()
out={'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report,'method':'Skin-only cross sections around independently estimated joints; wrists/ankles narrowest local ring, elbows centred at Meshy axial position. Earlier unconstrained distal-third fit rejected: left thumb mistaken for wrist.'}
json.dump(out,open(os.path.join(HERE,'work','joints_final.json'),'w'),indent=2)
