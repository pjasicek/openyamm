from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
os.environ['FRAMES']='0'
sys.argv=['render','--',str(p/'export/mm8_ratman_lod0.glb'),'Standing',str(p/'review/textured'),'1','front,side,tq,armR']
runpy.run_path(str(p/'scripts/render_clip_glb.py'),run_name='__main__')
