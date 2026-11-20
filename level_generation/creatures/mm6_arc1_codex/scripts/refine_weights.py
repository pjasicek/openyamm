import bpy,numpy as np,math,sys,os,runpy
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_clips.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
names={g.index:g.name for g in body.vertex_groups};gs={g.name:g for g in body.vertex_groups};co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data])
def put(i,w):
 for g in me.vertices[i].groups[:]:body.vertex_groups[g.group].remove([i])
 w={n:float(v)for n,v in w.items()if v>1e-6};total=sum(w.values());assert total>0
 for n,v in w.items():gs[n].add([i],v/total,'REPLACE')
# Neck follows neck/head, never the humerus. Remove the hard chest cutoff left by the first transfer.
for v in me.vertices:
 x,y,z=co[v.index]
 if pv[v.index]!=0 or z<1.13:continue
 w={names[g.group]:g.weight for g in v.groups}
 if z<1.34 or abs(x)>.12:
  a=w.pop('B_Head',0)+w.pop('B_Neck',0);w['B_Spine2']=w.get('B_Spine2',0)+a
 elif abs(x)<.105:
  t=float(np.clip((z-1.34)/.105,0,1));w={'B_Spine2':1-t,'B_Head':t}
 put(v.index,w)
adj={v.index:[]for v in me.vertices if pv[v.index]==0}
for e in me.edges:
 a,b=e.vertices
 if a in adj and b in adj:adj[a].append(b);adj[b].append(a)
for _ in range(18):
 old={i:{names[g.group]:g.weight for g in me.vertices[i].groups}for i in adj}
 for i,nb in adj.items():
  if not nb or not 1.13<co[i,2]<1.445:continue
  w={n:.45*v for n,v in old[i].items()}
  for j in nb:
   for n,v in old[j].items():w[n]=w.get(n,0)+.55*v/len(nb)
  put(i,w)
for v in me.vertices:put(v.index,dict(sorted([(names[g.group],g.weight)for g in v.groups],key=lambda x:-x[1])[:4]))
# Quiver reach clears the bob: abduct the right shoulder during the reach, retaining its wrist pose.
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene=bpy.context.scene
for f in range(4,20):
 scene.frame_set(f);pb=rig.pose.bones['B_R_UpperArm'];m=pb.matrix.copy();t=m.translation.copy();angle=-math.radians(16)*math.sin(math.pi*(f-4)/16)**2;m=Matrix.Rotation(angle,4,'Y')@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update();pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_refined.blend'))
sys.argv=['twist_bones.py','--','work/rig_refined.blend','work/rig_twist.blend'];runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
