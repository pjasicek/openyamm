import sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from rebake_render import render
for file,tag in [('work/round4/near_runtime.blend','r4_reference128'),('work/round4/far_pixels2.blend','r4_far128')]:render(P/file,tag,3,parts=('actor',),palette=('round4_shared','lzd_a'),samples=128,camera_path=P/'review/round4/camera.json')
