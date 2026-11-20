"""AO bake on the texture-pass UVs (texpass_uv.py's blend): UVMap made the active and render UV layer (the master also
carries MHUV and HeadUV), then ../../../claude_shared/bake_creature_ao.py on 'Body'. The blend is not saved.
Args (Blender): <texpass blend> <out png> [reach m 0.04] [size 2048]"""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers['UVMap'].active_render = True
sys.argv = ['blender', '--', 'Body'] + argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 2), 'claude_shared',
                            'bake_creature_ao.py'), run_name='__main__')
