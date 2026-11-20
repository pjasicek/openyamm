import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import equipped_reduction as eq
props={n:json.loads((P/f'review/far_props/{n}.json').read_text())for n in ['ForearmBlade','LeafShield']}
for ratio,folder in [(.1,'reduction_props'),(.075,'reduction_fit'),(.06,'reduction_fit')]:
 row=eq.choose('Body',3,ratio,folder);base=P/row['blend']
 for offset in [0,.003,.006,.009]:
  bpy.ops.wm.open_mainfile(filepath=str(base));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  if offset:
   with bpy.data.libraries.load(str(P/'work/accepted_master.blend'))as(src,dst):dst.meshes=['Body']
   high=dst.meshes[0];high.calc_loop_triangles();co=np.array([tuple(v.co)for v in high.vertices]);pp=np.array([a.value for a in high.attributes['piece'].data]);tri=np.array([t.vertices[:]for t in high.loop_triangles]);trees={int(p):BVHTree.FromPolygons([Vector(v)for v in co],tri[pp[tri[:,0]]==p].tolist(),all_triangles=True)for p in [0,1,3,5]};part=[a.value for a in body.data.attributes['piece'].data];names=[g.name for g in body.vertex_groups]
   for v in body.data.vertices:
    k=part[v.index]
    if k not in trees or(k==1 and v.co.z>.6)or any(g.weight>.25 and('Hand'in names[g.group]or'Finger'in names[g.group])for g in v.groups):continue
    hit,n,j,d=trees[k].find_nearest(v.co);move=n*offset
    if v.co.z<.05:move.z=0
    v.co+=move;v.co.z=max(v.co.z,0)
   body.data.update();bpy.data.meshes.remove(high)
  path=P/f'work/far_body_{ratio}_{offset}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));current=dict(row,blend=str(path.relative_to(P)),surface_offset_m=offset,rebake_after_fit_pending=bool(offset));rows={'Body':current,**props};eq.trial(3,f'fit_{ratio}_{offset}',rows)
