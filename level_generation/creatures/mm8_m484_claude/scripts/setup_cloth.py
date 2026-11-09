"""Give the separate mail kilt four-direction controls on its existing pelvis/thigh drape."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_reduced.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);skin=[tuple(f.vertices) for f in me.polygons if all(pv[i] in [0,1] for i in f.vertices)];tree=BVHTree.FromPolygons(co.tolist(),skin);cloth=[v for v in me.vertices if pv[v.index]==100];moves=[]
for v in cloth:
 if v.co.z>.89:continue
 loc,nrm,fi,d=tree.find_nearest(v.co,.08)
 if loc is not None:
  signed=(v.co-loc).dot(nrm)
  if signed<.014:
   move=nrm*(.014-signed);assert move.length<.055;v.co+=move;moves.append(move.length)
me.update();names=[g.name for g in b.vertex_groups];weights={v.index:[(names[g.group],g.weight) for g in v.groups if g.weight>.0001] for v in cloth};used=sorted({n for w in weights.values() for n,v in w});dirs={'F':Vector((0,-1,0)),'B':Vector((0,1,0)),'L':Vector((1,0,0)),'R':Vector((-1,0,0))}
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for n in used:
 for sd in dirs:
  eb=r.data.edit_bones.new('Skirt_'+sd+'_'+n);eb.matrix=r.data.edit_bones[n].matrix.copy();eb.length=.05;eb.parent=r.data.edit_bones[n]
bpy.ops.object.mode_set(mode='OBJECT')
for n in used:
 for sd in dirs:b.vertex_groups.new(name='Skirt_'+sd+'_'+n)
for v in cloth:
 t=min(1,max(0,(.905-v.co.z)/.10));x,y=v.co.x,v.co.y;xx=abs(x)/(abs(x)+abs(y)+1e-8);shares={'L' if x>0 else 'R':xx,'B' if y>0 else 'F':1-xx}
 for n,w in weights[v.index]:
  b.vertex_groups[n].add([v.index],w*(1-t),'REPLACE')
  for sd,share in shares.items():b.vertex_groups['Skirt_'+sd+'_'+n].add([v.index],w*t*share,'REPLACE')
for v in me.vertices:
 groups=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-6],key=lambda g:-g[1]);keep=groups[:4];total=sum(w for _,w in keep)
 for i,w in groups:b.vertex_groups[i].remove([v.index])
 for i,w in keep:b.vertex_groups[i].add([v.index],w/total,'REPLACE')
print('KILT',len(cloth),'vertices',len(used)*4,'controls','rest offset max',max(moves,default=0));assert len(r.data.bones)<128;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_cloth.blend'))
