import bpy,bmesh,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/skirt_v1.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;scene=bpy.context.scene
pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices]);gn={g.index:g.name for g in o.vertex_groups};faces=[tuple(f.vertices)for f in me.polygons]
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();part=bm.verts.layers.int['piece'];targets={};pairs=[]
for pid in [8,9]:
 ring={v for e in bm.edges if e.is_boundary and all(v[part]==pid for v in e.verts) for v in e.verts}
 assert len(ring)==20,(pid,len(ring))
 for v in ring:
  neighbours=[e.other_vert(v)for e in v.link_edges if e.other_vert(v)not in ring];assert len(neighbours)==1
  old=neighbours[0];w={gn[g.group]:g.weight for g in me.vertices[v.index].groups};targets[old.index]=w;pairs.append([old.index,v.index])
bm.free()
def put(i,w):
 v=me.vertices[i]
 for e in v.groups[:]:o.vertex_groups[e.group].remove([i])
 total=sum(w.values());assert total>0
 for n,x in w.items():
  if x>1e-8:o.vertex_groups[n].add([i],x/total,'REPLACE')
kd=KDTree(len(targets))
for i in targets:kd.insert(me.vertices[i].co,i)
kd.balance();original=[{gn[e.group]:e.weight for e in v.groups}for v in me.vertices]
for v in me.vertices:
 if pv[v.index]not in[8,9]or v.index in [n for _,n in pairs]:continue
 _,i,d=kd.find(v.co);t=max(0,1-d/.17);t=t*t*(3-2*t)
 w={n:x*(1-t)for n,x in original[v.index].items()}
 for n,x in targets[i].items():w[n]=w.get(n,0)+x*t
 put(v.index,w)
for a,b in pairs:put(a,targets[a]);put(b,targets[a])
print('SEAM weights',len(pairs),flush=True)

def curves(a):return [fc for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
def signs():
 flips=0
 for a in bpy.data.actions:
  groups={}
  for fc in curves(a):
   for k in fc.keyframe_points:k.interpolation='LINEAR'
   if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
  for cs in groups.values():
   if len(cs)!=4:continue
   prev=None
   for j in range(min(len(cs[i].keyframe_points)for i in range(4))):
    q=np.array([cs[i].keyframe_points[j].co.y for i in range(4)])
    if prev is not None and q@prev<0:
     q=-q;flips+=1
     for i in range(4):cs[i].keyframe_points[j].co.y=q[i]
    prev=q
  for fc in curves(a):fc.update()
 print('SIGN corrections',flips,flush=True)
signs()
def action(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def coeval():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();return c
# Small measured surface corrections rotate the entire arm at the shoulder, preserving elbow flex and hinge roll.
corrections={}
for role in ['Attack','Hit','Death']:
 a=bpy.data.actions[role];action(a);maxangle=0
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1))
  for sd in 'LR':
   sleeve=9 if sd=='L'else 8;hand=3 if sd=='L'else 4;un=f'B_{sd}_UpperArm';other=[fc for fc in faces if pv[fc[0]]not in[sleeve,hand]]
   for it in range(8):
    co=coeval();tree=BVHTree.FromPolygons(co,other);el=r.pose.bones[f'B_{sd}_Forearm'].head;wr=r.pose.bones[f'B_{sd}_Hand'].head;worst=None
    for i in np.where(np.isin(pv,[sleeve,hand]))[0]:
     if pv[i]==sleeve and (co[i]-el).dot(wr-el)<0:continue
     loc,n,fi,d=tree.find_nearest(co[i],.08)
     if loc is not None and (co[i]-loc).dot(n)<-.7*d and d>.0005 and (worst is None or d>worst[0]):worst=(d,n,co[i])
    if worst is None:break
    d,n,p=worst;M=r.pose.bones[un].matrix.copy();h=M.translation.copy();u=p-h;v=p+n*(d+.003)-h;q=u.normalized().rotation_difference(v.normalized());maxangle=max(maxangle,math.degrees(q.angle));M=q.to_matrix().to_4x4()@M;M.translation=h;r.pose.bones[un].matrix=M;bpy.context.view_layer.update()
   r.pose.bones[un].keyframe_insert('rotation_quaternion',frame=float(f))
 corrections[role]=maxangle;print('CONTACT correction',role,maxangle,flush=True)
signs()
# Dense floor correction avoids interpolating through the ground between the cloth's integer keys.
a=bpy.data.actions['Death'];action(a);values=[]
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 scene.frame_set(int(f),subframe=float(f%1));low=min(v.z for v in coeval());M=r.pose.bones['B_Pelvis'].matrix.copy();M.translation.z+=.004-low;values.append((float(f),M))
for f,M in values:
 scene.frame_set(int(f),subframe=f%1);r.pose.bones['B_Pelvis'].matrix=M;r.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
scene.frame_set(int(a.frame_range[1]),subframe=float(a.frame_range[1]%1));held={b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;r.animation_data.action=dead
for f in [0,30]:
 for n,(q,l)in held.items():
  b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30;signs();action(bpy.data.actions['Standing']);scene.frame_set(0)
(P/'review/rig_surface_corrections.json').write_text(json.dumps({'seam_pairs':pairs,'contact_rotation_max_deg':corrections},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_corrected.blend'))
import common
common.workbench_clay(scene)
for role in ['Standing','Attack','Death','Dead']:
 a=bpy.data.actions[role];action(a)
 for j in range(5):
  f=float(a.frame_range[1])*j/4;scene.frame_set(int(f),subframe=f%1);lo,hi=common.world_bounds([o]);mid=(lo+hi)*.5;common.render_views(str(P/'review'/f'corrected_{role}_{j}'),mid.z,max(2.05,(hi-lo).length*1.5),views=('front','left','three_quarter'),resolution=(360,450),target=(mid.x,mid.y))
