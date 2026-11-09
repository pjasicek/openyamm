import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene
last=list(o.data.vertices)[-28:];assert all(o.data.attributes['piece'].data[v.index].value==12 for v in last)
for v in last[:24]:v.co.z-=.035
for v in last[24:26]:v.co.x=-.221;v.co.z=.880
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/master.blend'));common.workbench_clay(s,True);s.display.shading.show_specular_highlight=False
for role,t in [('Standing',0),('Running',.2),('Attack',1.08),('Death',.3),('Death',1.4),('Dead',0)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*30;s.frame_set(int(f),subframe=f%1);lo,hi=common.world_bounds([o,bpy.data.objects['ClubMesh']]);mid=(lo+hi)/2;size=max(2.05,(hi-lo).length*1.08)
 common.render_views(str(P/'review/round2'/f'polished_{role}_{t}'),mid.z,size,views=('front','left'),target=(mid.x,mid.y),resolution=(600,800))
