import bpy,bmesh,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction/selection.json').read_text())
for e in [{'blend':'work/reduction_master.blend'}]+sel['body']:
 path=P/e['blend'];backup=P/'work/review1'/(path.stem+'_before_volume.blend')
 if not backup.exists():shutil.copyfile(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 parts=[a.value for a in o.data.attributes['piece'].data]
 for v in o.data.vertices:
  if parts[v.index]not in [8,9]or abs(v.co.x)<.185:continue
  sd='R'if parts[v.index]==8 else'L';head=r.data.bones[f'B_{sd}_UpperArm'].head_local;axis=(r.data.bones[f'B_{sd}_Forearm'].head_local-head).normalized();delta=v.co-head;distance=delta.dot(axis);t=max(0,min(1,distance/.25));fade=1-t*t*(3-2*t)
  v.co+= (delta-axis*distance)*(.55*fade)
 bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece'];faces=[f for f in bm.faces if all(v[part]in[8,9]for v in f.verts)]
 for f in faces:f.smooth=True
 bmesh.ops.recalc_face_normals(bm,faces=faces);bm.to_mesh(o.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(path))
