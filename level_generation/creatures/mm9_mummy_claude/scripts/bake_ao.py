"""AO on one object of uv.blend. Args: <blend> <object> <out png> [reach] [size]"""
import bpy, sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects[argv[1]]
for o in list(bpy.data.objects):
    if o is not ob and o.type == 'MESH' and o.name not in ('BodyUV', 'HeadUV'):
        bpy.data.objects.remove(o)
ob.name = 'Body'
sys.argv = ['blender', '--', 'Body'] + argv[2:]
runpy.run_path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/bake_creature_ao.py', run_name='__main__')
