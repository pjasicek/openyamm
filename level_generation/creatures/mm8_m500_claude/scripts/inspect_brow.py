import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'level_generation/creatures/mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m500.blend'))
sc=bpy.context.scene;common.workbench_clay(sc)
common.render_views(str(P/'review/brow_clay'),1.7,.65,views=('front','right'),resolution=(600,600))
