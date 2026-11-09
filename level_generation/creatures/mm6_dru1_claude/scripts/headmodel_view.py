"""Lit renders of the head-only Meshy model (meshy/head_model_v1): front, three-quarter, face close-up. Prints its
bounding box and triangle count. Args: -- <out prefix>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
out = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', 'head_model_v1', 'model_urls_glb.glb'))
m = [o for o in bpy.data.objects if o.type == 'MESH'][0]
import numpy as np
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices])
print('HEADMODEL tris', sum(len(p.vertices) - 2 for p in m.data.polygons), 'bbox', co.min(0).round(3), co.max(0).round(3))
scene = common.setup_render((800, 800))
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.3); sun.data.energy = 3.0
c = (co.min(0) + co.max(0)) / 2; h = co.max(0)[2] - co.min(0)[2]
common.render_views(out, c[2], h * 1.05, views=('front', 'three_quarter', 'left'), resolution=(700, 700), target=(c[0], c[1]))
common.render_views(out + '_face', c[2] + h * 0.12, h * 0.4, views=('front',), resolution=(700, 700), target=(c[0], c[1]))
