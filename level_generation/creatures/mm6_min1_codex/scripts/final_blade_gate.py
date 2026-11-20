"""Measure the real blade edges, after the final arm fit and distinct Cast timing."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));r=bpy.data.objects['Rig'];a=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;rate=sc.render.fps/sc.render.fps_base;vs=np.array([v.co[:] for v in a.data.vertices]);ids=np.where((abs(vs[:,0])>.21)&(vs[:,2]>.8))[0];points=vs[ids];report={}
for role in ['Attack','Cast']:
 act=bpy.data.actions[role];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];dur=act.frame_range[1]/rate;ts=np.arange(0,dur+.00001,1/120);m=[]
 for t in ts:
  f=t*rate;sc.frame_set(int(f),subframe=float(f%1));m.append(np.array(r.pose.bones['Axe'].matrix@r.data.bones['Axe'].matrix_local.inverted()))
 m=np.array(m);pts=np.einsum('tij,vj->tvi',m[:,:3,:3],points)+m[:,:3,3,None].transpose(0,2,1);vel=np.gradient(pts,1/120,axis=0);speed=np.linalg.norm(vel,axis=2);face=-m[:,1,2];speed[(face<.5)|(ts<.08)|(ts>dur-.08)]=0;i,j=np.unravel_index(speed.argmax(),speed.shape);v=vel[i,j];edge=m[i,:3,0]*np.sign(points[j,0]);lead=float(v@edge/np.linalg.norm(v));flat=float(abs(v@m[i,:3,1])/np.linalg.norm(v));report[role]={'impact_seconds':float(ts[i]),'speed_m_s':float(speed[i,j]),'edge_leading_share':lead,'flat_normal_share':flat,'target_alignment':float(face[i]),'actual_edge_vertex':int(ids[j]),'pass':lead>.65 and flat<.4};assert report[role]['pass']
(P/'review/final_blade_gate.json').write_text(json.dumps(report,indent=2));print('FINAL_BLADE',report)
