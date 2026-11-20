import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/assembled.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;rows={}
for ac in bpy.data.actions:
 if ac.name not in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:continue
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows[ac.name]={}
 for ob in [bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']]:
  low=(100,None);high=0
  for f in np.arange(0,ac.frame_range[1]+.001,sc.render.fps/48):
   sc.frame_set(int(f),subframe=float(f%1));ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min(v.co.z for v in me.vertices);ev.to_mesh_clear()
   if z<low[0]:low=(z,float(f/sc.render.fps))
  rows[ac.name][ob.name]={'lowest_m':low[0],'seconds':low[1]}
 print(ac.name,rows[ac.name],flush=True)
(P/'review/props_floor_initial.json').write_text(json.dumps(rows,indent=2))
