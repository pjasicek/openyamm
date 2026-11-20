"""Seat the reduced finger surfaces on the real shaft and retain flat distant soles."""
import bpy,json,sys,numpy as np,fnmatch
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from timing import phase
rows=json.loads((P/'review/round2/reduction/lod_selection.json').read_text());report=[]
for row in rows:
 bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names={g.index:g.name for g in body.vertex_groups};mesh=body.data
 def pose(clip,t):
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f-int(f)));bpy.context.view_layer.update()
 def coords():
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:]for v in m.vertices]);ev.to_mesh_clear();return co
 def move(index,target):
  v=mesh.vertices[index];original=v.co.copy();same=[q.index for q in mesh.vertices if (q.co-original).length<1e-6]
  for i in same:
   v=mesh.vertices[i];pairs=[(rig.pose.bones[names[g.group]].matrix@rig.data.bones[names[g.group]].matrix_local.inverted(),g.weight)for g in v.groups if names[g.group]in rig.pose.bones];m=sum((np.array(a)*w for a,w in pairs))/sum(w for a,w in pairs);v.co=np.linalg.solve(m,np.r_[target,1])[:3]
  mesh.update();bpy.context.view_layer.update()
 def weight(v,pattern):return sum(g.weight for g in v.groups if fnmatch.fnmatchcase(names[g.group],pattern))
 for side,clip,t,center in [('R','Standing',0,0),('L','Attack',phase('Attack',.8),.29)]:
  pose(clip,t);co=coords();staff=np.array([weight(v,'Staff')>.5 for v in mesh.vertices]);matrix=np.array(rig.pose.bones['Staff'].matrix);local=(np.c_[co,np.ones(len(co))]@np.linalg.inv(matrix).T)[:,:3];region=staff&(abs(local[:,2]-center)<.085);faces=[tuple(f.vertices)for f in mesh.polygons if all(region[i]for i in f.vertices)];assert faces,(row['level'],side);tree=BVHTree.FromPolygons(co.tolist(),faces)
  mesh.calc_loop_triangles();hand_weight=np.array([weight(v,f'B_{side}_Hand')+weight(v,f'B_{side}_Finger*')for v in mesh.vertices]);triangles=np.array([tuple(f.vertices)for f in mesh.loop_triangles if all(hand_weight[i]>.3 for i in f.vertices)]);bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3])
  for repeat in range(3):
   for part in ['Hand',*[f'Finger{i}*'for i in range(5)]]:
    co=coords();part_weight=np.array([weight(v,f'B_{side}_{part}')for v in mesh.vertices]);samples=np.einsum('sk,tkj->tsj',bary,co[triangles]);valid=np.einsum('sk,tk->ts',bary,part_weight[triangles])>.3;indices=np.argwhere(valid);assert len(indices),(row['level'],side,part)
    nearest=[(*tree.find_nearest(Vector(samples[ti,bi])),ti,bi)for ti,bi in indices];hit,normal,face,distance,ti,bi=min(nearest,key=lambda q:q[3]);entry={'lod':row['level'],'side':side,'part':part,'iteration':repeat,'before_gap_m':float(distance),'triangle':triangles[ti].tolist(),'barycentric':bary[bi].tolist()}
    if distance>.002:
     target=np.array(hit+normal*.0015);delta=target-samples[ti,bi];assert np.linalg.norm(delta)<.02,(entry,delta)
     for index,w in zip(triangles[ti],bary[bi]):
      if w:move(int(index),co[index]+delta*w/(bary[bi]@bary[bi]))
     entry['movement_m']=float(np.linalg.norm(delta))
    report.append(entry)
 if row['level']==3:
  pose('Standing',0)
  for side in 'LR':
   co=coords();ids=[v.index for v in mesh.vertices if weight(v,f'B_{side}_Foot')+weight(v,f'B_{side}_Toe*')>.5];low=min(co[i,2]for i in ids);bottom=[i for i in ids if co[i,2]<low+.025];assert len(np.unique(co[bottom,:2].round(5),axis=0))>=3
   for i in bottom:
    target=co[i].copy();target[2]=low;move(i,target)
   report.append({'lod':3,'sole':side,'flattened_vertices':len(bottom),'height_m':float(low)})
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 mesh.normals_split_custom_set([(0,0,0)]*len(mesh.loops));bpy.ops.wm.save_as_mainfile(filepath=str(P/row['blend']))
(P/'review/round2/reduction/contact_fit.json').write_text(json.dumps(report,indent=2));print('LOD CONTACT FIT',report,flush=True)
