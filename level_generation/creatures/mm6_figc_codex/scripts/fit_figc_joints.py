import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));ob=bpy.data.objects['Body'];me=ob.data
pv=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([tuple(v.co) for v in me.vertices]);J=json.loads((P/'work/meshy_joints.json').read_text())['joints'];J={k:np.array(v) for k,v in J.items()};report={}
for side,piece in [('L',1),('R',2)]:
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index]!=piece],context='VERTS');boundary={v for e in bm.edges if e.is_boundary for v in e.verts};assert len(boundary)>=8
 wrist=np.array([tuple(v.co) for v in boundary]).mean(0);old=J[side+'_Hand'].copy();J[side+'_Hand']=wrist;bm.free()
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();pieces={4} if side=='L' else {5,12};bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index] not in pieces],context='VERTS')
 sh=J[side+'_UpperArm'];axis=wrist-sh;ts=[];centres=[]
 for t in np.linspace(.1,.95,50):
  q=sh+axis*t;cut=bm.copy();res=bmesh.ops.bisect_plane(cut,geom=cut.verts[:]+cut.edges[:]+cut.faces[:],plane_co=Vector(q),plane_no=Vector(axis));vs=[v for v in res['geom_cut'] if isinstance(v,bmesh.types.BMVert)];pts=np.array([tuple(v.co) for v in vs]);cut.free()
  if len(pts)>=5:
   pts=pts[np.linalg.norm(pts-q,axis=1)<.13]
   if len(pts)>=5:ts.append(t);centres.append(pts.mean(0))
 bm.free();ts=np.array(ts);cs=np.array(centres)
 def line(mask):
  a=cs[mask];assert len(a)>3;c=a.mean(0);u=np.linalg.svd(a-c)[2][0];return c,u
 c1,u1=line((ts>.13)&(ts<.38));c2,u2=line((ts>.63)&(ts<.9));pars=np.linalg.lstsq(np.column_stack([u1,-u2]),c2-c1,rcond=None)[0];a=c1+u1*pars[0];b=c2+u2*pars[1];el=(a+b)/2;el_t=float((el-sh)@axis/(axis@axis));gap=float(np.linalg.norm(a-b));off=float(np.linalg.norm(el-J[side+'_Forearm']))
 # Near-straight armored arms have unstable line intersections; retain Meshy's independent estimate then.
 selected=.35<el_t<.7 and gap<.025 and off<.06
 if selected:J[side+'_Forearm']=el
 report[side]={'wrist_boundary_vertices':len(boundary),'wrist_correction_cm':float(np.linalg.norm(wrist-old)*100),'elbow_ring_t':el_t,'elbow_line_gap_cm':gap*100,'elbow_estimate_difference_cm':off*100,'ring_elbow_selected':selected,'ring_centres':cs.tolist()}
 print('JOINT_FIT',side,{k:v for k,v in report[side].items() if k!='ring_centres'},flush=True)
for side,pieces in [('L',[30,31]),('R',[32,34])]:
 pts=co[np.isin(pv,pieces)];ankle=(pts.min(0)+pts.max(0))/2;report[side]['ankle_correction_cm']=float(np.linalg.norm(J[side+'_Foot']-ankle)*100);J[side+'_Foot']=ankle
out={'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report};(P/'work/joints_final.json').write_text(json.dumps(out,indent=2))
