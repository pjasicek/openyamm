import bpy,sys,numpy as np,subprocess
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from rebake_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/far_pixels.blend'));r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);me=ob.data;ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();xyz=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in ob.vertex_groups];locked=np.zeros((len(xyz),3),bool);bow=r.data.bones['Bow'].matrix_local.inverted();grip=r.pose.bones['Bow'].head
for v in me.vertices:
 hand=sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group]);foot=sum(g.weight for g in v.groups if 'Foot'in names[g.group]or'Toe'in names[g.group])
 if pv[v.index]>=202 or (pv[v.index]==200 and v.co.z<1.52):locked[v.index]=True
 if hand>.3 and pv[v.index]==3 and (Vector(xyz[v.index])-grip).length<.06:locked[v.index]=True
 if foot>.3:
  locked[v.index,2]=True
  if v.co.z<.006:locked[v.index]=True
 if pv[v.index]==201 and not(.13<abs((bow@v.co).z)<.53):locked[v.index]=True

me.calc_loop_triangles();faces=np.array([tuple(f.vertices)for f in me.loop_triangles]);path=P/'work/rebake/round4_far_pixels2.npz';original=np.load(P/'work/rebake/round4_contour3.npz')['vertices'];_,groups=np.unique(np.c_[pv,np.round(original,7)],axis=0,return_inverse=True);np.savez(path,groups=groups,vertices=xyz,faces=faces,part='actor',level=3,camera='review/round4/camera.json',reference='r4_reference',locked=locked)
subprocess.run(['/usr/bin/python3',str(P/'scripts/pixel_silhouette_fit.py'),str(path)],check=True);out=np.load(path.with_suffix('.npy'));matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted()for g in ob.vertex_groups if g.name in r.pose.bones}
for v in me.vertices:
 matrix=Matrix([[0]*4 for _ in range(4)])
 for g in v.groups:
  if g.group in matrices:matrix+=matrices[g.group]*g.weight
 v.co=matrix.inverted()@Vector(out[v.index])
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();path=P/'work/round4/far_pixels2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,'round4_far_pixels2',3,parts=('actor',),palette=('round4_shared','lzd_a'),samples=32,camera_path=P/'review/round4/camera.json')
