import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/grip_final_preview.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];K=r.pose.bones['Knife'].matrix.copy();A=(K.to_3x3()@Vector((0,0,1))).normalized();C=K.translation;names=['B_R_Finger11','B_R_Finger12'];original={n:r.pose.bones[n].matrix_basis.copy()for n in names};gn={g.index:g.name for g in b.vertex_groups};ids=[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if gn[g.group].startswith('B_R_Finger1'))>.5];tip=Vector(json.loads((P/'work/finger_joints.json').read_text())['R']['B_R_Finger12_tip']);mat=common.material('grey',(.6,.6,.6,1)) if hasattr(common,'material')else None
common.workbench_clay(bpy.context.scene);H=r.pose.bones['B_R_Hand'].head;rows=[]
for j,first in enumerate([-30,0,30]):
 for k,last in enumerate([-90,-45,0,45,90]):
  for n,M in original.items():r.pose.bones[n].matrix_basis=M
  bpy.context.view_layer.update()
  for n,angle in zip(names,[first,last]):
   pb=r.pose.bones[n];M=pb.matrix.copy();h=M.translation.copy();pb.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(angle),4,A)@Matrix.Translation(-h)@M;bpy.context.view_layer.update()
  ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();V=pos[ids]-np.array(C);rad=np.linalg.norm(V-(V@np.array(A))[:,None]*np.array(A),axis=1);t=r.pose.bones['B_R_Finger12'].matrix@r.data.bones['B_R_Finger12'].matrix_local.inverted()@tip;v=t-C;row={'first':first,'last':last,'minimum_radius_mm':float(rad.min()*1000),'tip_radius_mm':float((v-A*v.dot(A)).length*1000),'q':{n:list(r.pose.bones[n].rotation_quaternion)for n in names}};rows.append(row);print('INDEX',row,flush=True);common.render_views(str(P/f'review/index_{j}{k}'),H.z-.025,.28,views=('three_quarter',),resolution=(360,360),target=(H.x,H.y))
(P/'review/index_angles.json').write_text(json.dumps(rows,indent=2))
