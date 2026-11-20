import bpy,bmesh,runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in ('step1','rig_fingers','grounded_pilots'):
 f=p/'work'/f'{n}.blend';bpy.ops.wm.open_mainfile(filepath=str(f));me=bpy.data.objects['Body'].data
 bm=bmesh.new();bm.from_mesh(me);la=bm.verts.layers.int['piece']
 faces=[f for f in bm.faces if all(v[la]==4 for v in f.verts)]
 # Mirrored source hand has inward winding, verified by signed volume.
 if sum(f.calc_area()*f.normal.dot(f.calc_center_median()) for f in faces)<0:bmesh.ops.reverse_faces(bm,faces=faces)
 bm.to_mesh(me);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(f))
runpy.run_path(str(p/'scripts/build_native_base.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/review_body_clips.py'),run_name='__main__')
