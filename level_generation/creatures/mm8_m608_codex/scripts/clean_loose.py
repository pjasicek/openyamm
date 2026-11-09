import bpy,bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
for o in [o for o in bpy.data.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(o.data);unused=[v for v in bm.verts if not v.link_faces]
 print('UNUSED',o.name,len(unused),flush=True)
 if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
 bm.to_mesh(o.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
