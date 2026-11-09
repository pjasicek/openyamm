"""List the objects of an imported GLB. Args: -- <glb>"""
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.data.objects: print('OBJ', o.name, o.type, len(o.data.polygons) if o.type == 'MESH' else '')
