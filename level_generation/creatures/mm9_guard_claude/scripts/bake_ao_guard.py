"""AO bake on one UV layer (bake_ao_texpass.py of mm9_imp_claude). Args (Blender): <blend> <out png> <uv layer> [reach] [size]"""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
me.uv_layers.active = me.uv_layers[argv[2]]
me.uv_layers[argv[2]].active_render = True
sys.argv = ['blender', '--', 'Body', argv[1]] + argv[3:]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
