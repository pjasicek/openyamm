"""Rest pose with bones drawn as red rods: front, side, top, three-quarter. Args: out_png"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
out = sys.argv[sys.argv.index('--') + 1]
cells = []
for name, loc, tgt in (('front', (0, -4, 0.2), (0, 0, 0.2)), ('side', (-4, 0, 0.2), (0, 0, 0.2)),
                       ('top', (0, -0.001, 4), (0, 0, 0.2)), ('q', (-2.6, -2.6, 1.6), (0, 0, 0.2))):
    p = out.replace('.png', f'_{name}.png')
    C.render_ortho(loc, tgt, 1.15, p, bones=True, res=(600, 600)); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(1200,1200))
[o.paste(im,((i%2)*600,(i//2)*600)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells: os.remove(p)
