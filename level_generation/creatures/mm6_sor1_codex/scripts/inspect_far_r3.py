import bpy,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_lod3.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene
for i in [1,89,360,482]:
 v=b.data.vertices[i];print('VERTEX',i,v.co[:],b.data.attributes['piece'].data[i].value,[(b.vertex_groups[g.group].name,g.weight) for g in v.groups],flush=True)
r.animation_data.action=bpy.data.actions['Cast'];r.animation_data.action_slot=r.animation_data.action.slots[0];s.frame_set(62,subframe=.5);common.workbench_clay(s,textured=False);common.render_views(str(p/'review/round3/far_cast'),1.25,1.2,views=('front','left','three_quarter'),resolution=(600,600))
