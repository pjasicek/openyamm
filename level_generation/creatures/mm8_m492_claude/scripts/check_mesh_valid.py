import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
mesh=bpy.data.objects['Body'].data;copy=mesh.copy();print('MASTER_VALIDATION',copy.validate(verbose=True,clean_customdata=False),len(mesh.polygons),len(copy.polygons));bpy.data.meshes.remove(copy)
for label in ['body','head','wings']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'work'/f'{label}_upload.glb'))
 for obj in set(bpy.data.objects)-before:
  if obj.type=='MESH':
   me=obj.data;print('UPLOAD',label,len(me.vertices),len(me.polygons),me.validate(verbose=True,clean_customdata=False))
