"""Workbench views of the raw Meshy mesh from the front (-Y), back (+Y), right side, top. Args: out_prefix"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_rob1 as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH'); m.name = 'MeshyRaw'
for name, loc in (('front', (0, -3, 0.0)), ('back', (0, 3, 0.0)), ('right', (-3, 0, 0.0)), ('top', (0, -0.01, 3)),
                  ('q', (-2, -2.2, 1.2))):
    C.render_ortho(loc, (0, 0, 0.0), 1.3, f'{out}_{name}.png', res=(500, 500))
