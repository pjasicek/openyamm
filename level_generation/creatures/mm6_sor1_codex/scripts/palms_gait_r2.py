"""Palms, actual shoe clearance, gait yaw and width diagnostics on the reimported endpoint at 48 Hz."""
import bpy,numpy as np,math,json
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/runtime_reimport.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
pv=np.array([a.value for a in body.data.attributes['piece'].data]);ids={s:np.where(pv==part)[0] for s,part in [('R',101),('L',102)]};G=json.loads((p/'work/runtime_grip_pose.json').read_text());report={}
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows={s:[] for s in 'LR'};palms={s:[] for s in 'LR'};previous={s:None for s in 'LR'}
 for t in np.arange(0,act.frame_range[1]/scene.render.fps+1e-6,1/48):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  for s in 'LR':
   H=rig.pose.bones['B_'+s+'_Hand'];socket=rig.pose.bones['Socket_Palm_'+{'L':'Left','R':'Right'}[s]];normal=(socket.tail-socket.head).normalized();normal=rig.matrix_world.to_3x3()@normal
   inward=Vector((-1 if s=='L' else 1,0,0));angle=math.degrees(normal.angle(previous[s])) if previous[s] is not None else 0;previous[s]=normal.copy();palms[s].append([normal.dot(inward),angle])
   xyz=np.array([list(body.matrix_world@me.vertices[int(i)].co) for i in ids[s]]);low=float(xyz[:,2].min());T=rig.pose.bones['B_'+s+'_Thigh'].head;K=rig.pose.bones['B_'+s+'_Calf'].head;F=rig.pose.bones['B_'+s+'_Foot'].head;knee=math.degrees((K-T).angle(F-K));foot=rig.pose.bones['B_'+s+'_Foot'];rfoot=rig.data.bones[foot.name];axis=(rig.matrix_world@foot.matrix@rfoot.matrix_local.inverted()).to_3x3()@Vector((0,-1,0));yaw=math.degrees(math.atan2(axis.x,-axis.y));rows[s].append([float(t),low,knee,yaw])
  ev.to_mesh_clear()
 result={'sample_hz':48,'feet':{},'palms':{}}
 for s in 'LR':
  a=np.array(rows[s]);v=np.array(palms[s]);peak=int(a[:,1].argmax());result['feet'][s]={'lowest_sole_mm':[float(a[:,1].min()*1000),float(a[:,1].max()*1000)],'peak_lift_time_s':float(a[peak,0]),'knee_at_peak_lift_deg':float(a[peak,2]),'yaw_deg':[float(a[:,3].min()),float(a[:,3].max())]};result['palms'][s]={'inward_dot':[float(v[:,0].min()),float(v[:,0].max())],'max_normal_delta_per_48hz_deg':float(v[:,1].max()),'continuous':bool(v[:,1].max()<60)}
 result['pass']=all(v['continuous'] for v in result['palms'].values()) and all(v['lowest_sole_mm'][0]>=-2 for v in result['feet'].values())
 if role in ['Standing','Walking']:result['rest_free_palm_inward']=result['palms']['L']['inward_dot'][0]>0;result['pass'] &= result['rest_free_palm_inward']
 report[role]=result;print('EXTRA_GATES',role,json.dumps(result),flush=True)
(p/'work/round2_palms_gait.json').write_text(json.dumps(report,indent=2));assert all(v['pass'] for v in report.values()),report
