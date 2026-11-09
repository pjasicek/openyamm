from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced_face_v1.blend'))
me=bpy.data.objects['Body'].data
print('PRE',len(me.vertices),len(me.polygons))
print('CHANGED',me.validate(verbose=True,clean_customdata=False))
print('POST',len(me.vertices),len(me.polygons))
