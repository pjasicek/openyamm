"""UV layout PNG of a blend's HDR mesh. Args: -- <blend> <out.png>"""
import bpy, os, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
m = bpy.data.objects['HDR']; bpy.context.view_layer.objects.active = m
for o in bpy.data.objects:
    o.select_set(o == m)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.export_layout(filepath=os.path.abspath(a[1]), size=(1024, 1024), opacity=0.4, export_all=True)
print('LAYOUT', a[1])
