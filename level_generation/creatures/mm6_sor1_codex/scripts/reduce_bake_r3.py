"""Protected geometric reduction followed by selected-to-active colour, mask, ORM and tangent normal baking."""
import bpy,bmesh,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
args=sys.argv[sys.argv.index('--')+1:];level=int(args[0]);factor=[1,.53,.24,.095][level];size=[1024,512,256,128][level]
out=p/'textures/round3';out.mkdir(exist_ok=True);review=p/'review/round3/reduction';review.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();highs={n:bpy.data.objects[n] for n in ['Body','Staff']};sources={n:o.data.copy() for n,o in highs.items()};counts={}
# The retained master carries Meshy's down-green normals; the installed GLB receipt records these two flips.
for im in bpy.data.images:
 if im.name in ['sor1_normal_1k.png','sor1_head_normal_1k.png']:
  a=np.array(im.pixels[:],np.float32).reshape(-1,4);a[:,1]=1-a[:,1];im.pixels.foreach_set(a.ravel());im.update()

from finger_clearance_r3 import fit as fit_fingers
if level==0:
 finger_report=fit_fingers(rig,highs['Body'],json.loads((p/'work/grip_pose.json').read_text()));(review/'finger_fit.json').write_text(json.dumps(finger_report,indent=2))
else:fit_fingers(rig,highs['Body'],json.loads((p/'work/grip_pose.json').read_text()))

def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def reduce_piece(high,ids,ratio,label):
 low=high.copy();low.data=high.data.copy();low.animation_data_clear();bpy.context.collection.objects.link(low);low.name=label
 bm=bmesh.new();bm.from_mesh(low.data)
 if ids is not None:
  layer=bm.verts.layers.int.get('piece');bmesh.ops.delete(bm,geom=[f for f in bm.faces if not all(v[layer] in ids for v in f.verts)],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.to_mesh(low.data);bm.free();active(low)
 co=np.array([v.co[:] for v in low.data.vertices]);protected=np.zeros(len(co),bool)
 if ids=={103,104}:
  for sd in 'LR':
   knee=rig.data.bones[f'B_{sd}_Calf'].head_local;protected|=(abs(co[:,2]-knee.z)<.09)&(abs(co[:,0]-knee.x)<.10)
 if high.name.startswith('Body'):
  for sd in 'LR':
   for bn in ['UpperArm','Forearm','Hand','Calf','Thigh']:
    pt=np.array(rig.data.bones['B_'+sd+'_'+bn].head_local);protected|=np.linalg.norm(co-pt,axis=1)<(.025 if bn in ['UpperArm','Thigh'] else .018)
  # Protect the eight-view silhouette sampled in horizontal strips, without preserving every internal fold.
  bins=np.floor(co[:,2]/.025).astype(int)
  for a in np.arange(8)*math.pi/4:
   x=co[:,0]*math.cos(a)+co[:,1]*math.sin(a)
   for z in set(bins):
    ix=np.where(bins==z)[0];protected[ix[x[ix]>=x[ix].max()-.002]]=True;protected[ix[x[ix]<=x[ix].min()+.002]]=True
  if level>0 and ids=={3,4}:
   for bone in rig.data.bones:
    if 'Finger' in bone.name:protected|=np.linalg.norm(co-np.array(bone.head_local),axis=1)<.012
  if ids=={2}:protected|=(co[:,1]<-.085)&(co[:,2]>1.5)&(co[:,2]<1.7)
 else:
  # Preserve the silhouette of the crown and the contact shaft rings at the two hands.
  protected|=np.abs(co[:,2]-np.median(co[:,2]))<.04
 vg=low.vertex_groups.new(name='_collapse');vg.add(np.where(~protected)[0].tolist(),1,'REPLACE')
 if level>0:vg.add(np.where(protected)[0].tolist(),.05,'REPLACE')
 bm=bmesh.new();bm.from_mesh(low.data);bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(2),use_dissolve_boundaries=False,verts=[],edges=list(bm.edges),delimit={'MATERIAL','SEAM','SHARP','UV'});bm.to_mesh(low.data);bm.free()
 mod=low.modifiers.new('SilhouetteCollapse','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;mod.vertex_group='_collapse';mod.vertex_group_factor=20 if level==0 or ids=={3,4} else .0001
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);low.vertex_groups.remove(low.vertex_groups['_collapse'])
 return low
body=highs['Body'];parts=set(a.value for a in body.data.attributes['piece'].data);special={1,2,3,4,5,7,8,9,10,100,101,102,103,104}
sets=[({1},1.5 if level==3 else .60),({2},.65 if level==3 else .58),({3,4},.45 if level==3 else .80),({5,7,8,9,10},.7 if level==3 else 1.),({100},.90 if level==3 else .70),({101,102},2.6 if level==3 else .85),({103,104},.16 if level==3 else .50),(parts-special,.50)]
pieces=[reduce_piece(body,ids,ratio*factor,f'BodyPart{i}') for i,(ids,ratio) in enumerate(sets) if ids]
active(pieces[0])
for o in pieces:o.select_set(True)
bpy.ops.object.join();lows={'Body':bpy.context.object};lows['Staff']=reduce_piece(highs['Staff'],None,.58*factor,'LowStaff')
if level>0:
 from staff_lods_r3 import rebuild_staff
 saved_materials=list(lows['Staff'].data.materials);rebuild_staff(lows['Staff'],scene,level)
 for m in saved_materials:lows['Staff'].data.materials.append(m)
if level>0:
 low=lows['Body'];bm=bmesh.new();bm.from_mesh(low.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer] in [103,104]],context='VERTS');bm.to_mesh(low.data);bm.free()
 from trousers_lods_r3 import add_trousers
 add_trousers(low,rig,level)
for name,low in lows.items():
 high=highs[name];high.name='High'+name;low.name=name;active(low)
 bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 # Project collapsed vertices back to their original surface, retaining the existing UV layout for the rebake.
 if name=='Body':
  pv=np.array([x.value for x in high.data.attributes['piece'].data]);verts=[v.co.copy() for v in high.data.vertices];trees={}
  for part in set(pv):
   fs=[tuple(f.vertices) for f in high.data.polygons if all(pv[i]==part for i in f.vertices)]
   if fs:trees[part]=BVHTree.FromPolygons(verts,fs)
  at=low.data.attributes['piece']
  for v in low.data.vertices:
   tree=trees.get(at.data[v.index].value)
   if tree:
    q,n,ix,d=tree.find_nearest(v.co)
    if level==0 and q is not None and d<.05:v.co=q
 # Keep the hidden trouser envelope inside the robe after collapsing its coarse rings.
 if name=='Body':
  for v in low.data.vertices:
   part=low.data.attributes['piece'].data[v.index].value
   if level==0 and part in [103,104]:
    sd='R' if part==103 else 'L';a=rig.data.bones[f'B_{sd}_Thigh'].head_local;b=rig.data.bones[f'B_{sd}_Foot'].head_local;d=b-a;u=max(0,min(1,(v.co-a).dot(d)/d.length_squared));centre=a+d*u;delta=v.co-centre;v.co=centre+delta*[.95,.70,.28,.06][level]
 if name=='Body':
  for v in low.data.vertices:
   part=low.data.attributes['piece'].data[v.index].value
   if level>0 or part not in [103,104]:continue
   sd='R' if part==103 else 'L';hip,knee,ankle=[rig.data.bones[f'B_{sd}_{b}'].head_local for b in ['Thigh','Calf','Foot']];length=(knee-hip).length+(ankle-knee).length;fraction=(knee-hip).length/length;t0=max(0,min(1,(hip.z-v.co.z)/(hip.z-ankle.z)));calf=max(0,min(1,(t0-fraction+.09)/.18));pelvis=max(0,1-t0/.18)
   for g in low.vertex_groups:g.remove([v.index])
   for n,w in [('B_Pelvis',pelvis),(f'B_{sd}_Thigh',(1-calf)*(1-pelvis)),(f'B_{sd}_Calf',calf*(1-pelvis))]:
    if w>1e-8:low.vertex_groups[n].add([v.index],w,'REPLACE')
 counts[name]={'before':sum(len(f.vertices)-2 for f in high.data.polygons),'after':sum(len(f.vertices)-2 for f in low.data.polygons)}
 # Copy material ownership; source shading stays on the unreduced surface.
 slots=[f.material_index for f in low.data.polygons]
 low.data.materials.clear()
 for m in high.data.materials:low.data.materials.append(m.copy())
 for face,slot in zip(low.data.polygons,slots):face.material_index=slot
 for i,m in enumerate(low.data.materials):m.name=high.data.materials[i].name+(f'_LOD{level}' if level else '')
# Interpolate the original cloth weights on the nearest original triangle; never snap vertices across folds.
low=lows['Body'];high=highs['Body'];high.data.calc_loop_triangles();triangles=[tuple(f.vertices) for f in high.data.loop_triangles if all(high.data.attributes['piece'].data[i].value==100 for i in f.vertices)];tree=BVHTree.FromPolygons([v.co for v in high.data.vertices],triangles,all_triangles=True);error=[]
for v in low.data.vertices:
 if low.data.attributes['piece'].data[v.index].value!=100:continue
 point,normal,ix,d=tree.find_nearest(v.co);ids=triangles[ix];a,b,c=[np.array(high.data.vertices[i].co) for i in ids];uv=np.linalg.lstsq(np.column_stack([b-a,c-a]),np.array(point)-a,rcond=None)[0];weights=np.maximum([1-uv.sum(),*uv],0);weights/=weights.sum();groups={};error.append(d)
 if level==0:v.co=point
 for g in low.vertex_groups:g.remove([v.index])
 for i,w in zip(ids,weights):
  for g in high.data.vertices[i].groups:
   n=high.vertex_groups[g.group].name;groups[n]=groups.get(n,0)+g.weight*w
 top=sorted(groups.items(),key=lambda x:-x[1])[:8];total=sum(w for n,w in top)
 for n,w in top:low.vertex_groups[n].add([v.index],float(w/total),'REPLACE')
if level>=2:
 hi=[v for v in high.data.vertices if high.data.attributes['piece'].data[v.index].value==100];hv=np.array([v.co[:] for v in hi]);snaps=[]
 for v in low.data.vertices:
  if low.data.attributes['piece'].data[v.index].value!=100:continue
  distances=np.linalg.norm(hv-np.array(v.co),axis=1);j=int(distances.argmin());source=hi[j];snaps.append(float(distances[j]));v.co=source.co
  for group in low.vertex_groups:group.remove([v.index])
  for group in source.groups:low.vertex_groups[high.vertex_groups[group.group].name].add([v.index],group.weight,'REPLACE')
 (review/f'lod{level}_exact_cloth_samples.json').write_text(json.dumps({'source_vertices':len(snaps),'max_rest_snap_mm':max(snaps)*1000,'reason':'preserve validated cloth trajectories at the sparse far-LOD samples'},indent=2))
(review/f'lod{level}_cloth_fit.json').write_text(json.dumps({'method':'barycentric original-surface cloth weight transfer','samples':len(error),'max_projection_mm':max(error)*1000,'animation_keys_unchanged':True},indent=2))
if level>0:fit_fingers(rig,lows['Body'],json.loads((p/'work/grip_pose.json').read_text()))
if level==3:
 from fit_far_silhouette_r3 import fit as fit_contour
 fit_contour(lows['Body'],lows['Staff'],rig)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.025;scene.render.bake.max_ray_distance=.10;scene.render.bake.margin=max(4,16//(2**level));scene.render.bake.use_clear=True
baked={}
for name,low in lows.items():
 high=highs[name];maps={};targetnodes=[];originalLinks=[]
 for slot,m in enumerate(high.data.materials):
  nodes=m.node_tree.nodes;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');originalLinks.append((m,bs,output))
  lm=low.data.materials[slot];target=lm.node_tree.nodes.new('ShaderNodeTexImage');targetnodes.append(target)
  maps[slot]={};mname=m.name.replace('_A','').replace('High','')
  for channel in ['basecolor','orm','normal','mask']:
   if channel=='mask' and name=='Staff':continue
   im=bpy.data.images.new(f'r3_lod{level}_{mname}_{channel}',width=size,height=size,alpha=True);im.colorspace_settings.name='sRGB' if channel=='basecolor' else 'Non-Color';im.filepath_raw=str(out/f'{im.name}.png');im.file_format='PNG';maps[slot][channel]=im
 for channel in ['basecolor','orm','normal','mask']:
  if name=='Staff' and channel=='mask':continue
  for slot,(m,bs,output) in enumerate(originalLinks):
   nodes=m.node_tree.nodes;links=m.node_tree.links
   for link in list(output.inputs['Surface'].links):links.remove(link)
   if channel=='normal':links.new(bs.outputs['BSDF'],output.inputs['Surface'])
   else:
    em=nodes.new('ShaderNodeEmission');em.name='BakeEmission';links.new(em.outputs[0],output.inputs['Surface'])
    if channel=='basecolor':src=bs.inputs['Base Color'].links[0].from_socket;links.new(src,em.inputs['Color'])
    elif channel=='orm':src=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image and 'metal_rough' in n.image.name);links.new(src.outputs['Color'],em.inputs['Color'])
    elif 'Head' not in m.name:
     src=nodes.new('ShaderNodeTexImage');src.name='BakeMaskSource';src.image=bpy.data.images.load(str(p/'textures/sor1_region_mask.png'),check_existing=True);src.image.colorspace_settings.name='Non-Color';src.image.alpha_mode='NONE';links.new(src.outputs['Color'],em.inputs['Color'])
    else:em.inputs['Color'].default_value=(0,0,0,1)
   target=targetnodes[slot];target.image=maps[slot].get(channel) or maps[slot]['orm'];low.data.materials[slot].node_tree.nodes.active=target
  for o in bpy.data.objects:
   if o.type=='MESH':o.hide_render=o not in [high,low]
  active(low);high.select_set(True)
  bpy.ops.object.bake(type='NORMAL' if channel=='normal' else 'EMIT',normal_space='TANGENT')
  for slot in maps:
   if channel in maps[slot]:maps[slot][channel].save();maps[slot][channel].pack()
  for m,bs,output in originalLinks:
   nodes=m.node_tree.nodes
   for n in list(nodes):
    if n.name in ['BakeEmission','BakeMaskSource']:nodes.remove(n)
   m.node_tree.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
  print('BAKED',level,name,channel,flush=True)
 for slot,lm in enumerate(low.data.materials):
  nodes=lm.node_tree.nodes;nodes.remove(targetnodes[slot])
  for node in nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   ch='basecolor' if 'basecolor' in node.image.name else 'normal' if 'normal' in node.image.name else 'orm' if 'metal_rough' in node.image.name else None
   if ch:node.image=maps[slot][ch]
  nodes.active=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image==maps[slot]['basecolor'])
 baked[name]={str(slot):{k:str(v.filepath_raw) for k,v in maps[slot].items()} for slot in maps}
# Keep the editable low meshes and rig only; unreduced sources remain in round3_motion.blend.
for o in highs.values():bpy.data.objects.remove(o,do_unlink=True)
for o in lows.values():o.hide_render=False
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/f'round3_lod{level}.blend'))
(review/f'lod{level}_bake.json').write_text(json.dumps({'level':level,'counts':counts,'textures':baked,'size':size,'normal_convention':'Blender tangent +Y; original Meshy green corrected before baking','method':'protected 2-degree planar dissolve + weighted collapse, surface projection, selected-to-active colour/region/ORM/tangent-normal rebake'},indent=2))
# Immediate eight-view geometric/texture comparison. Texture tier comparisons follow the actual runtime export.
if level==0:
 scene.render.film_transparent=True;common.workbench_clay(scene,textured=True);scene.render.resolution_x=scene.render.resolution_y=768;scene.render.resolution_percentage=100;lows['Staff'].hide_render=True
 cam=common.ortho_camera('ReductionCamera',(0,-6,.85),(math.pi/2,0,0),1.98);scene.camera=cam;lo=lows['Body'];candidate=lo.data
 for label,data in [('reference',sources['Body']),('candidate',candidate)]:
  lo.data=data
  for i in range(8):
   a=i*math.pi/4;cam.location=(6*math.sin(a),-6*math.cos(a),.85);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(review/f'{label}_{i}.png');bpy.ops.render.render(write_still=True)
 lo.data=candidate
print('REDUCTION',level,counts,flush=True)
