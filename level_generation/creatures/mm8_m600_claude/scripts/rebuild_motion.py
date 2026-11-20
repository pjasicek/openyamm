import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/rig.py'),run_name='__main__')
sys.argv=['animate.py','--full']
runpy.run_path(str(P/'scripts/animate.py'),run_name='__main__')
sys.argv=['transfer_uv.py','--',str(P/'work/animated.blend'),str(P/'meshy/body_texture_v1'),str(P/'work/textured_uv.blend')]
runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
sys.argv=['uv_raster.py','--',str(P/'work/textured_uv.blend'),'UVMap','2048']
runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
