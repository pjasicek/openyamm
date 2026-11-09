"""Assemble the fitted body, independent feather rig and rigid polearm."""
from pathlib import Path
import bpy,bmesh,json,sys,math
import numpy as np
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_motion.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
with bpy.data.libraries.load(str(P/'work/neutral_wings.blend'),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith(('WingCore_','Feather_','Covert_'))]
wings=[o for o in dst.objects if o]
for o in wings:bpy.context.scene.collection.objects.link(o)
meta=json.loads((P/'work/wings.json').read_text());byname={r['name']:r for r in meta}
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
for side in ('L','R'):
 r=byname['WingCore_'+side]
 for i,n in enumerate(r['bones']):
  b=eb.new(n);b.head=r['joints'][i];b.tail=r['joints'][i+1];b.align_roll(Vector((0,-1,0)))
  b.parent=eb['B_Spine2'] if i==0 else eb[r['bones'][i-1]]
for r in meta:
 if r['kind'] not in ('primary','secondary'):continue
 b=eb.new(r['bone']);b.head=r['root'];b.tail=r['tip'];b.align_roll(Vector((0,-1,0)));b.parent=eb[r['parent']]
g=json.loads((P/'work/grip_pose_R.json').read_text())
H=eb['B_R_Hand'].matrix.copy();C=H@Vector(g['handle_centre_hand_local']);A=(H.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized()
across=(H.to_3x3()@Vector((0,1,0)));across=(across-A*across.dot(A)).normalized();normal=A.cross(across).normalized()
b=eb.new('Polearm');b.head=C;b.tail=C+A*.25;b.align_roll(normal);b.parent=eb['B_R_Hand']
bpy.ops.object.mode_set(mode='OBJECT')
for o in wings:
 r=byname[o.name];o.vertex_groups.clear()
 if r['kind']=='core':
  js=[Vector(p) for p in r['joints']];gn=[o.vertex_groups.new(name=n) for n in r['bones']]
  for v in o.data.vertices:
   candidates=[]
   for i in range(4):
    ab=js[i+1]-js[i];t=max(0,min(1,(v.co-js[i]).dot(ab)/ab.length_squared));c=js[i]+ab*t
    candidates.append(((v.co-c).length,i+t))
   _,d=min(candidates);position=max(0,min(3,d-.35));i=min(3,int(position));frac=position-i
   gn[i].add([v.index],1-frac,'REPLACE')
   if i<3 and frac>0:gn[i+1].add([v.index],frac,'REPLACE')
 else:o.vertex_groups.new(name=r['bone']).add(list(range(len(o.data.vertices))),1,'REPLACE')
for o in bpy.data.objects:o.select_set(o==body or o in wings)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
# Import and normalize the equipment independently of the humanoid rig.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/polearm_v1/model_urls_glb.glb'))
new=list(set(bpy.data.objects)-before);meshes=[o for o in new if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0]
if len(meshes)>1:bpy.ops.object.join()
prop=bpy.context.view_layer.objects.active;prop.name='PolearmMesh';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in prop.data.vertices]);scale=1.35/np.ptp(co[:,2]);co*=scale;co[:,2]-=co[:,2].min()
shaft=(co[:,2]>.25)&(co[:,2]<.8);centre=np.median(co[shaft,:2],axis=0);co[:,:2]-=centre
radius=float(np.quantile(np.linalg.norm(co[shaft,:2],axis=1),.90));co[:,:2]*=.014/radius
radial=np.linalg.norm(co[:,:2],axis=1);shaft=co[:,2]<.75
co[shaft,:2]*=np.minimum(1,.012/np.maximum(radial[shaft],1e-8))[:,None]
B=Matrix((across,normal,A)).transposed()
for v,p in zip(prop.data.vertices,co):v.co=C+B@Vector((p[0],p[1],p[2]-.32))
prop.vertex_groups.clear();prop.vertex_groups.new(name='Polearm').add(list(range(len(prop.data.vertices))),1,'REPLACE')
prop.parent=rig;mod=prop.modifiers.new('Armature','ARMATURE');mod.object=rig
for f in prop.data.polygons:f.use_smooth=True
bpy.context.scene.render.fps=30;bpy.context.scene.render.fps_base=1
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/assembled_rig.blend'))
info={'body_triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'polearm_triangles':sum(len(f.vertices)-2 for f in prop.data.polygons),'bones':len(rig.data.bones),'shaft_radius':.012,'polearm_length':1.35,'grip_from_butt':.32,'wing_controls':44}
assert info['bones']<=128 and info['body_triangles']<=15000,info
(P/'work/assembly.json').write_text(json.dumps(info,indent=2)+'\n');print('ASSEMBLY',info)
