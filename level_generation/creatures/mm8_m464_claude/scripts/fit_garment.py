"""Fit wardrobe geometry to the accepted F3 body and transfer its existing fitted weights."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_body.blend'));r=bpy.data.objects['Rig'];old=bpy.data.objects['Body'];old.name='AcceptedBody';r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();source=old.data;source.calc_loop_triangles();co=[v.co.copy()for v in source.vertices];tris=[t.vertices[:]for t in source.loop_triangles];tree=BVHTree.FromPolygons(co,tris,all_triangles=True)
names=[g.name for g in old.vertex_groups];source_weights=[{names[g.group]:g.weight for g in v.groups if g.weight>1e-7}for v in source.vertices]
def weights(point):
 q,no,ti,d=tree.find_nearest(point);ids=tris[ti];a,b,c=[co[i]for i in ids];v0=b-a;v1=c-a;v2=q-a;aa=v0.dot(v0);ab=v0.dot(v1);bb=v1.dot(v1);ac=v0.dot(v2);bc=v1.dot(v2);det=aa*bb-ab*ab
 u=(bb*ac-ab*bc)/det if abs(det)>1e-16 else 0;v=(aa*bc-ab*ac)/det if abs(det)>1e-16 else 0;out={}
 for i,w in zip(ids,[1-u-v,u,v]):
  for n,value in source_weights[i].items():out[n]=out.get(n,0)+max(0,w)*value
 out=sorted(out.items(),key=lambda x:-x[1])[:4];total=sum(x[1]for x in out);return {n:w/total for n,w in out}
# Append geometry only; never import or replace the accepted rig or its actions.
with bpy.data.libraries.load(str(P/'work/garment_source.blend'),link=False)as(src,dst):dst.objects=['Body']
gar=dst.objects[0];bpy.context.scene.collection.objects.link(gar);gar.name='Garments';bm=bmesh.new();bm.from_mesh(gar.data);part=bm.verts.layers.int['part']
# Head/hand anatomy stays from the accepted source. Micro trim is carried by the new textures.
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,1.42),plane_no=(0,0,1))
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[part]not in [0,2,6] or (v[part]==2 and v.co.z>1.420001)],context='VERTS')
head_ids=[i for i,v in enumerate(source.vertices)if v.co.z>1.40];head_faces=[list(t.vertices)for t in source.loop_triangles if all(i in set(head_ids)for i in t.vertices)];headtree=BVHTree.FromPolygons(co,head_faces,all_triangles=True)
# A continuous landmark warp avoids seams between independently transformed arm segments.
landmarks=[((0,.03,1.40),(-.01,-.029,1.40)),((0,.03,1.30),(-.01,-.031,1.29)),((0,.02,1.16),(-.01,-.033,1.16)),((0,.02,1.05),(-.01,-.037,1.05)),((0,.03,.88),(-.01,-.037,.87))]
for side,sign in [('L',1),('R',-1)]:
 for oldname,newp in [('UpperArm',(sign*.152,.030,1.322)),('Forearm',(sign*.275,.018,1.140)),('Hand',(sign*.393,.000,.936)),('Thigh',(sign*.09,.030,.89)),('Calf',(sign*.19,.015,.515)),('Foot',(sign*.23,.035,.125))]:landmarks.append((newp,tuple(r.data.bones[f'B_{side}_{oldname}'].head_local)))
 for yy,ty in [(-.17,-.16),(.07,.035)]:landmarks.append(((sign*.235,yy,.02),(sign*.15,ty,.02)))
A=np.array([a for a,b in landmarks]);B=np.array([b for a,b in landmarks]);dist=np.linalg.norm(A[:,None]-A[None,:],axis=2);K=dist**2*np.log(np.maximum(dist,1e-9));linear=np.c_[np.ones(len(A)),A];system=np.block([[K+np.eye(len(A))*1e-7,linear],[linear.T,np.zeros((4,4))]]);coef=np.linalg.solve(system,np.r_[B-A,np.zeros((4,3))]);assert np.max(abs(system@coef-np.r_[B-A,np.zeros((4,3))]))<1e-6
for v in bm.verts:
 p=v.co.copy()
 if v[part]==6:
  p+=Vector((-.006,-.060,0));q,n,_,dist=headtree.find_nearest(p);p=q+n*(.008+min(.004,dist*.08))
 else:
  point=np.array(p);d=np.linalg.norm(point-A,axis=1);delta=np.r_[d*d*np.log(np.maximum(d,1e-9)),1,point]@coef;p+=Vector(delta)
  if point[2]<.05:p.z=float(point[2])
 v.co=p
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(gar.data);bm.free()
# New garment vertices borrow the accepted skin's barycentric weights; hair stays rigid on the head.
for n in names:gar.vertex_groups.new(name=n)
partvals=[a.value for a in gar.data.attributes['part'].data]
for v,pid in zip(gar.data.vertices,partvals):
 w={'B_Head':1.0}if pid==6 else weights(v.co)
 for n,value in w.items():gar.vertex_groups[n].add([v.index],float(value),'REPLACE')
mod=gar.modifiers.new('AcceptedRig','ARMATURE');mod.object=r;gar.parent=r
# Keep source face/neck and both hands, with the same vertices, UVs and finger weights.
bm=bmesh.new();bm.from_mesh(old.data);piece=bm.verts.layers.int['piece']
remove=[]
for v in bm.verts:
 if v.co.z>1.372:continue
 if v[piece]in [4,5]:
  side='L'if v[piece]==4 else'R';w=r.data.bones[f'B_{side}_Hand'].head_local;e=r.data.bones[f'B_{side}_Forearm'].head_local;axis=(w-e).normalized()
  if (v.co-w).dot(axis)>-.018:continue
 remove.append(v)
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(old.data);bm.free()
# Mark material ownership before joining; all retained head UVs stay unchanged.
for obj in [old,gar]:
 obj.data.materials.clear()
 for label in ['VampirePeasant_A','VampirePeasantHead_A']:
  mat=bpy.data.materials.get(label)or bpy.data.materials.new(label);mat.use_nodes=True;mat.diffuse_color=(.60,.65,.65,1);obj.data.materials.append(mat)
 for f in obj.data.polygons:f.material_index=int(sum(obj.data.vertices[i].co.z for i in f.vertices)/len(f.vertices)>1.372);f.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');old.select_set(True);gar.select_set(True);bpy.context.view_layer.objects.active=old;bpy.ops.object.join();old.name=old.data.name='Body'
# Strip unused helper bones/tracks while preserving the original fitted anatomy and actions.
used={old.vertex_groups[g.group].name for v in old.data.vertices for g in v.groups if g.weight>1e-6};bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');removed=[]
for bone in list(r.data.edit_bones):
 if bone.name.startswith(('Sari','Skirt','Braid','Knife'))and bone.name not in used:removed.append(bone.name);r.data.edit_bones.remove(bone)
bpy.ops.object.mode_set(mode='OBJECT')
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in list(bag.fcurves):
     if any('"'+n+'"'in fc.data_path for n in removed):bag.fcurves.remove(fc)
for o in list(bpy.data.objects):
 if o not in [old,r]:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_garments.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/fitted_garments'),.84,1.85,views=('front','left','back'),resolution=(650,900))
(P/'review/garment_fit.json').write_text(json.dumps({'vertices':len(old.data.vertices),'triangles':sum(len(f.vertices)-2for f in old.data.polygons),'rig_source':'mm6_mfp_codex/export/mm6_mfp.blend','anatomy_retained':'original face, neck, hands, full skeleton and source actions','garment_source':'garment_geometry_v1; fitted to original joint positions','weights':'nearest source skin triangle, interpolated and limited to 4'},indent=2))
