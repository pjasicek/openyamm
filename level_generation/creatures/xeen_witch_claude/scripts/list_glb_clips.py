"""List action names of a GLB. Args: -- <glb> [filter]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(a[0]))
names = sorted(x.name for x in bpy.data.actions)
print('CLIPS', [n for n in names if len(a) < 2 or a[1].lower() in n.lower()][:60])
