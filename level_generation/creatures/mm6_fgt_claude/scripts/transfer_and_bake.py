from pathlib import Path
import runpy,sys,bpy
p=Path(__file__).resolve().parents[1];s=p/'scripts'
for src,job,dst,layer in [('rig_head_uv','retexture_v1','rig_body_uv','UVMap'),('rig_body_uv','head_retexture_v1','rig_textured','HeadUV')]:
 sys.argv=[str(s/'transfer_uv.py'),'--',str(p/'work'/f'{src}.blend'),str(p/'meshy'/job),str(p/'work'/f'{dst}.blend'),layer]
 runpy.run_path(sys.argv[0],run_name='__main__')
for layer in ('UVMap','HeadUV'):
 sys.argv=[str(s/'uv_raster.py'),'--',str(p/'work/rig_textured.blend'),layer,'1024']
 runpy.run_path(sys.argv[0],run_name='__main__')
runpy.run_path(str(s/'bake_ao_only.py'),run_name='__main__')
