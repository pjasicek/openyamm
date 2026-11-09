import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import common
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
for s,x in (('L',.49),('R',-.49)):
 common.render_views(str(P/f'review/hand_geometry_{s}'),.85,.4,views=('front','left','back','right'),resolution=(600,600),target=(x,-.02))
