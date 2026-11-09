import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];hand=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])for v in me.vertices])>.25;faces=[tuple(f.vertices)for f in me.polygons if all(pv[v]<201 and not hand[v]for v in f.vertices)];inv=rig.data.bones['Bow'].matrix_local.inverted();bow=[inv@v.co for v in me.vertices if pv[v.index]==201 and abs((inv@v.co).z)>.11];rows=[]
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rel=rig.data.bones['B_L_Hand'].matrix_local.inverted()@rig.data.bones['Bow'].matrix_local
for f in range(34):
 scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();tree=BVHTree.FromPolygons([tuple(v.co)for v in m.vertices],faces);ev.to_mesh_clear();base=rig.pose.bones['B_L_Hand'].matrix@rel;handnock=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.55);draw=float(np.clip((f-14)/2,0,1))if f<23 else 0;angles={}
 for angle in range(-180,181,15):
  M=base@Matrix.Rotation(math.radians(angle),4,'Z');mid=M@Vector((0,.215,.04));nock=mid.lerp(handnock,draw);tips=[M@Vector((0,.215,z))for z in [-.55,.55]];pts=[M@v for v in bow]+[tip.lerp(nock,t)for tip in tips for t in np.linspace(0,1,31)];dep=0
  for q in pts:
   loc,normal,idx,d=tree.find_nearest(q,.06)
   if loc is not None and (q-loc).dot(normal)<-.7*d:dep=max(dep,d)
  angles[angle]=dep
 valid=[a for a,d in angles.items()if d<.001];rows.append({'frame':f,'valid':valid,'depths':angles});print('ATTACKROLL',f,valid)
(P/'review/attack_roll_sweep.json').write_text(json.dumps(rows,indent=2))
