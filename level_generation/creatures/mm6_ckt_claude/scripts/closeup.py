"""Close-ups (head, foot, wing) textured in rest pose. Args: basecolor out_png"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
args = sys.argv[sys.argv.index('--') + 1:]
sys.argv = ['x', '--', args[0]]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apply_preview.py')).read())
rig = bpy.data.objects['Ckt_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
out = args[1]; cells = []
for name, loc, tgt, sc in (('head', (-0.6, -1.0, 0.5), (0, -0.44, 0.36), 0.25), ('foot', (-0.5, -0.9, 0.2), (0.07, -0.24, 0.02), 0.2),
                           ('wing', (0.6, -1.5, 0.45), (0.3, -0.25, 0.35), 0.45)):
    p = out.replace('.png', f'_{name}.png'); C.render_ortho(loc, tgt, sc, p, res=(400, 400), textured=True); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(400*len(ims),400))
[o.paste(im,(i*400,0)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells: os.remove(p)
