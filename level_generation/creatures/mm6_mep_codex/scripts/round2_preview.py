import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sash_lod0.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
common.workbench_clay(sc,True);sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.display.shading.show_specular_highlight=False
for role,time in [('Standing',0),('Walking',.2),('Attack',.84375),('Death',1.2)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=time*30;sc.frame_set(int(f),subframe=f%1)
 common.render_views(str(P/f'review/round2/sash_{role}'),1.05,.56,views=('front','three_quarter'),resolution=(600,600))
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();piece=np.array([v.value for v in b.data.attributes['piece'].data]);out={}
for part in [0,4,12,13]:
 co=np.array([v.co[:] for v in b.data.vertices if piece[v.index]==part]);out[part]={'bounds':[co.min(0).tolist(),co.max(0).tolist()],'mean':co.mean(0).tolist()}
(P/'work/round2_head_parts.json').write_text(json.dumps(out,indent=2))
