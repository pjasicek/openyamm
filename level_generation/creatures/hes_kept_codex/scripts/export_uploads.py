"""Freeze neutral whole-body/head texture inputs and exact face correspondence on the animated master."""
import bpy,bmesh,sys,os,json,math,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];code='m' if kind=='male' else 'f';src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();co=np.array([v.co[:] for v in me.vertices]);pc=np.array([a.value for a in me.attributes['piece'].data]);faces=np.array([p.vertices[:] for p in me.polygons]);assert faces.shape[1]==3
cut=(rig.data.bones['B_Neck'].head_local.z+rig.data.bones['B_Head'].head_local.z)/2
extra=(10,11) if kind=='male' else (6,8,9,10,13,14)
head=((pc[faces[:,0]]==1)&(co[faces,2].min(1)>cut))|np.isin(pc[faces[:,0]],extra)
attr=me.attributes.get('head') or me.attributes.new('head','INT','FACE');attr.data.foreach_set('value',head.astype(np.int32))
layer=me.uv_layers.get('HeadUV') or me.uv_layers.new(name='HeadUV')
# Unwrap an isolated head so UV selection on the retained body cannot omit or merge its islands.
tmp=bpy.data.meshes.new('HeadUnwrap');tmp.from_pydata(co.tolist(),[],faces[head].tolist());tmp.update()
uo=bpy.data.objects.new('HeadUnwrap',tmp);bpy.context.scene.collection.objects.link(uo);tmp.uv_layers.new(name='HeadUV')
for o in bpy.data.objects:o.select_set(o==uo)
bpy.context.view_layer.objects.active=uo;bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(35),island_margin=.01,scale_to_bounds=False)
bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
# Smart projection can fold tiny concave islands. Split only overlapping faces and repack.
def overlap_faces(mesh):
 u=np.array([x.uv[:]for x in mesh.uv_layers.active.data]).reshape((-1,3,2));size=2048;owners=np.full((size,size),-1,np.int32);bad=set()
 def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
 for i,t in enumerate(u):
  a,b,c=t*size;lo=np.maximum(np.floor(t.min(0)*size).astype(int),0);hi=np.minimum(np.ceil(t.max(0)*size).astype(int),size-1)
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);p=np.stack((xx,yy),-1);den=cross(b-a,c-a);assert abs(den)>1e-8
  v=cross(p-a,c-a)/den;w=cross(b-a,p-a)/den;inside=(v>1e-5)&(w>1e-5)&(v+w<1-1e-5)
  cells=owners[lo[1]:hi[1]+1,lo[0]:hi[0]+1];old=cells[inside];prior=old[old>=0]
  if len(prior):bad.add(i);bad.update(map(int,prior))
  cells[inside]=i
 return bad
uv_split_faces=set()
for attempt in range(4):
 bad=overlap_faces(tmp)
 if not bad:break
 assert attempt<3,('Head UV self overlap',len(bad))
 uv_split_faces.update(bad)
 for fi in bad:
  for li in tmp.polygons[fi].loop_indices:tmp.uv_layers.active.data[li].uv.x+=2*(fi+1)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
assert len(tmp.polygons)==int(head.sum())
for dst,srcface in zip(np.where(head)[0],tmp.polygons):
 assert tuple(me.polygons[int(dst)].vertices)==tuple(srcface.vertices)
 for dl,sl in zip(me.polygons[int(dst)].loop_indices,srcface.loop_indices):layer.data[dl].uv=tmp.uv_layers.active.data[sl].uv
bpy.data.objects.remove(uo,do_unlink=True);bpy.data.meshes.remove(tmp)
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
layer=me.uv_layers['HeadUV'];uv=np.array([x.uv[:] for x in layer.data]).reshape((-1,3,2));assert np.isfinite(uv[head]).all() and uv[head].min()>=-1e-6 and uv[head].max()<=1+1e-6
area=abs(np.cross(uv[head,1]-uv[head,0],uv[head,2]-uv[head,0]))/2;assert area.min()>1e-12,area.min()
body_uv=next(l.name for l in me.uv_layers if l.name!='HeadUV');me.uv_layers.active=me.uv_layers[body_uv]
master=P/'work'/kind/'rig_texturing.blend';bpy.ops.wm.save_as_mainfile(filepath=str(master))
(P/'texturing').mkdir(exist_ok=True)
np.savez_compressed(P/'texturing'/f'kept_{code}_correspondence.npz',vertices=co,faces=faces,head=head,head_uv=uv,source_piece=pc[faces[:,0]])
rows=[]
for what,which_uv in [('body',body_uv),('head','HeadUV')]:
 ob=body.copy();ob.data=me.copy();bpy.context.scene.collection.objects.link(ob);ob.parent=None;ob.matrix_world=body.matrix_world.copy()
 for m in list(ob.modifiers):ob.modifiers.remove(m)
 ob.vertex_groups.clear()
 if what=='head':
  bm=bmesh.new();bm.from_mesh(ob.data);h=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[h]],context='FACES');bm.to_mesh(ob.data);bm.free()
 for name in [l.name for l in ob.data.uv_layers if l.name!=which_uv]:ob.data.uv_layers.remove(ob.data.uv_layers[name])
 for name in ('piece','source_piece','finger','head','orig_co'):
  if name in ob.data.attributes:ob.data.attributes.remove(ob.data.attributes[name])
 mat=bpy.data.materials.new('NeutralUpload');mat.use_nodes=True;mat.use_backface_culling=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.5,.5,.5,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.85
 ob.data.materials.clear();ob.data.materials.append(mat)
 for p in ob.data.polygons:p.material_index=0
 for o in bpy.data.objects:o.select_set(o==ob)
 bpy.context.view_layer.objects.active=ob;out=P/'texturing'/f'kept_{code}_{what}_upload.glb'
 bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_attributes=False,export_extras=False)
 rows.append({'path':str(out.relative_to(P)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'triangles':len(ob.data.polygons),'uv':which_uv})
 bpy.data.objects.remove(ob,do_unlink=True)
# Seam is a shared set of original edges, so body/head colour blending can match it exactly after UV transfer.
edges={}
for face,ishead in zip(faces,head):
 for i in range(3):edges.setdefault(tuple(sorted((int(face[i]),int(face[(i+1)%3])))),set()).add(bool(ishead))
seam=[list(e) for e,states in edges.items() if len(states)==2]
r={'master':str(master.relative_to(P)),'master_sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'body_triangles':len(faces),'head_triangles':int(head.sum()),'head_neck_cut_z_m':float(cut),'neck_seam_edges':seam,'head_uv_split_faces':len(uv_split_faces),'head_uv_overlap_pixels_2048':0,'head_uv_area_min':float(area.min()),'head_uv_bounds':[float(uv[head].min()),float(uv[head].max())],'uploads':rows,'correspondence':f'texturing/kept_{code}_correspondence.npz','coordinate_space':'Blender metres Z-up, front -Y; GLB Y-up front +Z','body_head_topology_identical_to_animated_master':True}
(P/'texturing'/f'kept_{code}_export.json').write_text(json.dumps(r,indent=2)+'\n');print('EXPORT',kind,len(faces),int(head.sum()),rows,flush=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
