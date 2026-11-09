"""Final geometry-based gait, grip, blow, scale and head-clearance measurements."""
import bpy,sys,json,math,numpy as np,runpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from surface_volumes import closed_faces,inside
path=P/'work/reduction/selected_lod0.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;s=bpy.context.scene;pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices]);faces=[tuple(f.vertices)for f in me.polygons];fingers=np.array([a.value for a in me.attributes['finger'].data]);sole={sd:np.where((pv==(6 if sd=='L'else 7))&(rest[:,2]<.012))[0]for sd in 'LR'};B=r.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();tip=B.head_local+axis*.452
parts=closed_faces(me,pv,faces)
report={};grip=[];blow=[];height=[];picks=[]
for role in C.ROLES:
 a=bpy.data.actions[role];end=float(a.frame_range[1])/30;angles=[];headpen=0.
 picks += [f'{role}:{int(float(a.frame_range[1])*q)}'for q in [0,.25,.5,.75,1]]
 for t in np.arange(0,end+1e-5,1/48):
  C.activate(role,float(t));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear()
  if role=='Walking':height.append(float(co[:,2].max()-co[:,2].min()))
  if role in ['Standing','Fidget','Walking','Running']:
   for sd,ids in sole.items():
    xy=co[ids,:2];v=np.linalg.eigh(np.cov(xy.T))[1][:,-1]
    if v[1]>0:v=-v
    angles.append(abs(math.degrees(math.atan2(v[0],-v[1]))))
  torso=[fc for fc in faces if pv[fc[0]]in[1,8,9]];tree=BVHTree.FromPolygons(co.tolist(),torso);volumes={}
  for i in np.where((pv==0)&(rest[:,2]>1.535))[0]:
   loc,n,fi,d=tree.find_nearest(Vector(co[i]),.10)
   if loc is not None and (Vector(co[i])-loc).dot(n)<-.7*d:
    pid=int(pv[torso[fi][0]])
    if pid not in volumes:volumes[pid]=BVHTree.FromPolygons(co.tolist(),parts[pid][0])
    if inside(Vector(co[i]),volumes[pid]):headpen=max(headpen,d*1000)
  if role=='Attack':
   M=r.pose.bones['Club'].matrix@B.matrix_local.inverted();T=M@tip;root=r.pose.bones['Club'].head;blow.append([float(t),*T,*root])
   if .21<=t<=end-.26:
    A=(M.to_3x3()@axis).normalized();C0=root;mins=[]
    for label in range(6):
     samples=[]
     for fc in faces:
      if pv[fc[0]]!=4:continue
      if not any(fingers[i]==label for i in fc):continue
      triangle=co[list(fc)];samples.extend(triangle.tolist());samples.append(triangle.mean(0).tolist())
      samples.extend(((triangle+np.roll(triangle,1,axis=0))*.5).tolist())
     q=np.array(samples)-np.array(C0);along=q@np.array(A);rad=np.linalg.norm(q-np.outer(along,A),axis=1);use=abs(along)<.05
     mins.append(float(rad[use].min())if use.any()else None)
    grip.append([float(t),*mins])
 report[role]={'foot_heading_max_deg':max(angles)if angles else None,'head_shoulder_penetration_mm':headpen}
blow=np.array(blow);v=np.gradient(blow[:,1:4],blow[:,0],axis=0);ax=blow[:,1:4]-blow[:,4:7];ax/=np.linalg.norm(ax,axis=1)[:,None];speed=np.linalg.norm(v,axis=1);eligible=ax@np.array([0,-1,0])>.7;idx=int(np.argmax(np.where(eligible,speed,-1)));assert eligible[idx]
report['blow']={'impact_seconds':float(blow[idx,0]),'tip_speed_m_s':float(speed[idx]),'points_at_target_dot':float(-ax[idx,1]),'cutting_edge':'not applicable: blunt wooden club','sample_hz':48}
g=np.array(grip);report['grip']={'held_samples':len(g),'sample_hz':48,'handle_radius_mm':12.5,'min_radial_mm_palm_thumb_index_middle_ring_pinky':(g[:,1:].min(0)*1000).tolist(),'max_closest_radial_mm_palm_thumb_index_middle_ring_pinky':(g[:,1:].max(0)*1000).tolist(),'maximum_penetration_mm':max(0,float(12.5-g[:,1:].min()*1000)),'palm_gap_max_mm':float(g[:,1].max()*1000-12.5)}
native_height=253*.699997
report['scale']={'walk_visible_height_m':max(height),'native_height_game_units':native_height,'scale':native_height/max(height),'stride_length':.84,'running_stride':1.302,'yaw_offset':-math.pi/2,'z_offset':-.001*native_height/max(height)}
(P/'review/final_intent.json').write_text(json.dumps(report,indent=2));print('FINAL INTENT',json.dumps(report),flush=True)
sys.argv=['g4_weights.py','--',str(path),'final',*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
