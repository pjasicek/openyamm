import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduce_natf as red
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;objects=[bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']];sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'review/final/frames';out.mkdir(exist_ok=True)
common.workbench_clay(sc,True);sc.display.render_aa='32';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=False;sc.display.shading.show_specular_highlight=False
for ob in objects:red.preview(ob,sel[ob.name]['0']['maps'],'natf_b');ob.hide_render=False
rows={}
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];frames=np.array({'Attack':[0,.5625,.6979166667,1.10,2.15],'Hit':[0,.15,.3541666667,.45,.7],'Death':[0,.1,.2,.34,1.3]}.get(name,np.linspace(0,a.frame_range[1]/sc.render.fps,5)))*sc.render.fps;bounds=[]
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds(objects);bounds.append((lo,hi))
 lo=np.min([b[0]for b in bounds],0);hi=np.max([b[1]for b in bounds],0);center=(lo+hi)/2;span=hi-lo;height=max(1.84,span[2]*1.12,np.hypot(span[0],span[1])*1.7);rows[name]=[]
 for ix,f in enumerate(frames):
  sc.frame_set(int(f),subframe=float(f%1))
  for view in ['front','left','three_quarter']:
   file=common.render_views(str(out/f'{name}_{ix}'),center[2],height,views=(view,),resolution=(280,420),target=center[:2])[0];rows[name].append({'view':view,'frame':float(f),'path':str(Path(file).relative_to(P))})
(P/'review/final/frames.json').write_text(json.dumps(rows,indent=2))

a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
for name in ['ForearmBlade','LeafShield']:
 for ob in objects:ob.hide_render=ob.name!=name
 lo,hi=common.world_bounds([bpy.data.objects[name]]);c=(lo+hi)/2;h=max((hi-lo).z*1.15,(hi-lo).x*1.5,(hi-lo).y*1.5)
 common.render_views(str(P/'review/final'/name),c.z,h,views=('front','left','back','three_quarter'),resolution=(420,640),target=(c.x,c.y))
for ob in objects:ob.hide_render=False
for name,bone,size in [('head','B_Head',.42),('shield_grip','B_L_Hand',.34),('blade_mount','B_R_Hand',.40)]:
 c=rig.pose.bones[bone].head.copy()
 if name=='head':c.z+=.035
 common.render_views(str(P/'review/final'/name),c.z,size,views=('front','left','back','three_quarter'),resolution=(500,600),target=(c.x,c.y))

# The skirt changed at every LOD; retain equal-size silhouette/clearance comparisons.
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,True);sc.display.render_aa='32';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=False;sc.display.shading.show_specular_highlight=False
 for name in ['Body','ForearmBlade','LeafShield']:
  ob=bpy.data.objects[name];red.preview(ob,sel[name][str(level)]['maps'],'natf_a');ob.hide_render=False
 for role,time in [('Standing',0),('Running',.25),('Attack',.9375),('Hit',.3541666667),('Death',.2291666667)]:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=time*sc.render.fps;sc.frame_set(int(f),subframe=float(f%1));common.render_views(str(P/f'review/round4/lod{level}_{role}'),.88,2.1,views=('front','left'),resolution=(300,430))
