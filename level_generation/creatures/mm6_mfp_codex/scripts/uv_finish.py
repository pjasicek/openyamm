import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for label,layer in [('body','UVMap'),('head','HeadUV')]:
 sys.argv=['transfer_uv.py','--',str(P/'work/rig_equipped.blend'),str(P/f'meshy/{label}_retexture_v1'),str(P/'work/rig_equipped.blend'),layer];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(P/'work/rig_equipped.blend'),layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
