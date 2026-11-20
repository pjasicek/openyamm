import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['render_flat.py','--',str(P/'work/master_uv.blend'),str(P/'meshy/body_retexture_v1/texture_urls_0_base_color.png'),'flat_raw',str(P/'meshy/head_retexture_v1/texture_urls_0_base_color.png')]
runpy.run_path(str(P/'scripts/render_flat.py'),run_name='__main__')
