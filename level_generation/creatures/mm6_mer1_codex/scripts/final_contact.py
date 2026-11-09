import bpy,bmesh,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_ready.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;scene=bpy.context.scene
pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices]);gn={g.index:g.name for g in o.vertex_groups};faces=[tuple(f.vertices)for f in me.polygons]
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
forearm=np.array([sum(e.weight for e in v.groups if 'Forearm'in gn[e.group])>.5 for v in me.vertices]);corrections={}
for role in ['Standing','Walking','Running','Fidget']:
 a=bpy.data.actions[role];action(a);maxangle=0
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1))
  for sd in 'LR':
   sleeve=9 if sd=='L'else 8;hand=3 if sd=='L'else 4;un=f'B_{sd}_UpperArm';other=[fc for fc in faces if pv[fc[0]]not in[sleeve,hand]]
   for it in range(16):
    co=coeval();tree=BVHTree.FromPolygons(co,other);el=r.pose.bones[f'B_{sd}_Forearm'].head;wr=r.pose.bones[f'B_{sd}_Hand'].head;worst=None
    for i in np.where(np.isin(pv,[sleeve,hand]))[0]:
     if pv[i]==sleeve and not forearm[i]:continue
     loc,n,fi,d=tree.find_nearest(co[i],.08)
     if loc is not None and (co[i]-loc).dot(n)<-.7*d and d>.0005 and (worst is None or d>worst[0]):worst=(d,n,co[i])
    if worst is None:break
    d,n,p=worst;M=r.pose.bones[un].matrix.copy();h=M.translation.copy();u=p-h;v=p+n*(d+.003)-h;q=u.normalized().rotation_difference(v.normalized());maxangle=max(maxangle,math.degrees(q.angle));M=q.to_matrix().to_4x4()@M;M.translation=h;r.pose.bones[un].matrix=M;bpy.context.view_layer.update()
   r.pose.bones[un].keyframe_insert('rotation_quaternion',frame=float(f))
 corrections[role]=maxangle;print('CONTACT correction',role,maxangle,flush=True)
signs()
clothcor=0
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
(P/'review/rig_gated_corrections.json').write_text(json.dumps({'cloth_boot_correction_m':clothcor,'contact_rotation_max_deg':corrections},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_gated.blend'))
import common
common.workbench_clay(scene)
for role in ['Standing','Attack','Death','Dead']:
 a=bpy.data.actions[role];action(a)
 for j in range(5):
  f=float(a.frame_range[1])*j/4;scene.frame_set(int(f),subframe=f%1);lo,hi=common.world_bounds([o]);mid=(lo+hi)*.5;common.render_views(str(P/'review'/f'ready_{role}_{j}'),mid.z,max(2.05,(hi-lo).length*1.5),views=('front','left','three_quarter'),resolution=(360,450),target=(mid.x,mid.y))
