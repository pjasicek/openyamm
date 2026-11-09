import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['transfer_uv.py','--',str(P/'work/rig_equipped.blend'),str(P/'meshy/body_retexture_v1'),str(P/'work/rig_textured.blend')]
runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
sys.argv=['uv_raster.py','--',str(P/'work/rig_textured.blend'),'HeadUV','1024']
runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
