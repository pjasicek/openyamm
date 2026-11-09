"""Workbench views of a work blend's HDR mesh: side (+X: the drone's left), front, back, top, bottom, three-quarter.
Args: -- <blend> <out_prefix> [rig]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_hdr as C
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args[0]))
out = os.path.abspath(args[1]); rig = 'HDR_Rig' if len(args) > 2 else None
c = (0, 0.0, 0.32)
for name, d in (('left', (1, 0, 0)), ('right', (-1, 0, 0)), ('front', (0, -1, 0)), ('back', (0, 1, 0)),
                ('top', (0, 0.001, 1)), ('bottom', (0, 0.001, -1)), ('q', (0.7, -0.7, 0.45))):
    loc = [c[i] + 3 * d[i] for i in range(3)]
    C.render_ortho(loc, c, 1.05, f'{out}_{name}.png', res=(560, 480), xray=bool(rig), rig_name=rig)
