"""Workbench textured close-up of an exported GLB's chest at Standing frame 0 (front, three-quarter). Args: -- <glb> <out prefix>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
glb, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Ico')):
        o.hide_render = True
sc = bpy.context.scene; common.workbench_clay(sc, textured=True)
common.render_views(out, 1.4, 0.55, views=('front', 'three_quarter'), resolution=(500, 500))
