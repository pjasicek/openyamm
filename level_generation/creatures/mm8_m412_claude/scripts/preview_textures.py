import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['render_tex.py','--',str(p/'work/master_equipped.blend'),str(p/'textures/body_basecolor.png'),'texture_final',str(p/'textures/head_basecolor.png')]
runpy.run_path(str(p/'scripts/render_tex.py'),run_name='__main__')
