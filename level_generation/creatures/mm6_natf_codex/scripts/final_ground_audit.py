import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];out={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;co=np.array([tuple(v.co)for v in body.data.vertices]);part=np.array([v.value for v in body.data.attributes['piece'].data]);feet={s:np.where((part==1)&(co[:,2]<.075)&(co[:,0]*(1 if s=='L'else-1)>0))[0]for s in 'LR'};out[str(level)]={}
 for name in ['Walking','Running']:
  a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];values=[]
  for f in sorted(set([*np.arange(0,a.frame_range[1],sc.render.fps/48),float(a.frame_range[1])])):
   sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(v.co)for v in me.vertices]);ev.to_mesh_clear();values.append([float(c[feet[s],2].min())for s in 'LR'])
  v=np.array(values);out[str(level)][name]={'lowest_sole_m':float(v.min()),'swing_peak_m':v.max(0).tolist(),'max_both_feet_airborne_m':float(v.min(1).max()),'contact_fraction_at_10mm':float(np.mean(v.min(1)<=.01))}
  if name=='Running':assert v.min(1).max()<=.04 and np.mean(v.min(1)<=.01)>=.8
(P/'review/final/ground_audit.json').write_text(json.dumps(out,indent=2));print('GROUND_FINAL',out,flush=True)
