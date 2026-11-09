import bpy,shutil,numpy as np,runpy
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bk=P/'work/before_cloth_finish.blend'
if not bk.exists():shutil.copy2(P/'work/textured_master.blend',bk)
bpy.ops.wm.open_mainfile(filepath=str(bk));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=ob.data;pv=np.array([a.value for a in me.attributes['piece'].data]);rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
names={g.index:g.name for g in ob.vertex_groups};kd=KDTree(int((pv==2).sum()))
for i in np.where(pv==2)[0]:kd.insert(me.vertices[int(i)].co,int(i))
kd.balance()
for v in me.vertices:
 if pv[v.index]!=5 or v.co.z<.37:continue
 t=float(np.clip((v.co.z-.37)/.06,0,1));w={names[e.group]:e.weight*(1-t) for e in v.groups};near=kd.find_n(v.co,3)
 for _,j,d in near:
  for e in me.vertices[j].groups:w[names[e.group]]=w.get(names[e.group],0)+t*e.weight/3
 for e in v.groups[:]:ob.vertex_groups[e.group].remove([v.index])
 w=dict(sorted(w.items(),key=lambda x:-x[1])[:4]);tot=sum(w.values())
 for n,x in w.items():ob.vertex_groups[n].add([v.index],x/tot,'REPLACE')
 # The covered trouser cuff follows the outer tunic; taper the unseen overlap inward.
 cx=.115 if v.co.x>0 else -.115;v.co.x=cx+(v.co.x-cx)*(1-.22*t);v.co.y*=1-.22*t
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
