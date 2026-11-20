"""Fit the neckline's skin to its garment edge and keep the walking arms outside the dress."""
import bpy,bmesh,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,kdtree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];m=o.data;sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
pv=np.array([v.value for v in m.attributes['piece'].data])
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table()
edgeverts={v.index for e in bm.edges if e.is_boundary for v in e.verts if pv[v.index]==0 and 1.23<v.co.z<1.40 and abs(v.co.x)<.12}
tree=kdtree.KDTree(len(edgeverts))
for i,v in enumerate(sorted(edgeverts)):tree.insert(m.vertices[v].co,v)
tree.balance();bm.free();changed=0
weights={v.index:{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-6} for v in m.vertices}
for v in m.vertices:
 if pv[v.index]!=1 or v.co.z>1.43:continue
 _,idx,d=tree.find(v.co)
 blend=max(0,min(1,(.05-d)/.027));blend=blend*blend*(3-2*blend)
 if not blend:continue
 w={n:a*(1-blend) for n,a in weights[v.index].items()}
 for n,a in weights[idx].items():w[n]=w.get(n,0)+a*blend
 keep=sorted(w.items(),key=lambda a:-a[1])[:4];total=sum(a for _,a in keep)
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for n,a in keep:o.vertex_groups[n].add([v.index],a/total,'REPLACE')
 changed+=1
print('NECKLINE fitted skin weights',changed)
a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
poses=[]
for f in np.arange(0,a.frame_range[1]+.01,.25):
 sc.frame_set(int(f),subframe=float(f%1))
 poses.append((float(f),{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
solved=[]
for f,pose in poses:
 r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis=pose[b.name]
 bpy.context.view_layer.update();result={}
 for s,sign in [('L',-1),('R',1)]:
  b=r.pose.bones[f'B_{s}_UpperArm']
  axis=(r.pose.bones['B_Pelvis'].matrix@r.data.bones['B_Pelvis'].matrix_local.inverted()).to_3x3()@Vector((0,1,0))
  M=b.matrix.copy();M=Quaternion(axis,math.radians(9)*sign).to_matrix().to_4x4()@M
  M.translation=b.head
  basis=b.parent.matrix@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local
  result[b.name]=(basis.inverted()@M).to_quaternion()
 solved.append((f,result))
r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
for f,pose in solved:
 for n,Q in pose.items():
  if n in prev and Q.dot(prev[n])<0:Q.negate()
  prev[n]=Q.copy();b=r.pose.bones[n];b.rotation_quaternion=Q;b.keyframe_insert('rotation_quaternion',frame=f)
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
print('WALK arms abducted 9 degrees')
