"""One protected candidate and eight fixed-camera textured renders, always compared to the accepted mesh."""
import bpy,bmesh,json,math,sys,os
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
part,level_s,step_s=os.environ['FIGC_REDUCE'].split(',');level=int(level_s);step=float(step_s);ratio=.9**step;tag=f'{part.lower()}_l{level}_s{step:05.2f}'.replace('.','p')
policy=os.environ.get('FIGC_POLICY','close');tag=policy+'_'+tag
bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();ob=bpy.data.objects[part];original=sum(len(f.vertices)-2 for f in ob.data.polygons)
# The accepted material appearance is frozen; head UV remains available for normal production export.
body=bpy.data.objects['Body'];me=body.data;head=[a.value for a in me.attributes['head'].data]
for f in me.polygons:
 if head[f.index]:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
for name in ['Body','Axe','Shield']:
 obj=bpy.data.objects[name];obj.data.materials.clear()
 for material,suffix in ([('FighterChain_A',''),('FighterChainHead_A','_head')] if name=='Body' else [('FighterChainGear_A','_gear')]):
  mat=bpy.data.materials.new(material);mat.use_nodes=True;nt=mat.node_tree;img=nt.nodes.new('ShaderNodeTexImage');img.image=bpy.data.images.load(str(P/'work'/f'tier_figc_a_{material}.png'),check_existing=True);nt.links.new(img.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.nodes.active=img;obj.data.materials.append(mat)
 for f in obj.data.polygons:
  f.material_index=head[f.index] if name=='Body' else 0
  if name=='Body':f.use_smooth=True
 obj.data.uv_layers.active=obj.data.uv_layers['UVMap']
# Lock UV boundaries while keeping the surface connected; independent seam collapses open cracks.
bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table();uv=bm.loops.layers.uv.get('UVMap');uv_seams=set();parent=list(range(len(bm.faces)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for e in bm.edges:
 seam=len(e.link_loops)!=2
 if not seam:
  l,r=e.link_loops
  seam=l.face.material_index!=r.face.material_index or any((next(q for q in l.face.loops if q.vert==v)[uv].uv-next(q for q in r.face.loops if q.vert==v)[uv].uv).length>1e-6 for v in e.verts)
 if seam:uv_seams.update(v.index for v in e.verts)
 else:parent[root(e.link_faces[0].index)]=root(e.link_faces[1].index)
attr=ob.data.attributes.new('_uv_chart','INT','FACE');attr.data.foreach_set('value',[root(i) for i in range(len(parent))]);bm.free()
source=ob.copy();source.data=ob.data.copy();source.modifiers.clear();scene.collection.objects.link(source);source.hide_render=True
me=ob.data;co=np.array([tuple(v.co) for v in me.vertices]);names=[g.name for g in ob.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
hard=np.zeros(len(co),bool);critical=hard.copy();importance=np.zeros(len(co))
if part=='Body':
 pv=np.array([x.value for x in me.attributes['piece'].data]);face=(pv==0)&(co[:,2]>1.47);hands=np.isin(pv,[1,2]);deforming=W.max(1)<.995
 # Strongly favour face, hands and blended deformation loops; all source weights remain interpolated in place.
 importance[face|hands]=1;importance[deforming]=1
 for name in ['B_L_UpperArm','B_R_UpperArm','B_L_Forearm','B_R_Forearm','B_L_Calf','B_R_Calf','B_L_Thigh','B_R_Thigh']:
  joint=np.array(rig.data.bones[name].head_local);near=np.linalg.norm(co-joint,axis=1)<.065;importance[near]=1;critical|=near&deforming
 hard=face|hands|np.isin(pv,[7,8])|(W[:,[i for i,n in enumerate(names) if any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]].sum(1)>1e-6)
else:
 bone=rig.data.bones[part];centre=np.array(bone.head_local);hard=np.linalg.norm(co-centre,axis=1)<.115;critical=np.linalg.norm(co-centre,axis=1)<.045;importance[hard]=1
# Preserve visible rest-space silhouette edges in eight azimuth views, including thin prop boundaries.
bm=bmesh.new();bm.from_mesh(me);bm.normal_update();tree=BVHTree.FromBMesh(bm);sil=set();center=Vector(co.mean(0));radius=float(np.linalg.norm(co.max(0)-co.min(0)))
for i in range(8):
 d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.08)).normalized()
 for e in bm.edges:
  ns=[f.normal.dot(d) for f in e.link_faces]
  if len(ns)==1 or (min(ns)<0<max(ns)):
   mid=(e.verts[0].co+e.verts[1].co)*.5;hit=tree.ray_cast(mid+d*max(2,radius*2),-d,max(3,radius*3))[0]
   if hit is not None and (hit-mid).length<.001:sil.update(v.index for v in e.verts)
for i in sil|uv_seams:importance[i]=1
# Planar dissolves only unprotected interiors and retain UV seams and material boundaries.
eligible=[e for e in bm.edges if all(importance[v.index]<.5 for v in e.verts)]
if step:
 bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.15),use_dissolve_boundaries=False,verts=[],edges=eligible,delimit={'UV','NORMAL','MATERIAL','SEAM'})
 bm.to_mesh(me);me.update()
bm.free()
# Dissolve preserves surviving positions; rebuild importance by nearest original vertex.
from mathutils.kdtree import KDTree
kd=KDTree(len(co))
for i,v in enumerate(co):kd.insert(Vector(v),i)
kd.balance();vg=ob.vertex_groups.new(name='_reduction_protect')
for v in me.vertices:
 _,i,_=kd.find(v.co)
 if importance[i]>.5:
  strength=(1 if critical[i] else ([.97,.7,.3,.1][level] if i in uv_seams else [.98,.8,.5,.3][level])) if policy=='lod_fit' else (1 if hard[i] else .98)
  vg.add([v.index],strength,'REPLACE')
planar=sum(len(f.vertices)-2 for f in me.polygons)
if step:
 for x in bpy.data.objects:x.select_set(x==ob)
 bpy.context.view_layer.objects.active=ob;m=ob.modifiers.new('Protected reduction','DECIMATE');m.ratio=min(1,original*ratio/planar);m.use_collapse_triangulate=True;m.vertex_group=vg.name;m.invert_vertex_group=True;m.vertex_group_factor=[10,5,3,1][level]
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
# Reproject UV and split normals within each source UV chart; preserve hard edges per corner.
if step:
 from mathutils.geometry import barycentric_transform
 sm=source.data;sm.calc_loop_triangles();charts={}
 for tr in sm.loop_triangles:charts.setdefault(sm.attributes['_uv_chart'].data[tr.polygon_index].value,[]).append(tr)
 trees={k:BVHTree.FromPolygons([v.co for v in sm.vertices],[tr.vertices for tr in ts],all_triangles=True) for k,ts in charts.items()};normals=[(0,0,1)]*len(ob.data.loops)
 for f in ob.data.polygons:
  center=sum((ob.data.vertices[v].co for v in f.vertices),Vector())/len(f.vertices);chart=ob.data.attributes['_uv_chart'].data[f.index].value
  for li in f.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co;hit,n,ti,d=trees[chart].find_nearest(p.lerp(center,.001));tr=charts[chart][ti];a,b,c=[sm.vertices[v].co for v in tr.vertices]
   for layer in ob.data.uv_layers:
    uv=sm.uv_layers[layer.name].data;u,v,w=[Vector((*uv[k].uv,0)) for k in tr.loops];layer.data[li].uv=barycentric_transform(p,a,b,c,u,v,w).xy
   u,v,w=[sm.corner_normals[k].vector for k in tr.loops];normals[li]=tuple(barycentric_transform(p,a,b,c,u,v,w).normalized())
  f.use_smooth=True
 ob.data.normals_split_custom_set(normals)
bpy.data.objects.remove(source,do_unlink=True)
ob.vertex_groups.remove(ob.vertex_groups['_reduction_protect'])
# Normalize only actual joint weights, never the temporary protection mask.
for v in ob.data.vertices:
 total=sum(g.weight for g in v.groups)
 assert total>0
 for g in list(v.groups):ob.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
ob.data.name=part+'_reduction_mesh';tris=sum(len(f.vertices)-2 for f in ob.data.polygons)
record={'part':part,'level':level,'step':step,'requested_ratio':ratio,'before_triangles':original,'after_planar_dissolve':planar,'triangles':tris,'protected_vertices':int((importance>.5).sum()),'silhouette_vertices':len(sil),'mesh':ob.data.name}
path=R/'candidates'/f'{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));record['blend']=str(path.relative_to(P))
if os.environ.get('FIGC_SKIP_RENDER')=='1':
 (R/'candidates'/f'{tag}.json').write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(0)
# A fixed orthographic scale reproduces the renderer's projected body-bound diameter; attachments inherit it.
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);bpy.context.view_layer.update()
def world_coords(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(obj.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return c
# Reference body bounding diameter and camera centre are retained across every candidate.
cal=R/'camera.json'
if cal.exists():camera=json.loads(cal.read_text())
else:
 c=world_coords(body);camera={'body_diameter_m':float(np.linalg.norm(c.max(0)-c.min(0))),'centres':{n:((world_coords(bpy.data.objects[n]).max(0)+world_coords(bpy.data.objects[n]).min(0))/2).tolist() for n in ['Body','Axe','Shield']}};cal.write_text(json.dumps(camera,indent=2)+'\n')
scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=False;sh.show_cavity=False;sh.show_specular_highlight=True
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
resolution=[1024,768,384,192][level];pixels=[800,550,220,88][level];scene.render.resolution_x=resolution;scene.render.resolution_y=resolution;scene.render.resolution_percentage=100;scene.display.render_aa='32'
for x in bpy.data.objects:
 if x.type=='MESH':x.hide_render=x!=ob
center=Vector(camera['centres'][part]);scale=camera['body_diameter_m']*resolution/pixels;data=bpy.data.cameras.new('reduction_camera');data.type='ORTHO';data.ortho_scale=scale;cam=bpy.data.objects.new('reduction_camera',data);scene.collection.objects.link(cam);scene.camera=cam
out=R/'renders'/tag;out.mkdir(exist_ok=True)
for i in range(8):
 angle=i*math.pi/4;cam.location=center+Vector((math.sin(angle),-math.cos(angle),.08))*6;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'{i}.png');bpy.ops.render.render(write_still=True)
record.update(projected_body_diameter_px=pixels,render_resolution=resolution,renders=str(out.relative_to(P)))
(R/'candidates'/f'{tag}.json').write_text(json.dumps(record,indent=2)+'\n');print('REDUCTION_CANDIDATE',json.dumps(record),flush=True)
