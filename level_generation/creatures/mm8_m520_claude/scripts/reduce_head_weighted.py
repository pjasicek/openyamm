"""Remove floating hair specks and compare silhouette reductions before head integration."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
reports=[]
for voxel in [.02]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_voxel.blend'))
 head=bpy.data.objects['HeadSource'];bpy.context.view_layer.objects.active=head;head.select_set(True)
 mod=head.modifiers.new('Hair volume cleanup','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(head.data);todo=set(bm.verts);parts=[]
 while todo:
  seed=todo.pop();stack=[seed];component=[seed]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    w=e.other_vert(v)
    if w in todo:todo.remove(w);stack.append(w);component.append(w)
  parts.append(component)
 parts.sort(key=len,reverse=True);discard=[v for c in parts[1:] for v in c]
 print('HEAD_COMPONENTS',voxel,[len(c) for c in parts[:10]],'discard',len(discard),flush=True)
 bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(head.data);bm.free()
 mod=head.modifiers.new('Surface cleanup','SMOOTH');mod.factor=.4;mod.iterations=2;bpy.ops.object.modifier_apply(modifier=mod.name)
 tri=sum(len(f.vertices)-2 for f in head.data.polygons)
 group=head.vertex_groups.new(name='ReductionAllowance')
 for v in head.data.vertices:
  x,y,z=v.co;face=float(np.clip((.6-abs(x))/.15,0,1)*np.clip((-.05-y)/.25,0,1)*np.clip((z+.75)/.2,0,1))
  group.add([v.index],1-.92*face,'REPLACE')
 mod=head.modifiers.new('Head silhouette budget','DECIMATE');mod.ratio=6500/tri;mod.vertex_group=group.name;mod.vertex_group_factor=.03;bpy.ops.object.modifier_apply(modifier=mod.name)
 head.vertex_groups.clear()
 for f in head.data.polygons:f.use_smooth=True
 bm=bmesh.new();bm.from_mesh(head.data)
 report={'voxel_source_units':voxel,'triangles':sum(len(f.vertices)-2 for f in head.data.polygons),'removed_components':len(parts)-1,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)};bm.free();reports.append(report);print('HEAD_REDUCE',report,flush=True)
 tag='head_weighted';bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/f'{tag}.blend'))
 co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0)
 common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review'/tag),float((lo[2]+hi[2])/2),float(np.ptp(co,axis=0).max()*1.1),views=('front','left','back','three_quarter'),resolution=(650,650),target=tuple((lo[:2]+hi[:2])/2))
(p/'work/head_weighted.json').write_text(json.dumps(reports,indent=2))
