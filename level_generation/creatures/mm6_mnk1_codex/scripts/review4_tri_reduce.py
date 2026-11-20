"""Silhouette-first reduction, with soft joint protection and explicit cuff boundaries."""
import bpy,bmesh,math,json,os
import numpy as np
from mathutils.kdtree import KDTree
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/round4';out.mkdir(exist_ok=True)
rows=[]
for ratio in [float(os.environ.get('REDUCE_RATIO','.64'))]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work/review4_triangulated.blend'))
 b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bm=bmesh.new();bm.from_mesh(b.data);pv=bm.verts.layers.int['piece'];old=len(bm.verts)
 for pi in set(v[pv] for v in bm.verts):bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if v[pv]==pi],dist=.00001)
 print('WELD',old,len(bm.verts),flush=True);bm.to_mesh(b.data);bm.free();bm=bmesh.new();bm.from_mesh(b.data);bm.verts.ensure_lookup_table();pv=bm.verts.layers.int['piece'];cf=bm.faces.layers.int['cuff'];deform=bm.verts.layers.deform.verify()
 group=b.vertex_groups.new(name='_protect');joints=[r.data.bones[f'B_{sd}_{part}'].head_local for sd in 'LR' for part in ['UpperArm','Forearm','Thigh','Calf']]
 contact=set();piece=[v[pv] for v in bm.verts];skin=[i for i,x in enumerate(piece) if x in [2,3]]
 for action in bpy.data.actions:
  r.animation_data.action=action;r.animation_data.action_slot=action.slots[0]
  for frame in range(0,int(action.frame_range[1])+1,2):
   bpy.context.scene.frame_set(frame);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();tree=KDTree(len(skin))
   for i in skin:tree.insert(em.vertices[i].co,i)
   tree.balance()
   for v in em.vertices:
    if piece[v.index] not in [2,3] and not (piece[v.index]==0 and abs(bm.verts[v.index].co.x+.006)>.22) and tree.find(v.co)[2]<.065:contact.add(v.index)
   ev.to_mesh_clear()
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 protected={v.index:(1. if v.index in contact or v[pv] in [2,3] else .85) for v in bm.verts if v.index in contact or v[pv] in [2,3] or any((v.co-j).length<.025 for j in joints)}
 for edge in bm.edges:
  if len(edge.link_faces)!=2 or len(set(f[cf] for f in edge.link_faces))>1:
   for v in edge.verts:protected.setdefault(v.index,.65)
 # Protect extreme silhouette samples, without locking hidden normal-crossing edges.
 coords=np.array([v.co[:] for v in bm.verts]);bands=np.floor(coords[:,2]/.025).astype(int)
 for band in np.unique(bands):
  ids=np.where(bands==band)[0]
  for angle in np.arange(8)*math.pi/4:
   values=coords[ids,:2]@np.array([math.cos(angle),math.sin(angle)])
   protected.setdefault(int(ids[np.argmax(values)]),.85)
 for v in bm.verts:
  if v.index in protected:v[deform][group.index]=protected[v.index]
 edges=[e for e in bm.edges if not any(v.index in protected for v in e.verts)]
 # Deformation strips are non-planar over time; do not dissolve across weight gradients.
 bm.to_mesh(b.data);bm.free();bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b
 mod=b.modifiers.new('Silhouette collapse','DECIMATE');mod.ratio=ratio;mod.vertex_group=group.name;mod.invert_vertex_group=True;mod.vertex_group_factor=.2;mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);b.vertex_groups.remove(b.vertex_groups["_protect"]);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 tris=sum(len(f.vertices)-2 for f in b.data.polygons);dest=p/os.environ.get('CANDIDATE','work/review4_tri.blend');bpy.ops.wm.save_as_mainfile(filepath=str(dest));rows.append(dict(ratio=ratio,triangles=tris,vertices=len(b.data.vertices),protected=len(protected),path=str(dest.relative_to(p))))
 print('REDUCED',rows[-1],flush=True)
(out/(os.environ.get('TRIAL_TAG','tri')+'_metadata.json')).write_text(json.dumps(rows,indent=2))
