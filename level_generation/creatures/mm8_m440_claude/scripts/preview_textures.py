import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['render_tex.py','--',str(P/'work/rig_textured_uv.blend'),str(P/'textures/m440_basecolor_1k.png'),'texture_v1',str(P/'textures/m440_head_basecolor_1k.png')]
runpy.run_path(str(P/'scripts/render_tex.py'),run_name='__main__')
