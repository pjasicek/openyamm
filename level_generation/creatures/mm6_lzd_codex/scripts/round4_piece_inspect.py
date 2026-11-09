import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for path in ['work/round4/near_runtime.blend','work/rebake/round4_lod3.blend','work/rebake/lod3_selected_baked.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));ob=bpy.data.objects['Body'];pv=np.array([x.value for x in ob.data.attributes['piece'].data]);xyz=np.array([tuple(v.co)for v in ob.data.vertices]);print('FILE',path,flush=True)
 for part in sorted(set(pv)):
  ids=pv==part;print(int(part),sum(len(f.vertices)-2 for f in ob.data.polygons if pv[f.vertices[0]]==part),np.round(xyz[ids].min(0),3).tolist(),np.round(xyz[ids].max(0),3).tolist(),flush=True)
