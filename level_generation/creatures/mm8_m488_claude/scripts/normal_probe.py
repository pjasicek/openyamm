from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];bpy.context.view_layer.objects.active=body
for o in bpy.data.objects:o.select_set(o==body)
print('NORMALS',body.data.has_custom_normals,[a.name for a in body.data.attributes])
bpy.ops.mesh.customdata_custom_splitnormals_clear()
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/animation/cleared_normals'),1.05,2.5,views=('front','three_quarter'),resolution=(768,768))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/normals.blend'))
