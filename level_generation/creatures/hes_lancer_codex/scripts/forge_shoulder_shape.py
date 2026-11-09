"""Fit the three shoulder lames around the upper arm, leaving the underside open."""
import bpy,bmesh,os,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_collision_fit.blend'))
r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
for side in 'LR':
 a=r.data.bones[f'B_{side}_UpperArm'].head_local;z=r.data.bones[f'B_{side}_Forearm'].head_local;axis=(z-a).normalized();up=Vector((0,0,1));up=(up-axis*up.dot(axis)).normalized();across=axis.cross(up)
 for name in (f'Arm_pauldron_{side}',f'Arm_pauldron_lower_{side}',f'Apron_Shoulder_{side}'):
  o=bpy.data.objects[name]
  for v in o.data.vertices:
   d=v.co-a;t=d.dot(axis);rad=d-axis*t;angle=math.atan2(rad.dot(across),rad.dot(up))*.72
   v.co=a+axis*(t+.025)+(up*math.cos(angle)+across*math.sin(angle))*rad.length
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for side in 'LR':
 b=r.data.edit_bones[f'B_ForgeShoulder_{side}'];p=r.data.edit_bones[f'B_{side}_UpperArm'];b.parent=p;b.matrix=p.matrix.copy();b.length=.08
bpy.ops.object.mode_set(mode='OBJECT')
for a in bpy.data.actions:
 if not a.name.startswith('Forge_'):continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if 'B_ForgeShoulder_' in fc.data_path:bag.fcurves.remove(fc)
 for f in (float(a.frame_range[0]),float(a.frame_range[1])):
  for side in 'LR':
   b=r.pose.bones[f'B_ForgeShoulder_{side}'];b.matrix_basis.identity();b.rotation_mode='QUATERNION'
   for path in ('location','rotation_quaternion','scale'):b.keyframe_insert(path,frame=f)
o=bpy.data.objects['Apron_Back2'];bm=bmesh.new();bm.from_mesh(o.data);seen=set();remove=[]
for v in bm.verts:
 if v in seen:continue
 component={v};queue=[v];seen.add(v)
 while queue:
  w=queue.pop()
  for e in w.link_edges:
   q=e.other_vert(w)
   if q not in seen:seen.add(q);component.add(q);queue.append(q)
 if max(abs(q.co.x) for q in component)<.075 and max(q.co.z for q in component)<.72:remove.extend(component)
assert remove,'Expected two bridge components'
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
r.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_direction_fit.blend'));(P/'review/forge_direction_fit.json').write_text('{}\n');sys.stdout.flush();os._exit(0)
