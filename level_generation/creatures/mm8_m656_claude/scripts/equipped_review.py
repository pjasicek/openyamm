import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/mercenary_textured_30fps.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,True)
for name,frames in [('Standing',[0]),('Attack',[30]),('Fidget',[8,15,30]),('Death',[60,80,109])]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in frames:
  sc.frame_set(f);common.render_views(str(P/'review'/f'equipped_{name}_{f}'),.78,2.25,views=('three_quarter','left'),resolution=(500,700))
