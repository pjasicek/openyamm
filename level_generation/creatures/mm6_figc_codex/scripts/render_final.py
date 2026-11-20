import bpy,sys,json,math,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_figc_a.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');objects=[o for o in bpy.data.objects if o.type=='MESH'];scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
for view in ['front','left','three_quarter']:
 out=P/f'review/final_{view}';out.mkdir(exist_ok=True);rows=[]
 for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
  act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];row=[]
  # One fixed camera per clip includes the complete body and dropped gear over all sampled frames.
  bounds=[]
  for i in range(7):
   f=float(act.frame_range[1])*i/6;scene.frame_set(int(f),subframe=f%1);bounds.append(common.world_bounds(objects))
  from mathutils import Vector
  lo=Vector([min(a[k] for a,b in bounds) for k in range(3)]);hi=Vector([max(b[k] for a,b in bounds) for k in range(3)]);c=(lo+hi)*.5;h=max(2.05,(hi-lo).length*1.3)
  for i in range(7):
   f=float(act.frame_range[1])*i/6;scene.frame_set(int(f),subframe=f%1);p=common.render_views(str(out/f'{name}_{i}'),c.z,h,views=[view],resolution=(320,420),target=(c.x,c.y))[0];row.append([p,f'{name} {f/30:.3f}s'])
  rows.append(row)
 (out/'frames.json').write_text(json.dumps(rows))
