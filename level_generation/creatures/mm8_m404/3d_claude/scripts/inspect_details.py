"""Close static anatomy views before choosing geometry corrections."""
from pathlib import Path
import bpy,sys,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/static_full'),0.95,2.35,views=('left','three_quarter'),resolution=(1000,1000),target=(0,-0.1))
common.render_views(str(p/'review/static_hand'),0.84,0.42,views=('front','back','left','three_quarter'),resolution=(700,700),target=(0.56,-0.65))
common.render_views(str(p/'review/static_head'),1.68,0.58,views=('front','left','three_quarter'),resolution=(700,700),target=(0,-0.73))
assert (p/'review/static_hand_front.png').is_file()
