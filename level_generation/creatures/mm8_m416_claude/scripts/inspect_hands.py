from pathlib import Path
import bpy,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'));common.workbench_clay(bpy.context.scene)
for side,x in [('left',.48),('right',-.48)]:common.render_views(str(P/'review'/f'st_hand_{side}'),1.02,.36,views=('front','left','right'),target=(x,0),resolution=(500,500))
