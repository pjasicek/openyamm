import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for tier in 'abc':
 sys.argv=['render_tex.py','--',str(P/'work/master_textured_uv.blend'),str(P/f'work/tier_triton_{tier}_Triton_A.png'),f'tier_{tier}',str(P/f'work/tier_triton_{tier}_TritonHead_A.png')]
 runpy.run_path(str(P/'scripts/render_tex.py'),run_name='__main__')
