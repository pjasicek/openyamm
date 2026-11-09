import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('transfer_uv.py',p/'work/texture_master.blend',p/'meshy/body_retexture_v1',p/'work/textured_uv.blend','UVMap')
run('transfer_uv.py',p/'work/textured_uv.blend',p/'meshy/head_retexture_v2',p/'work/textured_uv.blend','HeadUV')
import bpy
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'));me=bpy.data.objects['Body'].data
for face in me.polygons:
 if me.attributes['head'].data[face.index].value:
  c=sum((me.vertices[i].co for i in face.vertices),__import__('mathutils').Vector())/len(face.vertices)
  me.attributes['head'].data[face.index].value=int(c.z>1.448 or (c.z>1.30 and abs(c.x)<.067 and c.y<-.03) or (c.z>1.38 and abs(c.x)<.075 and c.y>.07))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
for uv in ['UVMap','HeadUV']:run('uv_raster.py',p/'work/textured_uv.blend',uv,1024)
