import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for f in ['rig_textured_uv.blend','m424_textured_master.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/f))
 for o in bpy.data.objects:
  if o.type=='MESH':
   print(f,o.name,[(u.name,u.active_render,min(x.uv.x for x in u.data),max(x.uv.x for x in u.data),min(x.uv.y for x in u.data),max(x.uv.y for x in u.data)) for u in o.data.uv_layers])
