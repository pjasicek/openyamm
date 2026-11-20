"""Views of a built cage from below (as the party sees a cage hanging overhead): LOD0 and LOD2 at 30 degrees under
the horizon, with review.py's dungeon light. Usage: blender --background work/<prop>.blend --python cage_below.py --
<prop>"""
import os
import sys

import bpy

sys.argv = sys.argv[:sys.argv.index('--') + 1] + [sys.argv[sys.argv.index('--') + 1], '0', '10']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'review.py')).read().split('lod0 = min(')[0])
lod0 = min(objects, key=lambda o: len(o.name))
lod2 = next(o for o in objects if o.name.endswith('LOD2'))
pl.render_views([lod0], out, 'below_lod0', views=((20, -30),))
pl.render_views([lod2], out, 'below_lod2', views=((20, -30),))
