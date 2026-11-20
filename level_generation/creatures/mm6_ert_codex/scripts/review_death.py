import bpy,json,sys,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
common.workbench_clay(scene);scene.display.shading.color_type='OBJECT';body.color=(.55,.56,.57,1)
out=P/'review/full_motion_v1'
for name in ['Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in range(7 if name=='Death' else 1):
  f=a.frame_range[1]*i/6;scene.frame_set(math.floor(f),subframe=f%1)
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
  centre=(co.min(0)+co.max(0))/2
  common.render_views(str(out/f'{name}_fitted_{i}'),float(centre[2]),3.3,views=('left','three_quarter'),resolution=(600,500),target=centre[:2])
