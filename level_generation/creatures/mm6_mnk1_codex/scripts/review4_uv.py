"""Non-overlapping bake UVs on frozen render triangles, without changing the rigged surface."""
import bpy,math,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/review4_tri.blend'));low=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for face in low.data.polygons:face.use_smooth=True
before=np.array([v.co[:] for v in low.data.vertices]);faces=[f.vertices[:] for f in low.data.polygons];low.data.uv_layers.active=low.data.uv_layers['UVMap']
for uv in list(low.data.uv_layers):
 if uv.name!='UVMap':low.data.uv_layers.remove(uv)
bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.001,area_weight=.3,correct_aspect=True,scale_to_bounds=True);bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.001);bpy.ops.object.mode_set(mode='OBJECT')
assert np.array_equal(before,np.array([v.co[:] for v in low.data.vertices])) and faces==[f.vertices[:] for f in low.data.polygons]
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/review4_rebaked.blend'))
