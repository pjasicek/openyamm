import bpy,bmesh,json,shutil,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/review1';sel=json.loads((P/'review/reduction/selection.json').read_text());original=json.loads((W/'selection.json').read_text());rows=[]
for level,entry in enumerate([{'blend':'work/reduction_master.blend'}]+sel['body']):
 path=P/entry['blend'];backup=W/(path.stem+'_socket_first.blend')
 if not backup.exists():shutil.copyfile(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece'];uv=bm.loops.layers.uv.active
 for sd,pid in [('R',8),('L',9)]:
  roots={v for v in bm.verts if v[part]==pid and abs(v.co.x)<.185 and v.co.z>1.18};assert roots
  center=sum((v.co for v in roots),Vector())/len(roots)
  for v in roots:
   v.co.y=center.y+(v.co.y-center.y)*2.5;v.co.z=center.z+(v.co.z-center.z)*2.5
  # Borrow a plain sleeve texel patch, replacing the old deliberately darkened inside-of-sleeve bake.
  sleevefaces=[f for f in bm.faces if all(v[part]==pid for v in f.verts)]
  sample=min(sleevefaces,key=lambda f:(f.calc_center_median()-Vector((-.36 if sd=='R'else .36,.035,1.17))).length_squared)
  centeruv=sum((l[uv].uv for l in sample.loops),Vector((0,0)))/len(sample.loops)
  for f in sleevefaces:
   if any(v in roots for v in f.verts) or (sd=='R' and len(f.verts)==3 and all(-.42<v.co.x<-.40 and 1.10<v.co.z<1.16 and v.co.y>.04 for v in f.verts)):
    for i,l in enumerate(f.loops):l[uv].uv=centeruv+Vector((math.cos(i*2*math.pi/len(f.verts)),math.sin(i*2*math.pi/len(f.verts))))*.001
 # Offset closure/loop triangles by removing the least curved interior torso vertices, preserving all silhouette edges.
 target=original['body'][level-1]['triangles'] if level else 14609
 def count():return sum(len(f.verts)-2 for f in bm.faces)
 removed=0
 while count()>target:
  bm.normal_update();choices=[]
  for v in bm.verts:
   if v[part]!=1 or v.is_boundary or not (.96<v.co.z<1.22) or abs(v.co.x)>.19 or len(v.link_edges)<3:continue
   ns=[f.normal for f in v.link_faces];flat=min(a.dot(b)for a in ns for b in ns)
   choices.append((flat,v))
  assert choices,'No interior torso budget available'
  _,v=max(choices,key=lambda x:x[0]);bmesh.ops.dissolve_verts(bm,verts=[v],use_face_split=False,use_boundary_tear=False);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);removed+=1
 bm.to_mesh(o.data);bm.free();o.data.update();n=sum(len(f.vertices)-2 for f in o.data.polygons)
 if level:entry['triangles']=n
 rows.append({'file':entry['blend'],'triangles':n,'interior_torso_vertices_dissolved':removed,'closed_socket_radius_factor':2.5})
 # Keep the repaired texturing in the authoritative source as well as its exports.
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and Path(bpy.path.abspath(im.filepath)).is_file():
   if im.packed_file:im.unpack(method='REMOVE')
   im.reload()
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
(P/'review/reduction/selection.json').write_text(json.dumps(sel,indent=2));(P/'review/review1_mesh_final.json').write_text(json.dumps(rows,indent=2));print(rows,flush=True)
