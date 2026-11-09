"""Planar cleanup and protected, weighted collapse on the fitted rest mesh."""
import bpy,bmesh,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def triangles(obj):return sum(len(f.vertices)-2 for f in obj.data.polygons)
def reduce(obj,rig,ratio,level,soft=False):
 if ratio>=.999:return {'before':triangles(obj),'after':triangles(obj)}
 before=triangles(obj);me=obj.data;protect=set();silhouette=set();co=np.array([v.co[:] for v in me.vertices]);isbody=obj.name=='Body'
 if isbody:
  # Face, fingers, soles and joint loops retain their motion/contact samples.
  protected=[g.index for g in obj.vertex_groups if any(k in g.name for k in ['Finger','Hand'])]
  contact=me.attributes.get('protect_contact')
  pv=np.array([a.value for a in me.attributes['piece'].data])
  for v in me.vertices:
   if sum(g.weight for g in v.groups if g.group in protected)>.3 or v.co.z<.035 or pv[v.index]==1 or (contact is not None and contact.data[v.index].value):protect.add(v.index)
  joints=[rig.data.bones[f'B_{s}_{n}'].head_local for s in 'RL' for n in ['UpperArm','Forearm','Thigh','Calf']]
  for v in me.vertices:
   if any((v.co-j).length<(.055 if level==0 else .025) for j in joints):protect.add(v.index)
   if (v.co.z>1.54 and v.co.y<-.075) or v.co.z>1.82:protect.add(v.index)
 else:
  for v in me.vertices:
   if .30<v.co.z<.76 and abs(v.co.x)<.035 and abs(v.co.y)<.035:protect.add(v.index)
 if level>0:protect.clear()
 # Keep silhouette edges in eight horizontal views and sharp prop outlines.
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.normal_update()
 if not isbody:
  bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(1),use_dissolve_boundaries=False,verts=list(bm.verts),edges=list(bm.edges),delimit={'NORMAL','MATERIAL'})
  bm.to_mesh(me);bm.free();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();protect={v.index for v in me.vertices if .30<v.co.z<.76 and abs(v.co.x)<.035 and abs(v.co.y)<.035}
 if level>0:protect.clear()
 # The comparison uses the relaxed pose, so protect its actual eight-view contours.
 action=rig.animation_data.action;rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0);ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();posedco=[v.co.copy() for v in posed.vertices];ev.to_mesh_clear();assert len(posedco)==len(bm.verts)
 original=[v.co.copy() for v in bm.verts]
 for v,co1 in zip(bm.verts,posedco):v.co=co1
 bm.normal_update();surface=BVHTree.FromPolygons(posedco,[tuple(f.vertices) for f in me.polygons])
 for e in bm.edges:
  if not e.is_manifold or (not isbody and e.calc_face_angle(0)>math.radians(35)):
   silhouette.update(v.index for v in e.verts);continue
  if len(e.link_faces)==2:
   for k in range(8):
    d=Vector((math.sin(k*math.pi/4),math.cos(k*math.pi/4),0))
    if e.link_faces[0].normal.dot(d)*e.link_faces[1].normal.dot(d)<0:
     mid=(e.verts[0].co+e.verts[1].co)*.5;edge=e.verts[1].co-e.verts[0].co;perp=d.cross(edge)
     if perp.length<1e-6:continue
     perp.normalize();hit=surface.ray_cast(mid+d*6,-d)[0]
     if hit is None or (hit-mid).length>.005:continue
     left=surface.ray_cast(mid+d*6+perp*.0025,-d)[0];right=surface.ray_cast(mid+d*6-perp*.0025,-d)[0]
     if (left is None)!=(right is None):protect.update(v.index for v in e.verts);break
 for v,co1 in zip(bm.verts,original):v.co=co1
 bm.normal_update();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 for v in bm.verts:v.select=v.index not in protect and v.index not in silhouette
 layer=bm.verts.layers.int.new('protected')
 for v in bm.verts:v[layer]=2 if v.index in protect else 1 if v.index in silhouette else 0
 edges=[e for e in bm.edges if all(v.select for v in e.verts)]
 bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(2),use_dissolve_boundaries=False,verts=[v for v in bm.verts if v.select],edges=edges,delimit={'NORMAL','MATERIAL','UV'})
 # Preserve the protection tag through planar changes.
 bm.to_mesh(me);bm.free();vg=obj.vertex_groups.new(name='_round1_reduce');attr=me.attributes['protected']
 for v in me.vertices:vg.add([v.index],(.025 if soft else 0.0) if attr.data[v.index].value==2 else .25 if attr.data[v.index].value==1 else 1.0,'REPLACE')
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 mod=obj.modifiers.new('Measured collapse','DECIMATE');mod.ratio=min(1,ratio*before/max(1,triangles(obj)));mod.vertex_group=vg.name;mod.vertex_group_factor=(30 if level==0 else globals().get('LOD_FACTOR',30)) if soft else (1000 if level==0 else 100);mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);obj.vertex_groups.remove(obj.vertex_groups['_round1_reduce']);me=obj.data
 if 'protected' in me.attributes:me.attributes.remove(me.attributes['protected'])
 bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 assert triangles(obj)<=before and len(me.vertices)>20
 return {'before':before,'after':triangles(obj),'protected_vertices':len(protect),'ratio':ratio,'level':level}
