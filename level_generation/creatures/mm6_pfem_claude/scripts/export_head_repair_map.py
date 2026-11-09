"""Export the selected head's surface-to-UV correspondence without changing the authoring master."""
from pathlib import Path
import bpy
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'work/final_v3.blend'), load_ui=False)
mesh = bpy.data.objects['Peasant'].data
mesh.calc_loop_triangles()
uv = mesh.uv_layers.active.data
head = mesh.attributes['head'].data
part = mesh.attributes['part'].data
triangles = [t for t in mesh.loop_triangles if head[t.polygon_index].value]
np.savez(ROOT / 'work/head_repair_uv3d.npz',
         uv=np.array([[tuple(uv[l].uv) for l in t.loops] for t in triangles], dtype=np.float32),
         xyz=np.array([[tuple(mesh.vertices[v].co) for v in t.vertices] for t in triangles], dtype=np.float32),
         part=np.array([part[t.polygon_index].value for t in triangles], dtype=np.int32),
         parts=np.array(json.loads(bpy.context.scene['pfem_parts'])))
print('HEAD_REPAIR_MAP', len(triangles))
