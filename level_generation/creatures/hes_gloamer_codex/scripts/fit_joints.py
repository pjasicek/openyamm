"""Compare Meshy's estimate with skin cross-sections; fit wrists/ankles and retain measured symmetric joints."""
import bpy,bmesh,json,os,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gloamer_clean_v1.blend'));me=bpy.data.objects['Body'].data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();part=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[part]!=0],context='VERTS')
bm.verts.ensure_lookup_table();bm.verts.index_update()
co=np.array([v.co[:] for v in bm.verts]);faces=np.array([[v.index for v in f.verts] for f in bm.faces])
np.savez(P/'review/geometry/joint_surface.npz',vertices=co,faces=faces)
M={k:np.array(v) for k,v in json.loads((P/'work/meshy_joints.json').read_text())['joints'].items()}
def ring(p,n):
    cut=bm.copy();res=bmesh.ops.bisect_plane(cut,geom=cut.verts[:]+cut.edges[:]+cut.faces[:],plane_co=Vector(p),plane_no=Vector(n))
    edges=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];adj={}
    for e in edges:
        a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
    seen=set();loops=[]
    for v in adj:
        if v in seen:continue
        stack=[v];group=set()
        while stack:
            x=stack.pop()
            if x in seen:continue
            seen.add(x);group.add(x);stack.extend(adj[x])
        if len(group)<4:continue
        points=np.array([x.co[:] for x in group]);per=sum(e.calc_length() for e in edges if e.verts[0] in group)
        loops.append((points.mean(0),per))
    cut.free()
    return min(loops,key=lambda r:np.linalg.norm(r[0]-p)) if loops else None
J={k:v.copy() for k,v in M.items()};R={};probes={}
for side in ['L','R']:
    for joint,parent in [('Hand','Forearm'),('Foot','Calf')]:
        name=side+'_'+joint;seed=M[name];axis=seed-M[side+'_'+parent];axis/=np.linalg.norm(axis)
        rows=[]
        for t in np.linspace(-.065,.065,27):
            hit=ring(seed+axis*t,axis)
            if hit is not None and np.linalg.norm(hit[0]-seed)<.095:rows.append((float(t),hit[0],float(hit[1])))
        assert len(rows)>=8,(name,len(rows))
        selected=min(rows,key=lambda v:v[2]);R[name]=selected[1];J[name]=selected[1]
        probes[name]=[{'offset':t,'centre':c.tolist(),'perimeter':per} for t,c,per in rows]
    # Independent ring centres at shoulder, elbow, knee and hip are comparison evidence, not automatic replacements.
    for joint,child in [('UpperArm','Forearm'),('Forearm','Hand'),('Thigh','Calf'),('Calf','Foot')]:
        name=side+'_'+joint;hit=ring(M[name],M[side+'_'+child]-M[name]);assert hit
        R[name]=hit[0]
for stem in ['Clavicle','UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0']:
    a,b=J['L_'+stem],J['R_'+stem];avg=(a+b)/2;avg[0]=(abs(a[0])+abs(b[0]))/2
    J['L_'+stem]=avg.copy();avg[0]*=-1;J['R_'+stem]=avg
for name in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']:J[name][0]=0
# The service put the spine and head near the chest surface; follow the measured hunch centreline.
for name,z in [('Pelvis',.94),('Spine',1.08),('Spine1',1.25),('Spine2',1.43)]:
    hit=ring(np.array([0,.22,z]),np.array([0,0,1]));assert hit
    J[name]=hit[0];J[name][0]=0;R[name]=J[name].copy()
# Upper horizontal cuts include the projecting head; place the spine in the posterior trunk instead.
J['Spine1']=np.array([0,.24,1.25]);J['Spine2']=np.array([0,.10,1.42])
J['Neck']=np.array([0,0,1.44]);J['Head']=np.array([0,-.08,1.44])
for side,sign in [('L',1),('R',-1)]:
    J[side+'_Clavicle']=np.array([sign*.07,.14,1.40])
    J[side+'_Thigh']=R[side+'_Thigh'].copy()
# Mirror hip positions after the independent ring fit.
a,b=J['L_Thigh'],J['R_Thigh'];avg=(a+b)/2;avg[0]=(abs(a[0])+abs(b[0]))/2
J['L_Thigh']=avg.copy();avg[0]*=-1;J['R_Thigh']=avg
report={'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'method':'Meshy central/limb estimates, cross-section minimum wrists/ankles; bilateral mean. Axial joints follow measured torso rings; neck/head fitted to the observed hunch and skull.'}
(P/'work/joints_fit_base.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'work/joints_final.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'work/joints_rings.json').write_text(json.dumps({'height_m':1.7,'joints':{k:v.tolist() for k,v in R.items()},'probes':probes},indent=2)+'\n')
print('RING',json.dumps({k:np.linalg.norm(J[k]-M[k]).item() for k in J if k.endswith(('Hand','Foot'))}),flush=True)
bm.free();sys.stdout.flush();sys.stderr.flush();os._exit(0)
