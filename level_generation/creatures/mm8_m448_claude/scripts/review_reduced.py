from pathlib import Path
import sys,runpy,bpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/reduced'),.85,1.95,views=('front','left','back','three_quarter'),resolution=(1000,1000))
common.render_views(str(p/'review/reduced_head'),1.54,.43,views=('front','left'),resolution=(800,800),target=(0,-.26))
frames=[]
for action in ('Standing','Walking','Running','Attack','Hit','Death','Fidget'):
 a=bpy.data.actions[action]
 frames.extend(f'{action}:{f}' for f in range(0,int(a.frame_range[1])+1,2))
sys.argv=['g4_weights','--',str(p/'work/rig_reduced.blend'),'reduced',*frames]
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
sys.argv=['g5_hand_stretch','--',str(p/'work/rig_reduced.blend'),'Standing','Walking','Running','Attack','Hit','Death','Fidget']
runpy.run_path(str(p/'scripts/g5_hand_stretch.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/export_uploads.py'),run_name='__main__')
