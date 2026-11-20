from pathlib import Path
import sys,bpy,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced_v1.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];bpy.context.scene.frame_set(0)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/reduced_body'),.85,1.9,views=('front','left','back','three_quarter'),resolution=(550,800))
common.render_views(str(p/'review/reduced_head'),1.56,.38,views=('front','left','three_quarter'),resolution=(600,600))
sys.argv=['g4_weights.py','--',str(p/'work/reduced_v1.blend'),'reduced','Standing:0','Walking:8','Walking:25','Hit:4','Hit:10','Fidget:30','Death:20']
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
