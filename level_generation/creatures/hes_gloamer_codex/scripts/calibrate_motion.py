"""Measure fitted size/impact and compare world rotation steps with each original source at 60 Hz."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_export.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
mapping={'B_Head':'Head','B_L_UpperArm':'LeftArm','B_R_UpperArm':'RightArm','B_L_Hand':'LeftHand','B_R_Hand':'RightHand','B_L_Foot':'LeftFoot','B_R_Foot':'RightFoot'}
def series(obj,act,bones,fps):
 obj.animation_data.action=act
 if len(act.slots):obj.animation_data.action_slot=act.slots[0]
 lo,hi=act.frame_range;prev=None;steps=[]
 for f in np.arange(lo,hi+.0001,fps/60):
  sc.frame_set(int(f),subframe=float(f-int(f)));q=[(obj.matrix_world@obj.pose.bones[n].matrix).to_quaternion() for n in bones]
  if prev:
   angles=[a.rotation_difference(b).angle for a,b in zip(prev,q)];steps.append([math.degrees(min(x,2*math.pi-x)) for x in angles])
  prev=q
 a=np.array(steps);return {'max_step_degrees':float(a.max()),'max_step_change_degrees':float(np.abs(np.diff(a,axis=0)).max()) if len(a)>1 else 0,'per_bone_max_degrees':dict(zip(mapping,[float(x) for x in a.max(0)]))}
clips=json.loads((P/'clips.json').read_text())['clips'];report={}
for role in clips:report[role]={'target':series(rig,bpy.data.actions[role],list(mapping),30)}
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];sc.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();lo=co.min(0);hi=co.max(0)
base_scale=175/(hi[2]-lo[2]);ground=co[co[:,2]<.18];radius=float(np.linalg.norm(ground[:,:2],axis=1).max()*base_scale)
size={'standing_bounds_m':[lo.tolist(),hi.tolist()],'base_model_scale':base_scale,'base_height_units':175,'base_radius_units':math.ceil(radius),'radius_measurement':'Maximum XY reach of the stance skin within 18 cm of the floor, from the model origin.'}
rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=bpy.data.actions['Attack'].slots[0];points=[]
for f in range(int(bpy.data.actions['Attack'].frame_range[1])+1):
 sc.frame_set(f);points.append([rig.pose.bones['B_'+s+'_Hand'].head.y for s in 'LR'])
v=-np.diff(np.array(points),axis=0)*30;frame=int(np.unravel_index(v.argmax(),v.shape)[0])+1;size['melee_impact_s']=frame/30
for role,path in clips.items():
 before=set(bpy.data.objects);before_actions=set(bpy.data.actions);bpy.ops.import_scene.fbx(filepath=os.path.abspath(path));fps=sc.render.fps/sc.render.fps_base;new=set(bpy.data.objects)-before;src=next(o for o in new if o.type=='ARMATURE');act=src.animation_data.action;pre=next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
 report[role]['source']=series(src,act,[pre+n for n in mapping.values()],fps)
 t,s=report[role]['target'],report[role]['source'];report[role]['step_ratio']=t['max_step_degrees']/max(s['max_step_degrees'],.01)
 assert t['max_step_degrees']<max(5,s['max_step_degrees']*2.5),(role,t,s)
 for o in new:bpy.data.objects.remove(o,do_unlink=True)
 for a in set(bpy.data.actions)-before_actions:bpy.data.actions.remove(a)
(P/'review/source_motion_comparison.json').write_text(json.dumps(report,indent=2)+'\n');(P/'review/calibration.json').write_text(json.dumps(size,indent=2)+'\n')
print('CALIBRATION',size,flush=True);print('STEP RATIOS',{k:round(v['step_ratio'],3) for k,v in report.items()},flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
