"""Per-shell protected geometry candidates for the revised rebake criterion."""
import bpy,bmesh,json,sys,math
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
def counts(ob):return sum(len(f.vertices)-2 for f in ob.data.polygons)
def build(tag,ratio,level=0,bow_ratio=None,global_groups=False,major_shells=False,pose_collapse=False,source_path=None,contact_poses=(('Standing',0),('Death',31)),budget_scale=1.,piece_budgets=None):
 bpy.ops.wm.open_mainfile(filepath=str(source_path or P/'work/round3_unreduced.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();body=bpy.data.objects['Body'];source=body.copy();source.data=body.data.copy();source.name='BakeSource';bpy.context.collection.objects.link(source);source.hide_render=True
 rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear()
 critical=set();me=body.data;groups=[g.name for g in body.vertex_groups];co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);weights=np.zeros((len(co),len(groups)))
 for v in me.vertices:
  for g in v.groups:weights[v.index,g.group]=g.weight
 for side in 'LR':
  ids=np.where((co[:,2]<.13)&(weights[:,[i for i,n in enumerate(groups)if n in [f'B_{side}_Foot',f'B_{side}_Toe0']]].sum(1)>.55))[0]
  bins=np.percentile(co[ids,1],[0,34,67,100])
  for j in range(3):
   band=ids[(co[ids,1]>=bins[j])&(co[ids,1]<=bins[j+1])]
   split=np.median(co[band,0])
   for chosen in [band[co[band,0]<=split],band[co[band,0]>=split]]:
    if len(chosen):critical.add(int(min(chosen,key=lambda i:posed[i].z)))
 from mathutils.bvhtree import BVHTree
 me.calc_loop_triangles();inv=rig.data.bones['Bow'].matrix_local.inverted();local=[inv@v.co for v in me.vertices]
 wrap=[list(f.vertices)for f in me.loop_triangles if all(pv[i]==201 and abs(local[i].z)<.11 for i in f.vertices)]
 bary=np.array([[i,j,4-i-j]for i in range(5)for j in range(5-i)])/4
 for role,frame in contact_poses:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();xyz=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons(xyz.tolist(),wrap)
  for digit in [0,1,2,4]:
   mask=weights[:,[i for i,n in enumerate(groups)if n.startswith(f'B_L_Finger{digit}')]].sum(1)>.4;best=(1e9,None,None)
   for tri in me.loop_triangles:
    ids=list(tri.vertices)
    if not all(pv[i]==3 for i in ids)or not any(mask[i]for i in ids):continue
    for point in bary@xyz[ids]:
     _,_,hit,distance=tree.find_nearest(Vector(point))
     if distance<best[0]:best=(distance,ids,wrap[hit])
   critical.update(best[1]);critical.add(min(best[2],key=lambda i:np.linalg.norm(xyz[i]-xyz[best[1]].mean(0))))
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();attr=body.data.attributes.new('_source_index','INT','POINT');attr.data.foreach_set('value',list(range(len(posed))))
 if pose_collapse:
  for v in body.data.vertices:v.co=posed[v.index]
  for m in body.modifiers:m.show_viewport=False;m.show_render=False
 budgets={2:{1:540,2:220,3:205,4:195,6:50,7:60,8:60,11:40,13:30,14:30,15:24,16:36,17:36,19:16,20:16,21:16,22:16,200:620,201:392,202:22,203:12,204:12},3:{1:208,2:60,3:72,4:70,6:16,7:18,8:18,11:16,13:12,14:12,15:8,16:10,17:10,19:6,20:6,21:6,22:6,200:156,201:116,202:12,203:12,204:12}}
 if piece_budgets is not None:budgets[level]=piece_budgets
 pieces=list(budgets[level])if major_shells else [-1,-2,201,202,203,204]if global_groups else sorted(set(x.value for x in body.data.attributes['piece'].data));parts=[];report={}
 def member(value,piece):return value<200 if piece==-1 else value==200 if piece==-2 else value==piece
 for piece in pieces:
  ob=body.copy();ob.data=body.data.copy();bpy.context.collection.objects.link(ob);bm=bmesh.new();bm.from_mesh(ob.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if any(not member(v[la],piece)for v in f.verts)],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');
  if global_groups:bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
  bm.to_mesh(ob.data);bm.free()
  before=counts(ob)
  if level==3 and piece==15 and not major_shells:
   xyz=np.array([tuple(v.co)for v in ob.data.vertices]);center=xyz.mean(0);_,_,axes=np.linalg.svd(xyz-center,full_matrices=False);local=(xyz-center)@axes.T;mn,mx=local.min(0),local.max(0);mn[2]=local[:,2].mean()-.0015;mx[2]=local[:,2].mean()+.0015;corners=np.array([[x,y,z]for x in [mn[0],mx[0]]for y in [mn[1],mx[1]]for z in [mn[2],mx[2]]]);points=corners@axes+center
   bm=bmesh.new();vs=[bm.verts.new(p)for p in points];bmesh.ops.convex_hull(bm,input=vs,use_existing_faces=False);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));ob.data.clear_geometry();bm.to_mesh(ob.data);bm.free();ob.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[15]*len(ob.data.vertices));(ob.vertex_groups.get('LoinFlap')or ob.vertex_groups.new(name='LoinFlap')).add(list(range(len(ob.data.vertices))),1,'REPLACE');report[str(piece)]=[before,counts(ob)];parts.append(ob);continue
  if not before:bpy.data.objects.remove(ob,do_unlink=True);continue
  factor=(bow_ratio if bow_ratio is not None else ratio)if piece==201 else ratio
  if piece in [202,203,204]:factor=1 if level==0 else [1,.6,.3,.12][level]
  if pose_collapse and piece in [203,204]:factor=1
  if piece in [3,4]:factor=1 if level==0 else min(1,ratio*1.4)
  if piece in [9,23] and level<3:factor=1
  if piece==15 and level in [1,2]:factor=1
  if piece==200 and level==0:factor=.6
  if piece==2 and level==0:factor=1
  # Preserve small silhouette shells rather than collapsing them into degenerate points.
  minimum=2 if level==3 and piece not in [1,2,3,4,200,201,202,203,204] else 8
  factor=max(min(1,minimum/before),factor)
  if major_shells:factor=min(1,int(budgets[level][piece]*(budget_scale if piece<201 else 1))/before)
  names=[g.name for g in ob.vertex_groups];vg=ob.vertex_groups.new(name='_protect')
  inv=rig.data.bones['Bow'].matrix_local.inverted();silhouette=set()
  bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();indices=[x.value for x in ob.data.attributes['_source_index'].data]
  for v in bm.verts:v.co=posed[indices[v.index]]
  bm.normal_update()
  for e in bm.edges:
   if len(e.link_faces)!=2 or any((e.link_faces[0].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)!=(e.link_faces[1].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0) for a in np.arange(8)*math.pi/4):silhouette.update(v.index for v in e.verts)
  bm.free()
  for v in ob.data.vertices:
   w={names[g.group]:g.weight for g in v.groups if g.weight>.01};importance=0
   if len(w)>1:importance=.6
   if piece==201 and abs((inv@v.co).z)<.100:importance=.98
   if v.co.z<.018:importance=.98
   for side in 'LR':
    for bone in ['UpperArm','Forearm','Hand','Thigh','Calf']:
     if (v.co-rig.data.bones[f'B_{side}_{bone}'].head_local).length<(.04 if level<2 else .025):importance=.98
   if v.index in silhouette:importance=max(importance,.98 if level==0 else .9)
   if indices[v.index] in critical:importance=1
   if importance:vg.add([v.index],importance,'REPLACE')
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  if factor<1:
   m=ob.modifiers.new('Planar dissolve','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=math.radians(.2);m.delimit={'MATERIAL','SEAM'};bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
   m=ob.modifiers.new('Protected shell collapse','DECIMATE');m.ratio=min(1,before*factor/counts(ob));m.use_collapse_triangulate=True;m.vertex_group=vg.name if piece!=202 and not global_groups and not pose_collapse else '';m.invert_vertex_group=True;m.vertex_group_factor=1000
   bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
  # Restore the actual constraint positions and skin weights after collapse interpolation.
  used=set();ids=[v.value for v in ob.data.attributes['_source_index'].data];desired=[] if pose_collapse else [i for i in critical if member(pv[i],piece)]
  for index in desired:
   matches=[]  # Integer point attributes can interpolate during collapse; they are not stable vertex IDs.
   v=min(matches or [v for v in ob.data.vertices if v.index not in used],key=lambda v:(v.co-Vector(co[index])).length);used.add(v.index);v.co=Vector(co[index])
   for g in ob.vertex_groups:g.remove([v.index])
   for g,w in enumerate(weights[index]):
    if w>0:ob.vertex_groups[groups[g]].add([v.index],float(w),'REPLACE')
  ob.vertex_groups.remove(ob.vertex_groups['_protect']);report[str(piece)]=[before,counts(ob)];parts.append(ob)
 bpy.data.objects.remove(body,do_unlink=True);bpy.ops.object.select_all(action='DESELECT')
 for ob in parts:ob.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=parts[0];body.name='Body'
 if pose_collapse:
  from mathutils import Matrix
  a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
  matrices={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()for g in body.vertex_groups if g.name in rig.pose.bones}
  for v in body.data.vertices:
   matrix=Matrix([[0]*4 for _ in range(4)])
   for g in v.groups:
    if g.group in matrices:matrix+=matrices[g.group]*g.weight
   v.co=matrix.inverted()@v.co
  for m in body.modifiers:m.show_viewport=True;m.show_render=True
  rig.animation_data.action=None
  for b in rig.pose.bones:b.matrix_basis.identity()
  bpy.context.view_layer.update()
 bm=bmesh.new();bm.from_mesh(body.data);layer=bm.verts.layers.deform.verify();names=[g.name for g in body.vertex_groups];bad=[]
 for e in bm.edges:
  for sd in 'LR':
   hand=names.index(f'B_{sd}_Hand');distal=[i for i,n in enumerate(names)if n.startswith(f'B_{sd}_Finger')and n.endswith('2')and len(n.rsplit('Finger',1)[1])==2]
   a,b=[v[layer]for v in e.verts]
   if (a.get(hand,0)>.5 and sum(b.get(i,0)for i in distal)>.5)or(b.get(hand,0)>.5 and sum(a.get(i,0)for i in distal)>.5):bad.append(e);break
 if bad:
  old=set(bm.verts);bmesh.ops.subdivide_edges(bm,edges=bad,cuts=1,use_grid_fill=False)
  for v in set(bm.verts)-old:
   w=v[layer];tips=[(weight,i)for i,weight in w.items()if 'Finger'in names[i]and names[i].endswith('2')and len(names[i].rsplit('Finger',1)[1])==2]
   if tips:
    middle=names[max(tips)[1]][:-1]+'1';w.clear();w[names.index(middle)]=1
 bm.to_mesh(body.data);bm.free()
 bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 ref=source.copy();ref.data=source.data.copy();bpy.context.collection.objects.link(ref)
 for m in list(ref.modifiers):ref.modifiers.remove(m)
 m=body.modifiers.new('Smooth source normals','DATA_TRANSFER');m.object=ref;m.use_loop_data=True;m.data_types_loops={'CUSTOM_NORMAL'};m.loop_mapping='POLYINTERP_NEAREST';m.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(ref,do_unlink=True)
 # Fit the simplified skin to the source in the reviewed stance, then solve back into bind space.
 if global_groups and not pose_collapse:
  from mathutils import Matrix
  source.hide_viewport=False;act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);deps=bpy.context.evaluated_depsgraph_get();ev=source.evaluated_get(deps);m=ev.to_mesh();high=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();pvs=[v.value for v in source.data.attributes['piece'].data];trees={piece:BVHTree.FromPolygons(high,[list(f.vertices)for f in source.data.polygons if all(pvs[i]==piece for i in f.vertices)])for piece in set(pvs)}
  ev=body.evaluated_get(deps);m=ev.to_mesh();points=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();pv_low=[v.value for v in body.data.attributes['piece'].data];matrices={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()for g in body.vertex_groups if g.name in rig.pose.bones};errors=[]
  for v in body.data.vertices:
   loc,_,_,dist=trees[pv_low[v.index]].find_nearest(points[v.index]);matrix=Matrix([[0]*4 for _ in range(4)])
   for g in v.groups:
    if g.group in matrices:matrix+=matrices[g.group]*g.weight
   v.co=matrix.inverted()@loc;errors.append(dist)
  report['stance_projection_max_m']=max(errors);report['stance_projection_mean_m']=float(np.mean(errors));rig.animation_data.action=None
  for b in rig.pose.bones:b.matrix_basis.identity()
  bpy.context.view_layer.update()
 # Keep the shared animation fixed: settle only reduced geometry that crossed the corpse floor.
 a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=[v.co.copy()for v in mesh.vertices];ev.to_mesh_clear();piece_values=[v.value for v in body.data.attributes['piece'].data];matrices={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()for g in body.vertex_groups if g.name in rig.pose.bones}
 from mathutils import Matrix
 floor_ids=[i for i,v in enumerate(posed)if piece_values[i]!=202 and v.z<.0004]
 if not floor_ids and min(v.z for i,v in enumerate(posed)if piece_values[i]<201)>.01:floor_ids=[min((i for i in range(len(posed))if piece_values[i]<201),key=lambda i:posed[i].z)]
 for i in floor_ids:
  v=body.data.vertices[i];matrix=Matrix([[0]*4 for _ in range(4)])
  for g in v.groups:
   if g.group in matrices:matrix+=matrices[g.group]*g.weight
  v.co+=matrix.to_3x3().inverted()@Vector((0,0,.0005-posed[i].z))
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();source.hide_viewport=True;source.hide_render=True
 path=P/f'work/rebake/{tag}.blend';path.parent.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(path))
 pv_final=[v.value for v in body.data.attributes['piece'].data];report['body']=sum(len(f.vertices)-2 for f in body.data.polygons if pv_final[f.vertices[0]]!=201);report['bow']=sum(len(f.vertices)-2 for f in body.data.polygons if pv_final[f.vertices[0]]==201);(P/f'review/rebake/{tag}_counts.json').write_text(json.dumps(report,indent=2));print('SHELL_REDUCTION',tag,report,flush=True)
 return path
if __name__=='__main__':
 (P/'review/rebake').mkdir(exist_ok=True)
 from round3_candidate_gates import check
 path=build('near60',.6,0,.7);r=check(path);(P/'review/rebake/near60_gates.json').write_text(json.dumps(r,indent=2));print('NEAR60_GATES',r['passed'],{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
