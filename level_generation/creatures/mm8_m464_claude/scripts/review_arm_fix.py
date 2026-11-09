import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/repaired_master.blend'))
r=bpy.data.objects['Rig'];s=bpy.context.scene;common.workbench_clay(s)
s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55)
for role,times in [('Running',[0,.2,.4,.6]),('Walking',[0,.6]),('Standing',[0]),('Fidget',[1]),('Hit',[.3]),('Death',[.4,1.0]),('Dead',[0])]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for t in times:
  f=t*30;s.frame_set(int(f),subframe=f%1)
  common.render_views(str(P/'review/arm_fix'/f'{role}_{t}'),1.27,.85,views=('left','right','front'),resolution=(800,800))
