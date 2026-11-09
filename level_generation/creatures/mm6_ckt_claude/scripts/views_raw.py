"""Workbench views of the raw Meshy mesh, framed to its bounds. Args: out_prefix"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH'); m.name = 'MeshyRaw'
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices]); lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2
print('BOUNDS', lo.round(3), hi.round(3))
s = float((hi - lo).max()) * 1.1
for name, d in (('front', (0, -1, 0)), ('back', (0, 1, 0)), ('right', (-1, 0, 0)), ('top', (0, -0.001, 1)),
                ('q', (-0.7, -0.8, 0.45))):
    loc = tuple(c + np.array(d) * 4)
    C.render_ortho(loc, tuple(c), s, f'{out}_{name}.png', res=(600, 600))
