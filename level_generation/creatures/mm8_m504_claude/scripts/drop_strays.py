"""m504: keep only the closed body shell P00 of the Smart Topology return (P01-P06 are 20-30 vertex surface flakes
floating off the feet, hand and head). Args: -- <parts blend in/out>"""
import bpy, sys, os
p = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(p))
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'P00']:
    print('DROP', o.name, len(o.data.vertices)); bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(p))
