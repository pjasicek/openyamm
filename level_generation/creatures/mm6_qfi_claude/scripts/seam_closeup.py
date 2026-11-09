"""Close-ups of the head/neck seam on work/step2.blend, coloured by part (body grey, head blue), from four sides.
Writes review/seam_<view>.png."""
import bpy, sys, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step2.blend'))
ob = bpy.data.objects['Queen']
part = [v.value for v in ob.data.attributes['part'].data]
col = ob.data.color_attributes.new('partcol', 'BYTE_COLOR', 'CORNER')
for poly in ob.data.polygons:
    c = (0.45, 0.6, 1.0, 1.0) if part[poly.index] else (0.8, 0.8, 0.8, 1.0)
    for li in poly.loop_indices:
        col.data[li].color = c
cut = json.loads((P / 'work' / 'graft_report.json').read_text())['cut_z']
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'VERTEX'
common.render_views(str(P / 'review' / 'seam'), cut, 0.32, views=('front', 'left', 'back', 'right'), resolution=(500, 500))
