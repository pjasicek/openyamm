import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
for o in bpy.data.objects:
    if o.type == 'MESH':
        print('UVLAYERS', o.name, [(l.name, l.active, l.active_render) for l in o.data.uv_layers])
