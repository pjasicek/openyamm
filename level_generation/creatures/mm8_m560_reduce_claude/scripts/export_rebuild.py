"""work/<blend> (default rebuild.blend, object Rebuilt) + rig -> a skinned GLB. With clips (preview, for glb_close.py)
or without (REA_CLIPS=0, for the runtime swap). The mesh node is named Wyvern like the installed one.
Usage: blender -b -P export_rebuild.py -- <out.glb> [blend]"""
import os, sys, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[1] if len(args) > 1 else 'rebuild.blend'))
rig = bpy.data.objects['Rig']; obj = bpy.data.objects['Rebuilt']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not obj:
        o.name = 'Old_' + o.name
obj.name = 'Wyvern'
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
clips = os.environ.get('REA_CLIPS', '1') == '1'
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, args[0]), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=clips, export_animation_mode='ACTIONS', export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False,
                          export_image_format='AUTO' if clips else 'NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in obj.data.polygons))
