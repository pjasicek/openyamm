import shutil,runpy,json,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
shutil.copy2(P/'work/forearms_repaired.blend',P/'work/textured_uv.blend')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
me=bpy.data.objects['Body'].data;pc=[x.value for x in me.attributes['piece'].data];record=json.loads((P/'work/feedback_geometry.json').read_text())
for side,part in [('L',4),('R',5)]:
 counts={}
 for f in me.polygons:
  if pc[f.vertices[0]]==part:
   for e in f.edge_keys:counts[e]=counts.get(e,0)+1
 record['arms'][side]={'cap_vertices':sorted({v for e,n in counts.items() if n==1 for v in e}),'source':'pre-reduction arm topology'}
record['triangles']=len(me.polygons);(P/'work/feedback_geometry.json').write_text(json.dumps(record,indent=2))
for name in ['raster_feedback.py','bake_ao.py','feedback_export.py','check_cuff_caps.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
