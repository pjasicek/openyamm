"""Give exact-union seam slivers unique padded charts; do not change the surface."""
from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'))
m=bpy.context.scene.objects['Flying_Demon_Body'].data
report=json.loads((P/'review/uv_validation.json').read_text())
assert len(report['overlaps'])==6
indices=sorted({x[k][1] for x in report['overlaps'] for k in ('a','b')})
assert all(x[k][0]=='Flying_Demon_Body' for x in report['overlaps'] for k in ('a','b'))
faces=[f for f in m.polygons if f.material_index==0];uv=m.uv_layers.active.data
for cell,index in enumerate(indices):
 f=faces[index];original=np.array([tuple(uv[i].uv) for i in f.loop_indices]);delta=original-original.min(0)
 size=max(delta.max(),1e-8);delta=delta/size*.020
 offset=np.array([.32+.04*(cell%4),.84+.04*(cell//4)])
 for i,value in zip(f.loop_indices,delta+offset):uv[i].uv=value
(P/'work/boolean_uv_repair.json').write_text(json.dumps({'skin_faces':indices,'chart_size':.020,'chart_spacing':.040,'reason':'Exact-union seam slivers inherited six subpixel overlaps; each involved triangle now has a distinct padded chart.'},indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_uv_master.blend'),compress=True)
