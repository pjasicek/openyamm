"""Short-range AO of the body in its rest pose, in the body texture layout (UVMap): work/ao_body.png.
Runs claude_shared/bake_creature_ao.py on work/rig_v6.blend after making UVMap the active (bake target) layer.
Usage: blender --background work/rig_v6.blend --python scripts/bake_ao.py"""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
body = bpy.data.objects['Body']
body.data.uv_layers.active = body.data.uv_layers['UVMap']
sys.argv = [sys.argv[0], '--', 'Body', os.path.join(HERE, 'work', 'ao_body.png'), '0.03', '1024']
runpy.run_path(os.path.join(HERE, '..', 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
