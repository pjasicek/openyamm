import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for clip,frames,cameras in [('Attack','126,142','front,armR,armL'),('Dead','0','front,side')]:
 os.environ['FRAMES']=frames
 sys.argv=['render','--',str(P/'review/viewer/mm8_m632_a.glb'),clip,str(P/'review'/('textured_'+clip.lower())),'120',cameras]
 runpy.run_path(str(P/'scripts/render_clip_glb.py'),run_name='__main__')
