import bpy,bmesh,sys,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices])
pv=np.array([d.value for d in me.attributes['piece'].data])
M=json.loads((P/'work/meshy_joints.json').read_text())['joints']
J={k:np.array(v,dtype=float) for k,v in M.items()}
BASE=bmesh.new();BASE.from_mesh(me)
BASE.verts.ensure_lookup_table()
# Only actual limb/hand shells and boots; no pauldron, skirt, hair or cuff shell.
bmesh.ops.delete(BASE,geom=[v for v in BASE.verts if pv[v.index] not in (0,5,7,8,12,14)],context='VERTS')
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



report={};centrelines={}
for side,pid in [('L',7),('R',8)]:
    # The hand is a separate open shell with one wrist boundary.
    bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index]!=pid],context='VERTS')
    rim=[e for e in bm.edges if e.is_boundary]
    assert 8<=len(rim)<=30,(side,len(rim))
    length=sum(e.calc_length() for e in rim)
    wrist=sum(((e.verts[0].co+e.verts[1].co)*.5*e.calc_length() for e in rim),Vector())/length
    J[f'{side}_Hand']=np.array(wrist);bm.free()
    sh=J[f'{side}_UpperArm'];el=J[f'{side}_Forearm'];wr=J[f'{side}_Hand']
    axis=(wr-sh)/np.linalg.norm(wr-sh)
    samples=[]
    for t in np.linspace(.1,.95,35):
        seed=sh+(wr-sh)*t;r=nearest_ring(seed,axis,seed)
        if r is not None and np.linalg.norm(r[0]-seed)<.10:
            samples.append(r[0])
    centrelines[side]=np.array(samples).tolist()
    r=nearest_ring(el,axis,el)
    assert r is not None
    # Keep the independent Meshy elbow position along the arm, centre it on the skin ring.
    projected=r[0]+axis*np.dot(el-r[0],axis)
    assert np.linalg.norm(projected-el)<.06
    J[f'{side}_Forearm']=projected
    foot=J[f'{side}_Foot'];r=nearest_ring(foot,np.array((0,0,1)),foot)
    assert r is not None and np.linalg.norm(r[0]-foot)<.06
    J[f'{side}_Foot']=r[0]
    report[side]={'wrist_boundary_edges':len(rim),'wrist_move_cm':float(np.linalg.norm(wr-M[f'{side}_Hand'])*100),'elbow_move_cm':float(np.linalg.norm(projected-el)*100),'ankle_move_cm':float(np.linalg.norm(r[0]-foot)*100)}
# The generated body is symmetric to within small service noise.
for name in ('Clavicle','UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0'):
    a,b=J['L_'+name],J['R_'+name]
    avg=(a+b*np.array((-1,1,1)))*.5
    J['L_'+name]=avg;J['R_'+name]=avg*np.array((-1,1,1))
for name in ('Pelvis','Spine','Spine1','Spine2','Neck','Head'):J[name][0]=0
J['Neck']=np.array([0,.005,1.065])
J['Head']=np.array([0,.015,1.112])
report['head_correction']='Meshy followed the beard; pivot moved beneath the skull at the lower ear height, neck above the chest.'
out={'height_m':1.4,'joints':{k:v.tolist() for k,v in J.items()},'report':report}
(P/'work/joints_final.json').write_text(json.dumps(out,indent=2))
(P/'work/centrelines.json').write_text(json.dumps(centrelines,indent=2))
print('JOINTS',json.dumps(report))
BASE.free()
