import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
sys.argv=['transfer','--','work/equipped.blend','meshy/body_retexture_v1','work/textured_master.blend'];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ['UVMap','HeadUV','Spear','Buckler']:
 sys.argv=['raster','--','work/textured_master.blend',layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
