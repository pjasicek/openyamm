"""Texture pass AO: bakes on the upload GLB itself (FitPose, Meshy's geometry; left limbs collapsed in UV, so they
occlude but never overwrite the right limbs' shared texels), not on the crouched rest pose.
Args: <upload glb> <out png> [reach] [size]"""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
sys.argv = ['blender', '--', mesh.name] + argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                            'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
