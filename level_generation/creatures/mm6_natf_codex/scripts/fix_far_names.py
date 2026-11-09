import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for part in ['ForearmBlade','LeafShield']:
 path=P/f'work/far_props/{part}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));me=bpy.data.objects[part].data
 if bpy.data.meshes.get(part) is not None and bpy.data.meshes.get(part) is not me:bpy.data.meshes[part].name=part+'_Unused'
 me.name=part
 assert me.name==part
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
