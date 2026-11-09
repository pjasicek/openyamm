"""Give the thick rear hull its measured floor space after the weapon release."""
import bpy,sys,os,math,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_motion_before_floor.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Forge_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[]
for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));m=armik.W(r,'Thunder_Maul').copy();root=armik.W(r,'B_Pelvis');t=max(0,min(1,(f-10)/15));root.translation.z+=.04*t*t*(3-2*t);armik.set_world(r,'B_Pelvis',root);armik.set_world(r,'Thunder_Maul',m);keys.append((float(f),{n:r.pose.bones[n].matrix_basis.copy() for n in ('B_Pelvis','Thunder_Maul')}))
for f,pose in keys:
 for n,m in pose.items():
  b=r.pose.bones[n];b.location=m.translation;b.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_motion_fit.blend'));d=json.loads((P/'review/forge_motion_fit.json').read_text());d.pop('Death',None);d.pop('Dead',None);(P/'review/forge_motion_fit.json').write_text(json.dumps(d,indent=2)+'\n');sys.stdout.flush();os._exit(0)
