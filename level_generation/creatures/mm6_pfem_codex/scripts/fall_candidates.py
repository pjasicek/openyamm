import bpy,sys,math,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
rows=[]
for file,clip in [('Relax','RelaxLaydownLayDown'),('Unarmed','UnarmedDeath1'),('Armed','ArmedDeath1'),('Armed-Shield','ShieldDeath1')]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(Path(f'anim_library/humanoid_set/{file}.glb').resolve()))
 r=next(o for o in bpy.data.objects if o.type=='ARMATURE');r.rotation_mode='XYZ';r.rotation_euler=(0,0,math.pi)
 for o in bpy.data.objects:
  if o.type=='MESH' and o.parent!=r:o.hide_render=True
 objs=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==clip);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 sc=bpy.context.scene;common.workbench_clay(sc);f0,f1=a.frame_range
 lo=[];hi=[]
 for f in np.linspace(f0,f1,9):
  sc.frame_set(int(f),subframe=float(f%1));l,h=common.world_bounds(objs);lo.append(list(l));hi.append(list(h))
 low=np.min(lo,0);high=np.max(hi,0);c=(low+high)*.5;size=max(high-low)*1.15
 dest=p/'review/fall_candidates'/clip;dest.mkdir(parents=True,exist_ok=True)
 for view in ('front','left','three_quarter'):
  row=[]
  for i,f in enumerate(np.linspace(f0,f1,7)):
   sc.frame_set(int(f),subframe=float(f%1))
   name=common.render_views(str(dest/f'{i}'),c[2],size,views=(view,),resolution=(420,420),target=(c[0],c[1]))[0];row.append(name)
  rows.append({'clip':clip,'view':view,'images':row})
 print('CLIP',clip,'duration',(f1-f0)/sc.render.fps)
(p/'review/fall_candidates/frames.json').write_text(json.dumps(rows,indent=2))
