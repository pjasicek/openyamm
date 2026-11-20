from pathlib import Path
import bpy,sys,runpy
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/master_reduced.blend'))
body=bpy.data.objects['Body']
ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==11 and v.co.z<1.52]
low=min(body.data.vertices[i].co.z for i in ids)
for i in ids:
 v=body.data.vertices[i];v.co.z=1.45+(v.co.z-low)*(.07/(1.52-low))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/master_reduced.blend'))
sys.argv=['export_runtime.py'];runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
