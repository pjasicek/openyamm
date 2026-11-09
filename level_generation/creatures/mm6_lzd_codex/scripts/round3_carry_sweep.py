"""Measure candidate carry frames against the complete bracer, forearm, leg and bowstring surfaces."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
# Reuse the revision's detached FK/IK and anatomical-frame operations.
code=(P/'scripts/round3_motion.py').read_text();exec(code[:code.index('baseline={')])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
g=rig.data.bones['B_L_Hand'].matrix_local.inverted()@rig.data.bones['Bow'].matrix_local;me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];hands=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])for v in me.vertices])>.25
faces=[list(f.vertices)for f in me.polygons if all(pv[i]<201 and not hands[i]for i in f.vertices)]
local=np.array([tuple(rig.data.bones['Bow'].matrix_local.inverted()@v.co)for v in me.vertices]);bowids=np.where((pv==201)&(abs(local[:,2])>.11))[0]
base=[]
for role in ['Standing','Fidget','Walking','Running','Hit']:
 a=bpy.data.actions[role]
 for f in np.linspace(0,a.frame_range[1],5):base.append((role,float(f),sample(a,float(f))))
def score():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,faces);bm=rig.pose.bones['Bow'].matrix;pts=[co[i]for i in bowids]+[bm@Vector((0,.215,float(z)))for z in np.linspace(-.55,.55,45)];worst=0
 for v in pts:
  hit,n,_,d=tree.find_nearest(v,.05)
  if hit is not None and (v-hit).dot(n)<-.7*d:worst=max(worst,d)
 return worst
best=None;trials=[]
for yaw in [-30,-25,-20,-15,0,15,30]:
 for pole_y in [-1,0,1,2]:
  for hand_y in [-.28,-.22,-.16]:
   R=Matrix.Rotation(math.radians(yaw),3,'Z')@Matrix.Rotation(math.radians(20),3,'X');HR=R@g.to_3x3().inverted();worst=0
   for role,f,p in base:
    put(p);shoulder=rig.pose.bones['B_L_UpperArm'].head;ik(['B_L_UpperArm','B_L_Forearm','B_L_Hand'],Vector((.45,hand_y,shoulder.z-.32)),Vector((1,pole_y,0)));rot('B_L_Hand',HR);rig.pose.bones['Bow'].rotation_quaternion=Quaternion();rig.pose.bones['Bow'].location=Vector();bpy.context.view_layer.update();anatomy('L');worst=max(worst,score())
   row={'yaw':yaw,'tilt_x':20,'pole_y':pole_y,'hand_y':hand_y,'contact_m':worst};trials.append(row)
   if best is None or worst<best['contact_m']:best=row;print('CARRY_BEST',best,flush=True)
print('CARRY_SELECTED',best,flush=True);(P/'review/round3_carry_sweep.json').write_text(json.dumps({'best':best,'trials':trials},indent=2))
