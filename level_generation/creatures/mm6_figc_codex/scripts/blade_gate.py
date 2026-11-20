"""Measure the real axe vertices, cutting plane and target-facing impact from the exported GLB."""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_figc_lod0.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');obj=next(o for o in bpy.data.objects if o.type=='MESH');eq=json.loads((P/'work/equipment.json').read_text());act=next(a for a in bpy.data.actions if a.name=='Attack');rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
# Convert the source Blender rest basis through the exported axe's local bind frame.
source=np.array(eq['axe_axis']);edge=np.array(eq['axe_edge']);gi=obj.vertex_groups['Axe'].index
ids=[v.index for v in obj.data.vertices if any(g.group==gi and g.weight>.99 for g in v.groups)]
rest=np.array([tuple(obj.matrix_world@obj.data.vertices[i].co) for i in ids]);grip=rig.matrix_world@rig.data.bones['Axe'].head_local
# glTF import already restores Blender Z-up. Runtime forward is Blender -Y.
dist=np.linalg.norm(rest-np.array(grip),axis=1);blade=dist>.24;assert blade.sum()>10
rows=[];prev=None;dt=1/240
for t in np.arange(0,1.5+dt/2,dt):
 frame=t*30;bpy.context.scene.frame_set(int(frame),subframe=float(frame%1));ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(obj.matrix_world@mesh.vertices[i].co) for i in ids]);ev.to_mesh_clear()
 deform=(rig.matrix_world@rig.pose.bones['Axe'].matrix)@rig.data.bones['Axe'].matrix_local.inverted()@rig.matrix_world.inverted()
 ax=(deform.to_3x3()@Vector(source)).normalized();ed=(deform.to_3x3()@Vector(edge)).normalized();normal=ax.cross(ed).normalized()
 if prev is not None:
  vel=(co-prev)/dt;speeds=np.linalg.norm(vel[blade],axis=1);k=np.where(blade)[0][int(np.argmax(speeds))];v=Vector(vel[k]);across=v-ax*v.dot(ax);share=abs(across.dot(ed))/max(across.length,1e-9)
  rows.append({'time':float(t-dt/2),'tip_speed_m_s':float(np.linalg.norm(vel[k])),'forward':float(-ax.y),'edge_share':float(share),'vertex':int(ids[k])})
 prev=co
candidates=[r for r in rows if r['forward']>.5];assert candidates
impact=max(candidates,key=lambda r:r['tip_speed_m_s']);impact['pass']=impact['edge_share']>.85;impact['samples_hz']=240
(P/'work/blade_gate.json').write_text(json.dumps(impact,indent=2));print('BLADE_GATE',impact);assert impact['pass']
