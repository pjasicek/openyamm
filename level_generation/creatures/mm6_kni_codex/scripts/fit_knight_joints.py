"""Independent mesh-boundary/ring measurements against Meshy joints for this plate-armour mesh."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));body=bpy.data.objects['Body'];me=body.data
M={k:np.array(v) for k,v in json.loads((P/'work/meshy_joints.json').read_text())['joints'].items()}
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
def boundary(piece):
 ids={v.index for e in bm.edges if e.is_boundary for v in e.verts if pv[v.index]==piece};assert len(ids)>5;return co[list(ids)].mean(0)
def ring_centres(S,W,pieces,ts):
 base=bm.copy();base.verts.ensure_lookup_table();bmesh.ops.delete(base,geom=[v for v in base.verts if pv[v.index] not in pieces],context='VERTS');d=(W-S)/np.linalg.norm(W-S);out=[]
 for t in ts:
  q=S+(W-S)*t;b=base.copy();r=bmesh.ops.bisect_plane(b,geom=b.verts[:]+b.edges[:]+b.faces[:],plane_co=Vector(q),plane_no=Vector(d));verts={v for e in r['geom_cut'] if isinstance(e,bmesh.types.BMEdge) for v in e.verts};pts=np.array([tuple(v.co) for v in verts if (v.co-Vector(q)).length<.12]);
  if len(pts)>=5:out.append((t,pts.mean(0).tolist()))
  b.free()
 base.free();return out
J={k:v.copy() for k,v in M.items()};report={};centrelines={}
for side,hand,boot,bracer in [('R',4,14,10),('L',5,13,9)]:
 S=M[side+'_UpperArm'];W=boundary(hand);J[side+'_Hand']=W;J[side+'_Foot']=boundary(boot)
 rs=ring_centres(S,W,{0,bracer},np.linspace(.18,.92,40));centrelines[side+'_arm']=rs
 vals=np.array([c for t,c in rs]);ts=np.array([t for t,c in rs]);d=(W-S)/np.linalg.norm(W-S)
 def fit(mask):
  a=vals[mask];assert len(a)>3;c=a.mean(0);u=np.linalg.svd(a-c)[2][0];return c,u if u@d>0 else -u
 c1,u1=fit((ts>.18)&(ts<.42));c2,u2=fit((ts>.60)&(ts<.90));ab=np.column_stack([u1,-u2]);q=np.linalg.lstsq(ab,c2-c1,rcond=None)[0];E=(c1+u1*q[0]+c2+u2*q[1])/2
 t=float((E-S)@d/np.linalg.norm(W-S));bend=math.degrees(math.acos(np.clip(u1@u2,-1,1)))
 report[side]={'mesh_wrist':W.tolist(),'meshy_wrist':M[side+'_Hand'].tolist(),'mesh_elbow':E.tolist(),'meshy_elbow':M[side+'_Forearm'].tolist(),'elbow_t':t,'line_bend_deg':bend,'line_gap_mm':float(np.linalg.norm(c1+u1*q[0]-c2-u2*q[1])*1000)}
 # Armour ring bulges are explicit measurement uncertainty; inspect the recorded fit before choosing its elbow.
 J[side+'_Forearm']=E
 assert .35<t<.70, 'Ring elbow outside anatomical segment' 
 print('JOINT',side,json.dumps(report[side]))
(P/'work/joint_measurements.json').write_text(json.dumps({'report':report,'centrelines':centrelines},indent=2))
(P/'work/joints_final.json').write_text(json.dumps({'height_m':1.9,'joints':{k:v.tolist() for k,v in J.items()},'report':report},indent=2))
