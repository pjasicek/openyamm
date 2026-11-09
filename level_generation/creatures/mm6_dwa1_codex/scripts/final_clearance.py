import bpy,bmesh,shutil,json,math,numpy as np,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];backup=P/'work/before_final_clearance.blend'
if not backup.exists():shutil.copy2(P/'work/textured_master.blend',backup)
bpy.ops.wm.open_mainfile(filepath=str(backup));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece'];sel=[v for v in bm.verts if v[pl]==5];ids=set(sel);geom=sel+[e for e in bm.edges if all(v in ids for v in e.verts)]+[f for f in bm.faces if all(v in ids for v in f.verts)];before=len(bm.faces);bmesh.ops.bisect_plane(bm,geom=geom,plane_co=(0,0,.49),plane_no=(0,0,1),clear_outer=True,clear_inner=False,dist=1e-6);bm.to_mesh(me);bm.free();print('HIDDEN PANTS',before,len(me.polygons))
# Full thigh ownership at the short tunic hem keeps it over the visible trouser cuffs.
pv=np.array([a.value for a in me.attributes['piece'].data]);names={g.index:g.name for g in body.vertex_groups};groups={g.name:g for g in body.vertex_groups}
def put(i,w):
 for e in me.vertices[i].groups[:]:body.vertex_groups[e.group].remove([i])
 w={n:x for n,x in w.items()if x>1e-7};total=sum(w.values())
 for n,x in w.items():groups[n].add([i],x/total,'REPLACE')
for v in me.vertices:
 if pv[v.index]!=2:continue
 w={names[e.group]:e.weight for e in v.groups};l=w.get('B_L_Thigh',0)/.8;r=w.get('B_R_Thigh',0)/.8;t=min(l+r,1);k=t/max(l+r,1e-9);put(v.index,{'B_Pelvis':1-t,'B_L_Thigh':l*k,'B_R_Thigh':r*k})
kd=KDTree(int((pv==2).sum()))
for i in np.where(pv==2)[0]:kd.insert(me.vertices[int(i)].co,int(i))
kd.balance();owners=json.loads((P/'work/stud_owners.json').read_text())
for p in [int(k)for k,v in owners.items()if v==2]:
 ids=np.where(pv==p)[0];w={}
 for i in ids:
  _,j,_=kd.find(me.vertices[int(i)].co)
  for e in me.vertices[j].groups:w[names[e.group]]=w.get(names[e.group],0)+e.weight
 for i in ids:put(int(i),w)
# One additional degree on the weapon arm clears the measured 2.23 mm cloth contact.
for a in [a for a in bpy.data.actions if a.name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];out=[]
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f);axis=rig.pose.bones['B_Spine2'].matrix.to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,1,0));pb=rig.pose.bones['B_R_UpperArm'];M=pb.matrix.copy();c=M.translation.copy();M=Matrix.Rotation(math.radians(1),4,axis)@M;M.translation=c;pb.matrix=M;bpy.context.view_layer.update();out.append(pb.rotation_quaternion.copy())
 for f,q in enumerate(out):
  if f and q.dot(out[f-1])<0:q=-q;out[f]=q
  rig.pose.bones['B_R_UpperArm'].rotation_quaternion=q;rig.pose.bones['B_R_UpperArm'].keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
