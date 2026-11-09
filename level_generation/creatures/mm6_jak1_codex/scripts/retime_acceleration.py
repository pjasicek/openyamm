"""Locally ease fast arm transitions while preserving every fitted pose and contact."""
import bpy,json,math,numpy as np

def warp(t,bumps):
 t=np.asarray(t,dtype=float);out=t.copy()
 for center,width,delay in bumps:
  u=np.clip((t-center+width)/(2*width),0,1);z=np.clip((-center+width)/(2*width),0,1);out+=delay*(u*u*(3-2*u)-z*z*(3-2*z))
 return out

def acceleration(q,times):
 dt=np.diff(times);a=q[1:];b=q[:-1].copy();b[...,1:]*=-1;w=a[...,:1]*b[...,:1]-(a[...,1:]*b[...,1:]).sum(-1,keepdims=True);v=a[...,:1]*b[...,1:]+b[...,:1]*a[...,1:]+np.cross(a[...,1:],b[...,1:]);v=np.where(w<0,-v,v);w=np.abs(w);length=np.linalg.norm(v,axis=-1,keepdims=True);angle=2*np.arctan2(length,w);velocity=v*np.divide(angle,length,out=np.zeros_like(angle),where=length>1e-12)*180/math.pi/dt[:,None,None];return np.linalg.norm(np.diff(velocity,axis=0)/((dt[:-1]+dt[1:])*.5)[:,None,None],axis=-1)

def retime(rig,P):
 fps=bpy.context.scene.render.fps;names=[f'B_{s}_{b}'for s in 'LR'for b in ['UpperArm','Forearm','Hand']]+[b.name for b in rig.pose.bones if '_Finger'in b.name];report={};target=17000
 for action in bpy.data.actions:
  rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];last=int(round(action.frame_range[1]));oldtimes=np.arange(last+1)/fps;quats=[]
  for frame in range(last+1):
   bpy.context.scene.frame_set(frame);quats.append([tuple((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())for n in names])
  quats=np.array(quats)
  for i in range(1,len(quats)):
   bad=(quats[i]*quats[i-1]).sum(1)<0;quats[i,bad]*=-1
  bumps=[];history=[];finger_history=[]
  for iteration in range(60):
   mapped=warp(oldtimes,bumps);end=math.ceil((mapped[-1]-1e-8)*fps)/fps;times=np.arange(int(math.floor(end*48+1e-6))+1)/48
   if end-times[-1]>1e-6:times=np.r_[times,end]
   else:times[-1]=end
   old=np.interp(times,mapped,oldtimes);position=np.minimum(old*fps,last-1e-9);index=np.floor(position).astype(int);fraction=(position-index)[:,None,None];q=quats[index]*(1-fraction)+quats[index+1]*fraction;q/=np.linalg.norm(q,axis=2,keepdims=True);acc=acceleration(q[:,:6],times);k,bone=np.unravel_index(acc.argmax(),acc.shape);maximum=float(acc[k,bone]);history.append(maximum)
   steps=2*np.degrees(np.arccos(np.clip(np.abs((q[1:,6:]*q[:-1,6:]).sum(2)),0,1)));j,digit=np.unravel_index(steps.argmax(),steps.shape);finger_max=float(steps[j,digit]);finger_history.append(finger_max)
   if maximum<=target and finger_max<=22:break
   finger_driven=finger_max/22>math.sqrt(maximum/target);center=float((old[j]+old[j+1])*.5 if finger_driven else old[k+1]);width=.10 if finger_driven else .14;u=np.array([np.clip((center-c+w)/(2*w),0,1)for c,w,d in bumps]);rate=1+sum(d*6*x*(1-x)/(2*w)for (c,w,d),x in zip(bumps,u));delay=max(.004,min(.10,((finger_max/22 if finger_driven else math.sqrt(maximum/target))-1)*rate*(2*width)/1.5));bumps.append([center,width,delay])
   assert float(warp(oldtimes[-1],bumps))<oldtimes[-1]*(1.75 if action.name in ['Attack','Cast'] else 1.35)+.1,(action.name,'excessive timing change',history)
  else:raise AssertionError((action.name,'acceleration fit did not converge',history))
  assert np.all(np.diff(mapped)>0) and abs(float(warp(0,bumps)))<1e-12
  if bumps:
   for layer in action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for curve in bag.fcurves:
       for key in curve.keyframe_points:
        key.co.x=float(warp(key.co.x/fps,bumps))*fps;key.interpolation='LINEAR'
       curve.update();value=curve.evaluate(float(mapped[-1]*fps));curve.keyframe_points.insert(end*fps,value,options={'FAST'});curve.update()
   action.use_frame_range=True;action.frame_start=0;action.frame_end=end*fps
  report[action.name]={'source_duration_s':float(oldtimes[-1]),'duration_s':end,'bumps':bumps,'predicted_max_deg_s2':maximum,'predicted_max_finger_step_deg':finger_max,'finger_step_history':finger_history,'iterations':len(history),'history':history}
  print('RETIME',action.name,report[action.name],flush=True)
 rig.animation_data.action=None
 (P/'work/action_timing.json').write_text(json.dumps(report,indent=2))
 drop=json.loads((P/'work/staff_drop.json').read_text());drop['source_phase_seconds']={key:drop[key]for key in ['release_seconds','first_floor_contact_seconds','settled_seconds']}
 for key,value in drop['source_phase_seconds'].items():
  if value is not None:drop[key]=float(warp(value,report['Death']['bumps']))
 (P/'work/staff_drop.json').write_text(json.dumps(drop,indent=2))
