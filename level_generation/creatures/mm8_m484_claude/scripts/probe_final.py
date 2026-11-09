import bpy,sys,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gated_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
reports={}
for nm in ['Standing','Walking','Attack','Hit']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=f%1);M=armik.W(r,'Axe')@r.data.bones['Axe'].matrix_local.inverted();rows.append({'f':f,'M':np.array(M),'tip':np.array(M@Vector((0,0,1.10)))})
 report={}
 if nm=='Attack':
  speed=np.array([np.linalg.norm(y['tip']-x['tip']) for x,y in zip(rows,rows[1:])]);k=speed>=np.percentile(speed,80);scores=[]
  for deg in range(0,180,5):
   ph=math.radians(deg);edge=Vector((math.cos(ph),math.sin(ph),0));flat=Vector((-math.sin(ph),math.cos(ph),0));val=[]
   for yes,x,y in zip(k,rows,rows[1:]):
    if yes:
     v=y['tip']-x['tip'];R=y['M'][:3,:3];e=v@(R@np.array(edge));n=v@(R@np.array(flat));val.append(abs(e)/max(math.hypot(e,n),1e-9))
   scores.append((deg,float(np.mean(val))))
  report={'roll_scores':scores,'min_forward_frame':float(min(rows,key=lambda x:x['tip'][1])['f']),'tip_path':[[float(x['f']),*map(float,x['tip'])] for x in rows]}
 reports[nm]=report
print('PROBE',json.dumps(reports));(P/'review/final_blade.json').write_text(json.dumps(reports,indent=2))
