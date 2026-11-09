"""Bake continuous lower-robe strips around the moving boots, preserving the existing drape."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,geometry
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
# The generated shin shafts are always covered; keep the shoes and ankle, remove hidden upper shafts.
bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
for pi in [7,8]:
 verts=[v for v in bm.verts if v[pl]==pi];edges=[e for e in bm.edges if all(v[pl]==pi for v in e.verts)];faces=[f for f in bm.faces if all(v[pl]==pi for v in f.verts)]
 bmesh.ops.bisect_plane(bm,geom=verts+edges+faces,plane_co=(0,0,.085),plane_no=(0,0,1),clear_outer=True,dist=1e-6)
bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles()
pv=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);ids=np.where(pv==1)[0];boots=np.where(np.isin(pv,[7,8]))[0]
faces=[tuple(t.vertices) for t in me.loop_triangles if all(pv[i]==1 for i in t.vertices)]
# Keep the shoe width inside the close woven folds; the hidden shaft has already been removed.
for i in boots:
 v=me.vertices[int(i)];sd='L' if v.co.x>0 else 'R';ankle=r.data.bones[f'B_{sd}_Foot'].head_local;v.co.x=ankle.x+(v.co.x-ankle.x)*.85
 for g in list(v.groups):b.vertex_groups[g.group].remove([int(i)])
 b.vertex_groups[f'B_{sd}_Foot'].add([int(i)],1,'REPLACE')
# Narrow central blending gives each cloth strip the motion of its own thigh and shin.
for i in ids:
 v=me.vertices[int(i)];z=v.co.z;wl=max(0,min(1,(v.co.x+.046)/.08));wl=wl*wl*(3-2*wl)
 t=max(0,min(1,(1.02-z)/.18));calf=max(0,min(1,(.68-z)/.23));foot=max(0,min(1,(.36-z)/.13))
 w={'B_Pelvis':1-t}
 for sd,amount in [('L',wl),('R',1-wl)]:
  w[f'B_{sd}_Thigh']=t*amount*(1-calf);w[f'B_{sd}_Calf']=t*amount*calf*(1-foot);w[f'B_{sd}_Foot']=t*amount*calf*foot
 for g in list(v.groups):b.vertex_groups[g.group].remove([int(i)])
 for n,weight in w.items():
  if weight>1e-7:b.vertex_groups[n].add([int(i)],weight,'REPLACE')
 # Keep the leading boot inside the lower cloth, with the original woven folds retained.
 u=max(0,min(1,(.40-z)/.25));v.co.x=-.006+(v.co.x+.006)*(1+.12*u);v.co.y=-.03+(v.co.y+.03)*(1+.12*u)
 v.co.z+=.04*max(0,min(1,(.30-z)/.20))
 waist=max(0,min(1,(z-.94)/.10));waist=waist*waist*(3-2*waist);v.co.x=-.006+(v.co.x+.006)*(1-.035*waist);v.co.y=-.03+(v.co.y+.03)*(1-.035*waist)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
