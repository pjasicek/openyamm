import bpy,bmesh,numpy as np,shutil,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bk=P/'work/before_head_repack.blend'
if not bk.exists():shutil.copy2(P/'work/textured_master.blend',bk)
bpy.ops.wm.open_mainfile(filepath=str(bk));body=bpy.data.objects['Body'];me=body.data;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();old=np.array([tuple(v.uv)for v in me.uv_layers['HeadUV'].data]);hd=[v.value for v in me.attributes['head'].data];T=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_retexture_v1/model_urls_glb.glb'));src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([tuple(src.matrix_world@v.co)for v in src.data.vertices])
with bpy.data.libraries.load(str(P/'work/texture_master.blend'),link=False)as(a,b):b.objects=['Body']
ref=b.objects[0];Tfit=np.array([tuple(ref.matrix_world@v.co)for v in ref.data.vertices]);bpy.data.objects.remove(ref,do_unlink=True)
print('BBOX',T.min(0),T.max(0),Tfit.min(0),Tfit.max(0),flush=True);scale=np.ptp(Tfit,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(Tfit.max(0)+Tfit.min(0))/2-(S.max(0)+S.min(0))*scale/2;kd=KDTree(len(src.data.polygons))
for f in src.data.polygons:kd.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
kd.balance();uv=me.uv_layers['HeadUV'].data;suv=src.data.uv_layers.active.data;worst=0
for f in me.polygons:
 if not hd[f.index]:continue
 _,j,d=kd.find(Vector(T[list(f.vertices)].mean(0)));worst=max(worst,d);sf=src.data.polygons[j]
 if d>1e-5:
  assert f.index in (4037,4038),(f.index,d)
  # Meshy's whole-body return omitted these two head triangles. Preserve each painted triangle as its own island.
  for li in f.loop_indices:uv[li].uv=old[li]+np.array((2*(f.index-4036),2))
  print('PRESERVED TRIANGLE ISLAND',f.index,d,flush=True)
  continue
 for li,vi in zip(f.loop_indices,f.vertices):
  k=int(np.argmin(np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1)));uv[li].uv=suv[sf.loop_indices[k]].uv
assert worst<.004,worst
for o in list(bpy.data.objects):
 if o not in before:bpy.data.objects.remove(o,do_unlink=True)
ids=me.attributes.new('face_id','INT','FACE')
for f in me.polygons:ids.data[f.index].value=f.index
ob=body.copy();ob.data=me.copy();bpy.context.collection.objects.link(ob);ob.modifiers.clear();bm=bmesh.new();bm.from_mesh(ob.data);h=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[h]],context='FACES');bm.to_mesh(ob.data);bm.free();ob.data.uv_layers.active=ob.data.uv_layers['HeadUV']
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(rotate=False,margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
for f in ob.data.polygons:
 dest=me.polygons[ob.data.attributes['face_id'].data[f.index].value]
 for a,b in zip(dest.loop_indices,f.loop_indices):uv[a].uv=ob.data.uv_layers['HeadUV'].data[b].uv
bpy.data.objects.remove(ob,do_unlink=True);me.attributes.remove(me.attributes['face_id']);me.calc_loop_triangles();tr=[t for t in me.loop_triangles if hd[t.polygon_index]]
np.savez_compressed(P/'work/head_reproject.npz',old=np.array([[old[i]for i in t.loops]for t in tr]),new=np.array([[tuple(uv[i].uv)for i in t.loops]for t in tr]),xyz=np.array([[tuple(me.vertices[i].co)for i in t.vertices]for t in tr]),normals=np.array([[tuple(me.vertices[i].normal)for i in t.vertices]for t in tr]))
me.uv_layers.active=me.uv_layers['UVMap'];bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print('HEAD REPACK',len(tr),worst)
