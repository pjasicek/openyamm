"""Render actual exported tier B clips and all three native palette turnarounds."""
import bpy,json,sys,math
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/final_frames';out.mkdir(exist_ok=True);rows={v:[] for v in ['front','left','three_quarter']}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'review/viewer/mm6_mnk1_b.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;common.workbench_clay(sc,True);sc.display.shading.show_specular_highlight=False
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];name=a.name.split('@')[-1].split('|')[-1];f0,f1=a.frame_range
 for view in rows:
  row=[]
  for i in range(5):
   f=f0+(f1-f0)*i/4;sc.frame_set(int(f),subframe=f%1)
   file=common.render_views(str(out/f'{name}_{i}'),.85,2.5,views=(view,),resolution=(400,400),target=(.18,.22))[0];row.append([file,f'{name} {i/4*(f1-f0)/sc.render.fps:.2f}s'])
  rows[view].append(row)
for view,row in rows.items():(out/f'{view}.json').write_text(json.dumps(row))
for k in 'abc':
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/f'review/viewer/mm6_mnk1_{k}.glb'));sc=bpy.context.scene;common.workbench_clay(sc,True);sc.display.shading.show_specular_highlight=False
 r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=next(a for a in bpy.data.actions if a.name.endswith('Standing'));r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 common.render_views(str(out/f'tier_{k}'),.855,1.9,views=('front','left','back','three_quarter'),resolution=(512,640))
