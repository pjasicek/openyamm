"""High-angle (55 deg) render of each LOD of an exported prop, to check the top surfaces. Args: <prop> <glb>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deco_common as dc
prop, glb = sys.argv[sys.argv.index('--') + 1:]
dc.reset(); objs = [o for o in dc.import_gltf(glb) if o.type == 'MESH']
dc.setup_render((400, 400))
for o in objs:
    o.hide_render = True
for i, o in enumerate(sorted(objs, key=lambda o: (len(o.name), o.name))):
    o.hide_render = False; dc.frame_camera([o], 20, 55)
    dc.render(os.path.join(dc.PROJECT, prop, 'review', f'top_lod{i}.png')); o.hide_render = True
