"""Larger renders of one clip at given times: side, front, three-quarter. Args: out_png clip t1,t2,..."""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
args = sys.argv[sys.argv.index('--') + 1:]
out, clip, times = args[0], args[1], [float(x) for x in args[2].split(',')]
rig = bpy.data.objects['Ckt_Rig']; rig.animation_data.action = bpy.data.actions[clip]
cells = []
for t in times:
    bpy.context.scene.frame_set(int(round(t * 24)) + 1)
    for v, loc in (('s', (-3, 0, 0.2)), ('f', (0, -3, 0.25)), ('q', (-2.2, -2.2, 1.3))):
        p = out.replace('.png', f'_{t}_{v}.png'); C.render_ortho(loc, (0, 0, 0.18), 1.2, p, res=(360, 360)); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; n=len(ims)//3; o=Image.new('RGB',(360*n,1080))
[o.paste(im,((i//3)*360,(i%3)*360)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells: os.remove(p)
