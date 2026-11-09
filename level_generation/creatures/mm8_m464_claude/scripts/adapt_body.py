"""Adapt the selected F3 surface and rig; new boot shells use the original ankle/calf joints."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_body.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
sc=bpy.context.scene;sc.render.fps=30;bpy.context.preferences.filepaths.save_version=0
# Retain the face, hands and original weights; ease hidden-under-sari hip corners into trousers.
bm=bmesh.new();bm.from_mesh(b.data);part=bm.verts.layers.int['piece'];bm.normal_update()
for _ in range(4):
 vs=[v for v in bm.verts if v[part]==0 and .5<v.co.z<1.01]
 bmesh.ops.smooth_vert(bm,verts=vs,factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=False)
for v in bm.verts:
 if v[part]==0 and .5<v.co.z<1.06:v.co+=v.normal*.006
# Replace the short sleeve flare by a fitted sleeve continuation; forearm surface becomes jacket fabric.
for side,sign,pid in [('L',1,4),('R',-1,5)]:
 shoulder=r.data.bones[f'B_{side}_UpperArm'].head_local;elbow=r.data.bones[f'B_{side}_Forearm'].head_local;wrist=r.data.bones[f'B_{side}_Hand'].head_local
 axis=(elbow-shoulder);length=axis.length;axis.normalize()
 for v in bm.verts:
  if v[part]!=0 or v.co.x*sign<.115 or not 1.15<v.co.z<1.34:continue
  t=(v.co-shoulder).dot(axis);center=shoulder+axis*t;rad=v.co-center
  if t>.06:
   blend=min(1,max(0,(t-.06)/.08));target=.041+(1-min(1,t/length))*.014
   if rad.length>1e-6:v.co=center+rad*(1-blend+blend*target/rad.length)
 for v in bm.verts:
  if v[part]==pid and v.co.z>wrist.z+.015:v.co+=v.normal*.004
# Fine hair volume follows the retained head, with a short nape and broken fringe silhouette.
for v in bm.verts:
 if v[part]!=0:continue
 x,y,z=v.co;hairline=1.585 if y<-.045 else 1.50 if abs(x)>.06 else 1.465
 if z>hairline:
  t=min(1,(z-hairline)/.025);v.co+=v.normal*(.006+.003*math.sin(x*145+y*132))*t
# Boots replace hidden bare feet/calf surface; never leave toe shapes showing through the shoe.
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,.475),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(b.data);bm.free()
parts=[]
for side,sign in [('L',1),('R',-1)]:
 ankle=r.data.bones[f'B_{side}_Foot'].head_local; knee=r.data.bones[f'B_{side}_Calf'].head_local
 levels=[(.004,.051,.113,-.067),(.021,.052,.114,-.067),(.044,.051,.108,-.065),(.08,.045,.084,-.048),(.135,.036,.046,-.019),(.22,.042,.049,-.010),(.34,.053,.059,-.010),(.465,.053,.057,-.011),(.485,.055,.059,-.011),(.495,.055,.059,-.011)]
 verts=[];faces=[];N=20
 for z,rx,ry,cy in levels:
  t=min(1,max(0,(z-ankle.z)/(knee.z-ankle.z)));cx=ankle.x*(1-t)+knee.x*t
  for i in range(N):
   a=2*math.pi*i/N;verts.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
 for j in range(len(levels)-1):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 faces.append(tuple(reversed(range(N))))
 me=bpy.data.meshes.new('Boot_'+side);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Boot_'+side,me);sc.collection.objects.link(ob)
 for n in [f'B_{side}_Calf',f'B_{side}_Foot',f'B_{side}_Toe0']:ob.vertex_groups.new(name=n)
 for v in me.vertices:
  t=min(1,max(0,(v.co.z-.07)/.12));ob.vertex_groups[f'B_{side}_Calf'].add([v.index],t,'REPLACE');ob.vertex_groups[f'B_{side}_Foot'].add([v.index],1-t,'REPLACE')
 for f in me.polygons:f.use_smooth=True
 attr=me.attributes.new('piece','INT','POINT');attr.data.foreach_set('value',[200+int(side=='R')]*len(me.vertices));parts.append(ob)
# Join only the new garment shells. All source skin weights remain on the same fitted rig.
bpy.ops.object.select_all(action='DESELECT');b.select_set(True)
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=b;bpy.ops.object.join()
# Remove unused source equipment and cloth bones, retaining every deforming and anatomical bone.
used={b.vertex_groups[g.group].name for v in b.data.vertices for g in v.groups if g.weight>1e-6}
bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
removed=[]
for bone in list(r.data.edit_bones):
 if bone.name.startswith(('Sari','Skirt','Braid','Knife')) and bone.name not in used:removed.append(bone.name);r.data.edit_bones.remove(bone)
bpy.ops.object.mode_set(mode='OBJECT')
# Source cloth tracks have no surviving target. Strip them before export.
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if any('"'+n+'"' in fc.data_path for n in removed):bag.fcurves.remove(fc)
# Uniform clay makes cloth construction faults visible before texture work.
b.data.materials.clear();mat=bpy.data.materials.new('VampirePeasantClay');mat.diffuse_color=(.57,.62,.62,1);mat.use_nodes=True;b.data.materials.append(mat)
for f in b.data.polygons:f.material_index=0;f.use_smooth=True
for o in list(bpy.data.objects):
 if o not in (b,r):bpy.data.objects.remove(o,do_unlink=True)
# All source vertices above the boot seam are retained; no auto-rig or replacement anatomy.
assert len(b.data.vertices)>2500 and r.data.bones.get('B_L_Hand') and not bpy.data.objects.get('KnifeAsset')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/adapted_body.blend'))
common.workbench_clay(sc);sc.display.shading.color_type='MATERIAL'
common.render_views(str(P/'review/adapted_clay'),.84,1.85,views=('front','left','back'),resolution=(650,900))
(P/'review/geometry_adaptation.json').write_text(json.dumps({'source':'mm6_mfp_codex/export/mm6_mfp.blend','kept':'head, body, arms, hands, fitted rig, accepted motion','removed':'knife, sari, braid, jewellery, bare feet','new':'boot shells; fitted sleeves, smooth trousers and short scalp volume','vertices':len(b.data.vertices),'triangles':sum(len(f.vertices)-2 for f in b.data.polygons),'removed_bones':removed},indent=2))
