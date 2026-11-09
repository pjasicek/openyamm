"""Fit the retained equipment to the new library motions without changing the source arm trajectory."""
from pathlib import Path
import bpy,sys,math,json,runpy,ast,numpy as np
from mathutils import Vector,Matrix,Quaternion
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from sword import add_sword
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v11.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
# Retain the original leg-following rear panel; add clearance at its lower free edge.
with bpy.data.libraries.load(str(p/'work/rig_v7.blend'),link=False) as (src,dst):dst.objects=['Body']
old=dst.objects[0];vs=[v for v in old.data.vertices if old.data.attributes['piece'].data[v.index].value==14];kd=KDTree(len(vs))
for i,v in enumerate(vs):kd.insert(v.co,i)
kd.balance()
for v in body.data.vertices:
 if body.data.attributes['piece'].data[v.index].value!=14:continue
 _,i,d=kd.find(v.co);assert d<1e-5,d
 for g in body.vertex_groups:g.remove([v.index])
 for e in vs[i].groups:body.vertex_groups[old.vertex_groups[e.group].name].add([v.index],e.weight,'REPLACE')
 v.co.y+=.02*min(max((1.055-v.co.z)/.2,0),1)
bpy.data.objects.remove(old,do_unlink=True);body.data.update()
so=add_sword(rig);hand=rig.pose.bones['B_R_Hand'];act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
poses=[]
for f in range(int(act.frame_range[1])+1):
 sc.frame_set(f);poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
rig.animation_data.action=None
names={g.index:g.name for g in body.vertex_groups}
grip={v.index for v in body.data.vertices if any(e.weight>.3 and (names[e.group].startswith('B_R_Hand') or names[e.group].startswith('B_R_Finger')) for e in v.groups)}
faces=[tuple(f.vertices) for f in body.data.polygons if not any(i in grip for i in f.vertices)]
def apply(pose,deg):
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update();h=hand.head.copy();axis=(h-rig.pose.bones['B_R_Forearm'].head).normalized();hand.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(deg),4,axis)@Matrix.Translation(-h)@hand.matrix
 bpy.context.view_layer.update()
def depth():
 deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,faces)
 ev=so.evaluated_get(deps);m=ev.to_mesh();worst=0
 for v in list(m.vertices)[::2]:
  loc,n,fi,d=tree.find_nearest(v.co,.2)
  if loc is not None and d>1e-6 and (v.co-loc).dot(n)<-.707*d:worst=max(worst,d)
 ev.to_mesh_clear();return worst
probes=[]
for deg in sorted(range(-90,91,10),key=abs):
 worst=0
 for pose in poses:
  apply(pose,deg);worst=max(worst,depth())
 row=(deg,worst);probes.append(row);print('WEAPON_GRIP_PROBE',row,flush=True)
 if worst<.002:break
best=min(probes,key=lambda r:(r[1]>.002,abs(r[0]) if r[1]<.002 else r[1]));assert best[1]<.002,probes
out=[]
for pose in poses:apply(pose,best[0]);out.append(hand.rotation_quaternion.copy())
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f,q in enumerate(out):hand.rotation_quaternion=q;hand.keyframe_insert('rotation_quaternion',frame=f)
FA=.5;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist','exec'),globals());bake_twist(act)
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(int(act.frame_range[1]));held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones};bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;rig.animation_data.action=a
for f in [0,30]:
 for n,(q,l) in held.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.data.objects.remove(so,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v12.blend'));(p/'revision_02/motion/weapon_fit.json').write_text(json.dumps({'constant_death_wrist_roll_deg':best[0],'max_blade_depth_m':best[1],'probes':probes},indent=2)+'\n')
for s in ['g6_skirt_poke.py','g6_head_clearance.py']:
 sys.argv=[s,'--',str(p/'work/rig_v12.blend'),'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'];runpy.run_path(str(p/'scripts'/s),run_name='__main__')
