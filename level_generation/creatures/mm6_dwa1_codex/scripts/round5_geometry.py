"""Protected per-surface collapse prevents cheap boots and cuffs losing geometry to a dense head."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
W=P/'work/round5';R=P/'review/round5'
bpy.ops.wm.open_mainfile(filepath=str(W/'authoring_source.blend'));S.cleanup();S.reset();body=bpy.data.objects['Body'];axe=bpy.data.objects['Axe'];rig=bpy.data.objects['Rig']
S.protect(body,'body');S.protect(axe,'axe')
for ob in [body,axe]:
 group=ob.vertex_groups['_reduction_protect'];group.add([v.index for v in ob.data.vertices if any(g.group==group.index for g in v.groups)],.8,'REPLACE')
 if ob==body:
  co=np.array([v.co[:]for v in ob.data.vertices]);pv=np.array([x.value for x in ob.data.attributes['piece'].data]);names={g.index:g.name for g in ob.vertex_groups}
  hard=np.isin(pv,[11])|((pv==0)&(co[:,1]<-.06)&(co[:,2]>1.17)&(co[:,2]<1.29)&(abs(co[:,0])<.13))
  hard|=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group]or 'Finger'in names[g.group])>.1 for v in ob.data.vertices]);hard|=co[:,2]<.016;hard|=(pv==0)&(co[:,2]>1.24)
  group.add(np.flatnonzero(hard).tolist(),1,'REPLACE')
 else:
  co=np.array([v.co[:]for v in ob.data.vertices]);hand=np.array(rig.matrix_world@rig.data.bones['B_R_Hand'].head_local);d=np.linalg.norm(co-hand,axis=1);group.add(np.flatnonzero(d<d.min()+.025).tolist(),1,'REPLACE')
parts=[];source=body.data.copy()
for piece in range(14):
 ob=body.copy();ob.data=source.copy();bpy.context.scene.collection.objects.link(ob);ob.name=f'Surface_{piece}';bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]!=piece],context='VERTS');bm.to_mesh(ob.data);bm.free()
 if len(ob.data.polygons):parts.append((piece,ob,S.triangles(ob)))
 else:bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.objects.remove(body,do_unlink=True)
floors={1:879,2:773,3:1008,4:1000,5:365,6:310,7:310,8:260,9:180,10:180,11:260,12:64,13:64}
report={'source_triangles':12502,'baked_stud_triangles':1421,'steps':[]}
def collapse(ob,target):
 count=S.triangles(ob)
 if target>=count:return
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 md=ob.modifiers.new('Surface budget','DECIMATE');md.ratio=target/count;md.use_collapse_triangulate=True;md.vertex_group='_reduction_protect';md.invert_vertex_group=True;md.vertex_group_factor=5;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 gi=ob.vertex_groups['_reduction_protect'].index
 for v in ob.data.vertices:
  weights=sorted([(g.group,g.weight)for g in v.groups if g.group!=gi],key=lambda x:-x[1])[:8];total=sum(w for _,w in weights);assert total>0
  for g in list(v.groups):
   if g.group!=gi:ob.vertex_groups[g.group].remove([v.index])
  for g,w in weights:ob.vertex_groups[g].add([v.index],w/total,'REPLACE')
for step in range(1,13):
 for piece,ob,initial in parts:collapse(ob,max(floors.get(piece,0),int(initial*(.83 if piece==0 else .94)**step)))
 collapse(axe,int(2630*.9**step))
 copies=[]
 for _,ob,_ in parts:
  dup=ob.copy();dup.data=ob.data.copy();bpy.context.scene.collection.objects.link(dup);copies.append(dup)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in copies:ob.select_set(True)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();merged=bpy.context.object;merged.name='Body'
 for _,ob,_ in parts:bpy.context.scene.collection.objects.unlink(ob)
 row={'step':step,'body':S.triangles(merged),'axe':S.triangles(axe),'pieces':{str(piece):S.triangles(ob)for piece,ob,_ in parts}};report['steps'].append(row);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'step{step}.blend'));print('SURFACE_TRIAL',row,flush=True)
 bpy.data.objects.remove(merged,do_unlink=True)
 for _,ob,_ in parts:bpy.context.scene.collection.objects.link(ob)
(R/'geometry_curve.json').write_text(json.dumps(report,indent=2)+'\n')
