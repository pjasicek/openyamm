"""Repair coincident Meshy fragments, preserve original density and identify semantic shells."""
import sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import bpy,bmesh,numpy as np
from common import workbench_clay,render_views
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
# Meshy duplicated triangles across the finger breaks; remove these and patch the original shell.
for name in ['P109','P112','P113','P114']:
 bpy.data.objects.remove(parts.pop(name),do_unlink=True)
report={}
for name,ob in parts.items():
 bm=bmesh.new();bm.from_mesh(ob.data);before=len(bm.verts)
 if name not in ('P04','P05'):bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
 if name in ('P04','P05'):
  # Fill small finger holes; leave the proximal wrist boundary under the cuff.
  holes=[e for e in bm.edges if e.is_boundary and max(v.co.z for v in e.verts)<.91]
  filled=bmesh.ops.holes_fill(bm,edges=holes,sides=20)['faces'] if holes else []
  if filled:bmesh.ops.triangulate(bm,faces=filled)
  print('HAND',name,'welded',before-len(bm.verts),'filled',len(filled))
  assert all(min(v.co.z for v in e.verts)>.91 for e in bm.edges if e.is_boundary),name
  assert all(e.is_manifold or e.is_boundary for e in bm.edges),name
 # The rear cloak has a pinched self-intersection on +X; use the intact opposite half.
 if name=='P00':
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,0),plane_no=(1,0,0),clear_outer=True,dist=.00001)
  from mathutils import Matrix
  dup=bmesh.ops.duplicate(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces))['geom']
  mirrorverts=[v for v in dup if isinstance(v,bmesh.types.BMVert)]
  bmesh.ops.transform(bm,matrix=Matrix.Diagonal((-1,1,1,1)),verts=mirrorverts)
  bmesh.ops.reverse_faces(bm,faces=[f for f in dup if isinstance(f,bmesh.types.BMFace)])
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
 # Fix orientations on disconnected triangle patches too.
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 report[name]={'welded':before-len(bm.verts),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_boundary and not e.is_manifold for e in bm.edges)}
 bm.to_mesh(ob.data);bm.free()
 ob.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(name[1:])]*len(ob.data.vertices))
 ob.select_set(True)
# Repair the left glove's small finger opening with a fine voxel surface, then mirror it to replace the
# right glove's self-intersecting middle-finger patches. Keep dense finger geometry until weighting.
left=parts['P05']
for o in bpy.data.objects:o.select_set(o==left)
bpy.context.view_layer.objects.active=left
bm=bmesh.new();bm.from_mesh(left.data)
from mathutils import Matrix,Vector
plug=bmesh.ops.create_uvsphere(bm,u_segments=24,v_segments=16,radius=1)['verts']
bmesh.ops.transform(bm,matrix=Matrix.Diagonal((.014,.007,.024,1)),verts=plug)
bmesh.ops.translate(bm,vec=Vector((.551,-.075,.850)),verts=plug)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(left.data);bm.free()
left.data.remesh_voxel_size=.0015
left.data.use_remesh_preserve_volume=True
bpy.ops.object.voxel_remesh()
m=left.modifiers.new('Surface relaxation','SMOOTH');m.factor=.5;m.iterations=12
bpy.ops.object.modifier_apply(modifier=m.name)
(left.data.attributes.get('piece') or left.data.attributes.new('piece','INT','POINT')).data.foreach_set('value',[5]*len(left.data.vertices))
right=parts['P04'];old=right.data;right.data=left.data.copy()
for v in right.data.vertices:v.co.x=-v.co.x
bm=bmesh.new();bm.from_mesh(right.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(right.data);bm.free()
right.data.attributes['piece'].data.foreach_set('value',[4]*len(right.data.vertices))
for o in parts.values():o.select_set(True)
# Preserve each shell label while joining; weight tools and masks use these identities.
bpy.context.view_layer.objects.active=parts['P00'];bpy.ops.object.join()
body=bpy.context.view_layer.objects.active;body.name=body.data.name='Body'
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
for f in body.data.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
(p/'work/cleanup_report.json').write_text(json.dumps(report,indent=2))
workbench_clay(bpy.context.scene)
render_views(str(p/'review/clean'),.85,2.0,views=('front','back'),resolution=(900,900))
render_views(str(p/'review/clean_hand'),.878,.25,views=('front','back'),resolution=(700,700),target=(-.546,-.073))
for a in list(body.data.attributes):
 if a.name in ('piece','orig_co'):body.data.attributes.remove(a)
bpy.ops.export_scene.gltf(filepath=str(p/'export/nobl_clean_v1.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False,export_materials='NONE')
