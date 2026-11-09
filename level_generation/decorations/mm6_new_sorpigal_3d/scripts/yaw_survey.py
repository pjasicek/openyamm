"""Render a source model from eight yaw angles (eye level, 15 deg up) for picking the orientation that reads like the
native sprite. Args: model.gltf out_prefix"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deco_common as dc
src, prefix = sys.argv[sys.argv.index('--') + 1:]
dc.reset(); objs = [o for o in dc.import_gltf(src) if o.type == 'MESH']
dc.setup_render((320, 320))
for yaw in range(0, 360, 45):
    dc.frame_camera(objs, yaw, 15)
    dc.render(f'{prefix}_{yaw:03d}.png')
