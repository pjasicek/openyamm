import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['transfer_uv.py','--',str(P/'work/rig_equipped.blend'),str(P/'meshy/body_retexture_v2'),str(P/'work/rig_equipped.blend'),'UVMap'];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(P/'work/rig_equipped.blend'),layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/bake_textures_v2.py'),run_name='__main__')
