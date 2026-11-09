"""Actual bow/arrow vertices and string centerlines against body surfaces, sampled at 48 Hz."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from volume_contact import volumes,deepest
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(globals().get('GATE_BLEND',P/'work/export_reimport.blend')));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
pv=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);names=[g.name for g in body.vertex_groups];hands=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group] or'Finger'in names[g.group])for v in me.vertices])>.25
faces=[tuple(f.vertices)for f in me.polygons if all(pv[v]<201 and not hands[v]for v in f.vertices)];bowlocal=np.array([tuple(rig.data.bones['Bow'].matrix_local.inverted()@Vector(v))for v in co]);bowids=np.where((pv==201)&(abs(bowlocal[:,2])>.11))[0];arrowids=np.where(pv==202)[0];report={}
for act in bpy.data.actions:
 if act.name not in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];duration=act.frame_range[1]/30;worst={n:{'depth_m':0}for n in ['bow','arrow','string']};poses=[]
 for t in np.r_[np.arange(0,duration,1/48),duration]:
  f=t*30;scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();xyz=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();regions=volumes(xyz,faces,pv)
  samples={'bow':xyz[bowids]}
  if act.name in ('Attack','Cast')and 19<=f<23:samples['arrow']=xyz[arrowids]
  string=[]
  for n in ['StringTop','StringBottom']:
   m=rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted();string.extend([m@Vector((0,0,z))for z in np.linspace(0,1,31)])
  samples['string']=string
  for n,pts in samples.items():
   d,piece,point=deepest(regions,pts)
   if d>worst[n]['depth_m']:worst[n]={'depth_m':d,'time':float(t),'hit_piece':piece,'point':point}
  if act.name=='Attack':
   bm=rig.pose.bones['Bow'].matrix;axis=bm.to_3x3()@Vector((0,0,1));forward=bm.to_3x3()@Vector((0,-1,0));poses.append({'t':float(t),'bow_vertical_dot':axis.normalized().z,'aim_dot':forward.normalized().dot(Vector((0,-1,0)))})
 report[act.name]={'contacts':worst,'bow_orientation':poses};print('EQUIPMENT',act.name,worst)
(P/'review/equipment_gate.json').write_text(json.dumps(report,indent=2))
