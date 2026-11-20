from pathlib import Path
import bpy,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
for tier in 'abc':
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/portable_{tier}.blend'))
 rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 bpy.context.scene.frame_set(8);common.workbench_clay(bpy.context.scene,textured=True)
 common.render_views(str(P/'review/textured'/f'raven_{tier}_head'),2.14,.55,views=('front','left'),resolution=(512,512))
