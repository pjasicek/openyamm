import bpy,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for script in ['export_trace_final.py','acceleration_gate.py']:
 runpy.run_path(str(p/'scripts'/script),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));ob=bpy.data.objects['Body'];pv=[x.value for x in ob.data.attributes['piece'].data]
print('PIECE_COUNTS',{x:(sum(v==x for v in pv),sum(len(f.vertices)-2 for f in ob.data.polygons if all(pv[i]==x for i in f.vertices))) for x in set(pv)},flush=True)
