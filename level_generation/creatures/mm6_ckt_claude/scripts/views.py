"""Workbench views of a blend's 'Cockatrice' mesh: front, back, right, top, three-quarter, back three-quarter.
Args: out_png"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
out = sys.argv[sys.argv.index('--') + 1]
tex = '--textured' in sys.argv
cells = []
for name, loc in (('front', (0, -3, 0.22)), ('back', (0, 3, 0.22)), ('right', (-3, 0, 0.22)), ('top', (0, -0.01, 3)),
                  ('q', (-2, -2.2, 1.3)), ('bq', (1.8, 2.2, 1.2))):
    p = out.replace('.png', f'_{name}.png')
    C.render_ortho(loc, (0, 0, 0.22), 1.15, p, res=(420, 420), textured=tex)
    cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(420*len(ims),420))
[o.paste(im,(i*420,0)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells:
    os.remove(p)
