import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/"work/m408_textured_master.blend"))
bpy.context.scene.frame_set(0)
mesh=bpy.data.objects["Couatl"].evaluated_get(bpy.context.evaluated_depsgraph_get())
x=np.array([tuple(v.co) for v in mesh.data.vertices])
source=json.loads((P/'references_native/inventory.json').read_text())
bbox=source['sources']['m408sa2']['native_bbox']
native_height=bbox[3]-bbox[1]
assert native_height==115
report=dict(min=x.min(0).tolist(),max=x.max(0).tolist(),standing_height=float(np.ptp(x[:,2])),native_height=native_height,scale=native_height/float(np.ptp(x[:,2])))
(P/"work/scale.json").write_text(json.dumps(report,indent=2)+"\n")
print(report)
