import runpy,sys,bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
runpy.run_path(str(p/'scripts/fit_monk_joints.py'),run_name='__main__')
common.workbench_clay(bpy.context.scene)
for sd,x in [('R',-.52),('L',.51)]:
 common.render_views(str(p/'review'/f'hand_mesh_{sd}'),.99,.31,views=('front','back','three_quarter'),resolution=(700,700),target=(x,-.10))
