"""Viewer copy of a turret: the actor's LOD0 (armature, clips) with its mount decoration added as a static mesh at
the shared origin (both in metres, mount bottom at z = 0). Review only, not a runtime file.
Args: -- <actor lod0 glb> <mount glb> <out glb>"""
import bpy, sys, os
actor, mount, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(actor))
bpy.ops.import_scene.gltf(filepath=os.path.abspath(mount))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', export_animations=True,
                          export_animation_mode='ACTIONS', export_yup=True)
print('VIEWERGLB', out)
