"""Export the cleaned rest mesh (no materials, no attributes) for Meshy rigging. Args: -- <blend> <out glb>"""
import bpy, sys, os
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']
for a in [a.name for a in ob.data.attributes if a.name == 'piece']:
    ob.data.attributes.remove(ob.data.attributes[a])
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=False, export_attributes=False, export_materials='NONE')
print('EXPORTED', out)
