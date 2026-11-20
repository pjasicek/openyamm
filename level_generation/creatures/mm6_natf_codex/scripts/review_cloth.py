import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_cloth.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
common.workbench_clay(sc);body.data.materials.clear();m=bpy.data.materials.new('clay');m.diffuse_color=(.58,.51,.40,1);body.data.materials.append(m)
co=np.array([tuple(v.co)for v in body.data.vertices]);parts=np.array([a.value for a in body.data.attributes['piece'].data]);rows={};report={};(P/'review/cloth').mkdir(exist_ok=True)
rest={};hf=json.loads((P/'work/hand_frames.json').read_text());soles={}
for sd in 'LR':
 a,b,c=[rig.data.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];rest[sd]={'u':(a.matrix_local.to_3x3().inverted()@(b.head_local-a.head_local)).normalized(),'f':(b.matrix_local.to_3x3().inverted()@(c.head_local-b.head_local)).normalized(),'rel':a.matrix_local.to_3x3().inverted()@b.matrix_local.to_3x3()}
 ids=np.where((parts==1)&(co[:,0]*(1 if sd=='L'else -1)>0)&(co[:,2]<.075))[0];z=co[ids,2].min();soles[sd]=ids[co[ids,2]<z+.009]
def twist(q,ax):return math.degrees((2*math.atan2(Vector((q.x,q.y,q.z)).dot(ax),q.w)+math.pi)%(2*math.pi)-math.pi)
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];f0,f1=act.frame_range;data={s:[]for s in 'LR'};bounds=[];posture=[]
 for f in np.arange(f0,f1+.001,sc.render.fps/48):
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(v.co)for v in me.vertices]);ev.to_mesh_clear();p=rig.pose.bones['B_Pelvis'].head;n=rig.pose.bones['B_Neck'].head;posture.append([p.z,math.degrees((n-p).angle(Vector((0,0,1))))])
  for sd in 'LR':
   a,b,h=[rig.pose.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(b.head-a.head).normalized();v=(h.head-b.head).normalized();hn=(a.matrix.to_3x3()@Vector((0,0,-1))).normalized();flex=math.degrees(math.atan2(u.cross(v).dot(hn),u.dot(v)));plane=math.degrees(math.asin(min(1,abs(v.dot(hn)))));upper=twist(a.rotation_quaternion,rest[sd]['u']);base=a.matrix.to_3x3()@rest[sd]['rel'];base=(base@rest[sd]['f']).rotation_difference(v).to_matrix()@base;roll=twist((base.inverted()@b.matrix.to_3x3()).to_quaternion(),rest[sd]['f']);pts=c[soles[sd]];rc=co[soles[sd]];heel=pts[rc[:,1]>np.quantile(rc[:,1],.75),2].min();toe=pts[rc[:,1]<np.quantile(rc[:,1],.25),2].min();hh,kk,aa=[rig.pose.bones[f'B_{sd}_{n}'].head for n in ['Thigh','Calf','Foot']];knee=math.degrees((kk-hh).angle(aa-kk));normal=h.matrix.to_3x3()@Vector(hf[sd]['palm_local']);d=hh-h.head;d.z=0
   data[sd].append({'seconds':float(f/sc.render.fps),'flex':flex,'plane':plane,'upper':upper,'fore':roll,'sole':float(pts[:,2].min()),'heel':float(heel),'toe':float(toe),'knee':knee,'palm_in':normal.dot(d.normalized())})
 report[name]={'sides':{sd:{'flex_min':min(r['flex']for r in dd),'flex_max':max(r['flex']for r in dd),'plane_max':max(r['plane']for r in dd),'upper_max':max(abs(r['upper'])for r in dd),'fore_max':max(abs(r['fore'])for r in dd),'sole_min':min(r['sole']for r in dd),'swing_peak':max(r['sole']for r in dd),'knee_at_peak':max(dd,key=lambda r:r['sole'])['knee'],'heel_toe_delta_max':max(abs(r['heel']-r['toe'])for r in dd),'palm_in_min':min(r['palm_in']for r in dd)}for sd,dd in data.items()},'pelvis_range':[min(r[0]for r in posture),max(r[0]for r in posture)],'trunk_max':max(r[1]for r in posture)}
 print('PILOT',name,report[name],flush=True);rows[name]=[]
 for i in range(5):
  f=f0+(f1-f0)*i/4;sc.frame_set(int(f),subframe=f-int(f));lo,hi=common.world_bounds([body]);h=max(1.82,(hi-lo).z*1.1,(hi-lo).x*1.55,(hi-lo).y*1.55);center=(lo+hi)*.5
  for view in ['front','left','three_quarter']:
   path=common.render_views(str(P/'review/cloth'/f'{name}_{i}'),center.z,h,views=(view,),resolution=(240,360),target=(center.x,center.y))[0];rows[name].append({'view':view,'frame':f,'path':str(Path(path).relative_to(P))})
(P/'review/cloth/frames.json').write_text(json.dumps(rows,indent=2));(P/'review/cloth/pose_audit.json').write_text(json.dumps(report,indent=2))
assert len(report)==9
