from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
for layer in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(P/'work/rig_textured_uv.blend'),layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/check_uv.py'),run_name='__main__')
