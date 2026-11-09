import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced_v1.blend'))
b=bpy.data.objects['Body'];rows=[]
for f in b.data.polygons:
 if f.center.z>2.18:
  radial=(f.center-Vector((-.035,.0,2.16))).normalized()
  rows.append((round(f.normal.dot(radial),3),f.index,list(f.center),list(f.vertices)))
print('SKULL',json.dumps(sorted(rows)[:30]))
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/skull_close'),2.21,.60,views=('front','left','three_quarter'),resolution=(700,700),target=(-.035,-.03))
