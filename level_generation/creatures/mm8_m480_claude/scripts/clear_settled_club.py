"""Ease the settled bone a few degrees away from the torso during the backward fall."""
from pathlib import Path
import bpy,bmesh,json,math,ast,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];club=bpy.data.objects['Club'];me=body.data
names=[g.name for g in body.vertex_groups]
keep=[me.attributes['piece'].data[v.index].value==0 and sum(g.weight for g in v.groups if names[g.group].startswith('B_R_') and any(k in names[g.group] for k in ('Clavicle','UpperArm','Forearm','Hand','Finger')))<.2 for v in me.vertices]
bm=bmesh.new();bm.from_mesh(me);ix=bm.verts.layers.int.new('index')
for v in bm.verts:v[ix]=v.index
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not keep[v.index]],context='VERTS');bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges)
if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
faces=[tuple(v[ix] for v in f.verts) for f in bm.faces];bm.free()
def coords(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(obj.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return co
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(33,subframe=.5)
tree=BVHTree.FromPolygons(coords(body).tolist(),faces,all_triangles=True);co=coords(club);_,indices=np.unique(np.round(co,5),axis=0,return_index=True);co=co[indices]
hand=rig.pose.bones['B_R_Hand'];pivot=np.array(hand.head)
def penalty(points):
 worst=0.
 for point in points:
  v=Vector(point);loc,n,idx,d=tree.find_nearest(v)
  if (v-loc).dot(n)<-.5*d:worst=max(worst,d+.003)
  elif d<.003:worst=max(worst,.003-d)
 return worst
before=penalty(co);found=None
for deg in range(2,21,2):
 for ax in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,0),(-1,-1,0),(1,-1,0),(-1,1,0)]:
  q=Quaternion(Vector(ax).normalized(),math.radians(deg));m=np.array(q.to_matrix());after=penalty((co-pivot)@m.T+pivot)
  if after<.0001:found=(q,deg,ax,after);break
 if found:break
assert found,('No small clearance adjustment',before)
q,deg,axis,after=found;keys=[]
for f in np.arange(0,act.frame_range[1]+.01,.5):
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));h=rig.pose.bones['B_R_Hand'];m=h.matrix.copy();t=float(np.clip((f-25)/6,0,1));t=t*t*(3-2*t);correction=Quaternion(Vector(axis).normalized(),math.radians(deg)*t);nm=(correction.to_matrix()@m.to_3x3()).to_4x4();nm.translation=m.translation;h.matrix=nm;h.location=(0,0,0);keys.append((float(f),h.rotation_quaternion.copy()))
previous=None
for f,q in keys:
 if previous is not None and q.dot(previous)<0:q.negate()
 previous=q.copy();h.rotation_quaternion=q;h.keyframe_insert('rotation_quaternion',frame=f)
# The corpse uses the corrected endpoint exactly.
rig.animation_data.action=bpy.data.actions['Dead'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for f in (0,1):h.rotation_quaternion=keys[-1][1];h.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
report={'angle_degrees':deg,'world_axis':axis,'before_penalty_m':before,'after_penalty_m':after,'fade_frames':[25,31],'sample_frame':33.5}
(p/'review/settled_club_clearance.json').write_text(json.dumps(report,indent=2));print('SETTLED CLUB',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/authored.blend'))
