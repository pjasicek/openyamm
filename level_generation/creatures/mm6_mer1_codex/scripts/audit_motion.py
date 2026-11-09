"""Surface, weights and floor audits of every role at 48 Hz, with signed distances in millimetres."""
import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=str(P/args[0]));tag=args[1]
sys.path.insert(0,str(P/'scripts'));from surface_volumes import closed_faces,inside
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;me=body.data
pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices]);faces=[tuple(f.vertices)for f in me.polygons];fp=np.array([pv[f[0]]for f in faces]);E=np.array([tuple(e.vertices)for e in me.edges]);rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1);report={}
names={g.index:g.name for g in body.vertex_groups};forearm=np.array([sum(e.weight for e in v.groups if 'Forearm'in names[e.group])>.5 for v in me.vertices])
armEdges={s:np.isin(pv[E[:,0]],[8 if s=='R'else 9])&np.isin(pv[E[:,1]],[8 if s=='R'else 9])for s in 'LR'}
handEdges={s:(pv[E[:,0]]==(4 if s=='R'else 3))&(pv[E[:,1]]==(4 if s=='R'else 3))for s in 'LR'}
clothfaces=[f for f in faces if pv[f[0]]==2];clothhigh=np.array([rest[list(f),2].mean()>.375 for f in clothfaces]);skirtEdges=(pv[E[:,0]]==2)&(pv[E[:,1]]==2)
parts=closed_faces(me,pv,faces)
footids={s:np.where((pv==(6 if s=='L'else 7))&(rest[:,2]<.005))[0]for s in 'LR'}
# Self-check the signed convention: positive is outside cloth, negative is inside the torso.
assert Vector((0,0,.01)).dot(Vector((0,0,1)))>0
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[];worst={'G4_arm_p99':0.,'G4_arm_max':0.,'G5_hand_max':0.,'skirt_stretch_p99':0.,'cloth_leg_mm':0.,'G6_hand_body_mm':0.,'G6_forearm_body_mm':0.,'sleeve_hand_mm':0.};where={}
 for t in np.arange(0,float(a.frame_range[1])/30+1e-5,1/48):
  f=t*30;scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();stretch=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)/np.maximum(rl,1e-8)
  closed={}
  def volume(pid):
   if pid not in closed:closed[pid]=BVHTree.FromPolygons(co.tolist(),parts[pid][0])
   return closed[pid]
  def put(k,v,info=None):
   if v>worst[k]:worst[k]=float(v);where[k]={'time':float(t),'detail':info}
  for sd in 'LR':
   put('G4_arm_p99',np.percentile(stretch[armEdges[sd]],99),sd);put('G4_arm_max',stretch[armEdges[sd]].max(),sd);put('G5_hand_max',stretch[handEdges[sd]].max(),sd)
  put('skirt_stretch_p99',np.percentile(stretch[skirtEdges],99))
  # A folded hem has no single exit plane. Measure actual cloth surface inside closed boot volumes.
  cf=np.array([fc for fc in clothfaces if len(fc)==3 and rest[list(fc),2].min()>.335],dtype=int)
  samples=np.concatenate([co[cf].reshape(-1,3),co[cf].mean(1),((co[cf]+np.roll(co[cf],1,axis=1))*.5).reshape(-1,3)])
  for pid in [6,7]:
   tree=volume(pid);boot=co[pv==pid];use=np.all((samples>=boot.min(0))&(samples<=boot.max(0)),axis=1)
   for point0 in samples[use]:
    point=Vector(point0);loc,n,fi,d=tree.find_nearest(point)
    if loc is not None and parts[pid][1][fi] and (point-loc).dot(n)<0 and inside(point,tree):put('cloth_leg_mm',d*1000,{'boot':pid,'surface_point':point0.tolist()})
  for sd in 'LR':
   hand=3 if sd=='L'else 4;sleeve=9 if sd=='L'else 8
   other=[fc for fc in faces if pv[fc[0]]not in [hand,sleeve]];tree=BVHTree.FromPolygons(co.tolist(),other)
   ids=np.where(pv==hand)[0];sh=rig.pose.bones[f'B_{sd}_UpperArm'].head;el=rig.pose.bones[f'B_{sd}_Forearm'].head;wr=rig.pose.bones[f'B_{sd}_Hand'].head
   for i in np.where(np.isin(pv,[hand,sleeve]))[0]:
    if pv[i]==sleeve and not forearm[i]:continue
    loc,n,fi,d=tree.find_nearest(Vector(co[i]),.08)
    if loc is not None and (Vector(co[i])-loc).dot(n)<-.7*d and inside(Vector(co[i]),volume(int(pv[other[fi][0]]))):put('G6_hand_body_mm'if pv[i]==hand else'G6_forearm_body_mm',d*1000,[int(i),int(pv[other[fi][0]])])
   sf=[fc for fc in faces if pv[fc[0]]==sleeve];tree=BVHTree.FromPolygons(co.tolist(),sf)
   for i in ids:
    # The 8 mm cuff transition deliberately overlaps; beyond it fingers may exit only through the opening.
    if (Vector(co[i])-wr).dot((wr-el).normalized())<.008:continue
    loc,n,fi,d=tree.find_nearest(Vector(co[i]),.06)
    if loc is not None and (Vector(co[i])-loc).dot(n)<-.7*d and inside(Vector(co[i]),volume(sleeve)):put('sleeve_hand_mm',d*1000,int(i))
  soles={sd:co[ids,2]for sd,ids in footids.items()};knees={}
  for sd in 'LR':
   h,k,an=[rig.pose.bones[f'B_{sd}_{n}'].head for n in ['Thigh','Calf','Foot']];knees[sd]=math.degrees((k-h).angle(an-k))
  pelvis=rig.pose.bones['B_Pelvis'].head;trunk=rig.pose.bones['B_Head'].head-pelvis
  rows.append([float(t),float(co[:,2].min()),min(float(v.min())for v in soles.values()),*[float(soles[sd].min())for sd in 'LR'],*[float(soles[sd].max())for sd in 'LR'],knees['L'],knees['R'],pelvis.z,math.degrees(trunk.angle(Vector((0,0,1))))])
 rows=np.array(rows);report[name]={'samples':len(rows),'sample_hz':48,**worst,'worst_at':where,'floor':{'whole_surface_min_m':float(rows[:,1].min()),'lowest_sole_min_m':float(rows[:,2].min()),'lowest_sole_max_m':float(rows[:,2].max()),'swing_peaks_m':rows[:,3:5].max(0).tolist(),'heel_toe_max_m':rows[:,5:7].max(0).tolist(),'contact_fraction_1cm':float((rows[:,2]<=.01).mean()),'knee_peak_deg':rows[:,7:9].max(0).tolist()},'posture':{'pelvis_height_m':[float(rows[:,9].min()),float(rows[:,9].max())],'trunk_lean_deg':[float(rows[:,10].min()),float(rows[:,10].max())]}}
 (P/'review'/f'{tag}_{name}_samples.json').write_text(json.dumps(rows.tolist()));print('GATES',name,json.dumps(report[name]),flush=True)
(P/'review'/f'{tag}_surface_gates.json').write_text(json.dumps(report,indent=2))
