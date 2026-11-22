"""Close-up clay renders with a 5 cm floor grid (and vertical grid planes) of a region of work/clean_v1.blend.
Usage: zoom_views.py <name> <cx> <cy> <cz> <size>  -> review/zoom_<name>_<view>.png (views front, top, side, under)"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
name = a[0]; c = [float(x) for x in a[1:4]]; s = float(a[4])
src = a[5] if len(a) > 5 else 'clean_v1.blend'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', src))
for v, d in {'front': (0, -3, 0), 'top': (0, 0, 3), 'side': (3, 0, 0), 'under': (0, 0, -3), 'back': (0, 3, 0)}.items():
    loc = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
    C.render(loc, c, s, os.path.join(HERE, 'review', f'zoom_{name}_{v}.png'), res=(600, 600), floor=(v == 'top'))
