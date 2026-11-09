"""Head-set AO: ../../claude_shared/bake_creature_ao.py with HeadUV as the active (and render) UV layer.
Body faces sit at HeadUV (0, 0) (one corner texel, outside every island). Args: <blend> <mesh> <out.png> [reach] [size]"""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects[argv[1]].data
me.uv_layers.active = me.uv_layers['HeadUV']
for l in me.uv_layers:
    l.active_render = (l.name == 'HeadUV')
sys.argv = ['blender', '--'] + argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                            'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
