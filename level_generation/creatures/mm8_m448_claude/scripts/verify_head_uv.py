from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=['uv','--',str(p/'work/rig_body_uv.blend'),str(p/'meshy/head_retexture_v1'),str(p/'work/rig_textured_uv.blend'),'HeadUV']
runpy.run_path(str(p/'scripts/transfer_uv.py'),run_name='__main__')
