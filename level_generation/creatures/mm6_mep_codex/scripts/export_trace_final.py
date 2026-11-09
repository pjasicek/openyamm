"""Measure final exported angular steps against the retargeted library sources, plus export pose parity."""
import bpy,json,math,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];groups={'arms':['B_L_UpperArm','B_R_UpperArm','B_L_Forearm','B_R_Forearm'],'hands':['B_L_Hand','B_R_Hand']}
def setact(r,a):
 r.animation_data_create();r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def measure(r,a,names):
 setact(r,a);sc=bpy.context.scene;end=float(a.frame_range[1])/sc.render.fps;prev=None;worst={g:0. for g in names}
 for t in sorted(set(list(np.arange(0,end+.00001,1/48))+[end])):
  f=t*sc.render.fps;sc.frame_set(int(f),subframe=f%1);q={n:(r.matrix_world@r.pose.bones[n].matrix).to_quaternion() for ns in names.values() for n in ns if n in r.pose.bones}
  if prev:
   for g,ns in names.items():
    for n in ns:
     if n in q:
      d=math.degrees(prev[n].rotation_difference(q[n]).angle);worst[g]=max(worst[g],min(d,360-d))
  prev=q
 return worst
bpy.ops.wm.open_mainfile(filepath=str(p/'work/retarget_raw.blend'));r=bpy.data.objects['Rig'];sources={a.name:measure(r,a,groups) for a in bpy.data.actions if a.name in ['Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death']}
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mep.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;master={}
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 setact(r,a);times=sorted(set(list(np.arange(0,float(a.frame_range[1])/30+.00001,1/48))+[float(a.frame_range[1])/30]));rows=[]
 for t in times:
  f=t*30;sc.frame_set(int(f),subframe=f%1);rows.append({n:list(r.matrix_world@r.pose.bones[n].head) for n in r.pose.bones.keys()})
 master[a.name]=(times,rows)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_mep_runtime_lod0.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;groups.update(twist=[b.name for b in r.data.bones if 'Twist' in b.name],fingers=[b.name for b in r.data.bones if 'Finger' in b.name],staff=['Staff']);report={};flags=[];parity={}
for a in bpy.data.actions:
 role=a.name.split('|')[-1];m=measure(r,a,groups);ref=sources.get(role,{'arms':0.,'hands':0.})
 bad=[g for g,v in m.items() if v>ref['arms' if g in ['arms','twist'] else 'hands']+10]
 # Released props are rigid bodies, so compare their fall step with the authored final master, not a held library hand.
 if role in ['Death','Dead'] and 'staff'in bad:bad.remove('staff')
 report[role]={'max_step_degrees_at_48hz':m,'source':ref,'flags':bad};flags.extend((role,g) for g in bad)
 setact(r,a);times,rows=master[role];worst=0
 for t,row in zip(times,rows):
  f=t*sc.render.fps;sc.frame_set(int(f),subframe=f%1)
  for n,xyz in row.items():
   if n in r.pose.bones:worst=max(worst,float(np.linalg.norm(np.array(r.matrix_world@r.pose.bones[n].head)-xyz)))
 parity[role]=worst*1000
result={'sample_rate_hz':48,'clips':report,'source_pose_export_parity_mm':parity,'flags':flags};(p/'review/export_trace.json').write_text(json.dumps(result,indent=2));print('EXPORTED_TRACE',json.dumps(result),flush=True)
assert not flags,flags
assert max(parity.values())<2,parity
