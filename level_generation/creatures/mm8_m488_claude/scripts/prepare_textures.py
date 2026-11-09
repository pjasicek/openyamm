from pathlib import Path
import bpy,sys,runpy
p=Path(__file__).resolve().parents[1]
for name,args in [('transfer_uv.py',[str(p/'work/texture_ready.blend'),str(p/'meshy/retexture_v1'),str(p/'work/uv_body.blend')]),('transfer_uv.py',[str(p/'work/uv_body.blend'),str(p/'meshy/head_retexture_v1'),str(p/'work/uv_master.blend'),'HeadUV'])]:
 path=p/'scripts'/name;sys.argv=[str(path),'--',*args];runpy.run_path(str(path),run_name='__main__')
for layer,out in [('UVMap','ao_body.png'),('HeadUV','ao_head.png')]:
 path=p/'scripts/uv_raster.py';sys.argv=[str(path),'--',str(p/'work/uv_master.blend'),layer,'1024'];runpy.run_path(str(path),run_name='__main__')
 if layer=='HeadUV':
  im=bpy.data.images.new('HeadNoAO',1024,1024,alpha=False);im.generated_color=(1,1,1,1);im.filepath_raw=str(p/'work'/out);im.file_format='PNG';im.save();continue
 bpy.data.objects['Body'].data.uv_layers.active=bpy.data.objects['Body'].data.uv_layers[layer]
 path=p.parent/'claude_shared/bake_creature_ao.py';sys.argv=[str(path),'--','Body',str(p/'work'/out),'0.025','1024'];runpy.run_path(str(path),run_name='__main__')
