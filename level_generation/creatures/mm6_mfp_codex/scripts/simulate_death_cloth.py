"""Offline Blender cloth only for the fall; runtime receives ordinary bone keys."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();names=[n for n in r.pose.bones.keys()if n.startswith('Skirt_')]
# Exact skirt surface, evenly subdivided once for stable simulation.
ob=body.copy();ob.data=body.data.copy();bpy.context.collection.objects.link(ob);ob.name='SimSkirt';ob.parent=None
for mod in list(ob.modifiers):ob.modifiers.remove(mod)
bm=bmesh.new();bm.from_mesh(ob.data);pc=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pc]!=1],context='VERTS');bmesh.ops.subdivide_edges(bm,edges=bm.edges[:],cuts=1,use_grid_fill=True);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(ob.data);bm.free();ob.vertex_groups.clear();ob.vertex_groups.new(name='B_Pelvis').add(list(range(len(ob.data.vertices))),1,'REPLACE');pin=ob.vertex_groups.new(name='Pin')
for v in ob.data.vertices:
 if v.co.z>.915:pin.add([v.index],min(1,(v.co.z-.915)/.040),'REPLACE')
mod=ob.modifiers.new('Pin motion','ARMATURE');mod.object=r
rest=np.array([v.co[:]for v in ob.data.vertices]);track={n:int(np.argmin(np.linalg.norm(rest-np.array(r.data.bones[n].head_local),axis=1)))for n in names};offset={n:r.data.bones[n].head_local-Vector(rest[track[n]])for n in names}
# The exact weighted body supplies collisions, including fingers; no approximation can undersize a calf.
colliders=[];collider=body.copy();collider.data=body.data.copy();bpy.context.collection.objects.link(collider);collider.name='SimBody'
bm=bmesh.new();bm.from_mesh(collider.data);pc=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pc]not in [0,4,5,13,14,16,17]],context='VERTS');bm.to_mesh(collider.data);bm.free();collider.modifiers.new('Collision','COLLISION');collider.collision.thickness_outer=.006;collider.collision.cloth_friction=5;collider.hide_render=True;colliders.append(collider)
bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,-.010));floor=bpy.context.object;floor.name='SimFloor';floor.modifiers.new('Collision','COLLISION');floor.collision.thickness_outer=.004;floor.collision.cloth_friction=5;floor.hide_render=True
act=bpy.data.actions['Death'];nf=int(act.frame_range[1]);pre=24;settle=15
# The temporary action supplies held pre-roll followed by the source fall and a held end.
def curves(a):return [fc for l in a.layers for st in l.strips for bag in st.channelbags for fc in bag.fcurves]
timeline=act.copy();timeline.name='Death_cloth_timeline'
for fc in curves(timeline):
 for k in fc.keyframe_points:k.co.x+=pre+1;k.handle_left.x+=pre+1;k.handle_right.x+=pre+1
r.animation_data.action=timeline;r.animation_data.action_slot=timeline.slots[0]
cloth=ob.modifiers.new('Cloth','CLOTH');c=cloth.settings;c.quality=10;c.mass=.18;c.air_damping=3;c.tension_stiffness=30;c.compression_stiffness=25;c.shear_stiffness=15;c.bending_stiffness=.8;c.tension_damping=8;c.compression_damping=8;c.shear_damping=8;c.bending_damping=2;c.vertex_group_mass='Pin';c.pin_stiffness=1
cc=cloth.collision_settings;cc.use_collision=True;cc.distance_min=.005;cc.collision_quality=5;cc.use_self_collision=True;cc.self_distance_min=.004
cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=pre+1+nf+settle;sc.frame_start=1;sc.frame_end=cloth.point_cache.frame_end
# Control frames from circumferential and longitudinal surface directions.
def frame(points,j,c):
 n=f'Skirt_{j}_{c}';pc=Vector(points[track[n]]);side=Vector(points[track[f'Skirt_{j}_{(c+1)%12}']])-Vector(points[track[f'Skirt_{j}_{(c-1)%12}']]);down=Vector(points[track[f'Skirt_{min(j+1,2)}_{c}']])-Vector(points[track[f'Skirt_{max(j-1,0)}_{c}']]);x=side.normalized();z=x.cross(down).normalized();y=z.cross(x).normalized();return pc,Matrix((x,y,z)).transposed()
restframe={n:frame(rest,int(n.split('_')[1]),int(n.split('_')[2]))[1]for n in names};samples=[]
for f in range(1,sc.frame_end+1):
 sc.frame_set(f);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear()
 if f>=pre+1:
  row={}
  for n in names:
   j,c=map(int,n.split('_')[1:]);pt,F=frame(pos,j,c);R=F@restframe[n].transposed();M=(R@r.data.bones[n].matrix_local.to_3x3()).to_4x4();M.translation=pt+R@offset[n];row[n]=M
  samples.append(row)
 if f%20==0:print('CLOTH_SIM_FRAME',f,'of',sc.frame_end,flush=True)
r.animation_data.action=None;bpy.data.actions.remove(timeline)
# Extend the final body pose over the settling cloth tail.
r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(nf);held={n:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for n,pb in r.pose.bones.items()}
for f,row in enumerate(samples):
 sc.frame_set(min(f,nf));r.animation_data.action=None
 if f>nf:
  for n,(q,l,s)in held.items():pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
 bpy.context.view_layer.update()
 for n,M in row.items():r.pose.bones[n].matrix=M;bpy.context.view_layer.update()
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 for n,pb in r.pose.bones.items():
  if n in names or f>nf:pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=len(samples)-1
r.animation_data.action=act;sc.frame_set(len(samples)-1);held={n:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for n,pb in r.pose.bones.items()};dead=bpy.data.actions['Dead'];r.animation_data.action=dead;r.animation_data.action_slot=dead.slots[0]
for f in range(31):
 for n,(q,l,s)in held.items():pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
for a in [act,dead]:
 for fc in curves(a):
  for k in fc.keyframe_points:k.interpolation='LINEAR'
for o in [ob,floor,*colliders]:bpy.data.objects.remove(o,do_unlink=True)
(P/'review/death_cloth_sim.json').write_text(json.dumps({'solver':'Blender cloth baked to 36 control bones','fps':30,'pre_roll_frames':pre,'settle_frames':settle,'samples':len(samples),'proxy_vertices':len(rest),'collision_gap_m':.005},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
