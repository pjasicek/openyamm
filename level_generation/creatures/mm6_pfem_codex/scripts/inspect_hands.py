import bpy,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
for side,x in [('R',-.465),('L',.462)]:
 common.render_views(str(p/f'review/hand_rest_{side}'),.891,.19,views=('front','back','three_quarter'),resolution=(600,600),target=(x,-.056))
sys.argv=['fit_fingers.py','--',str(p/'work/rig_v1.blend')]
runpy.run_path(str(p/'scripts/fit_fingers.py'),run_name='__main__')
