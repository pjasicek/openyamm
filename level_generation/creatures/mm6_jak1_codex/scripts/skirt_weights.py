"""Transfer hip skin weights barycentrically to the wrap, avoiding nearest-vertex discontinuities."""
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import Vector
import json,math

def repair_skirt(body):
 me=body.data;pv=[a.value for a in me.attributes['piece'].data]
 if 'round2_wrap_rest' not in body:body['round2_wrap_rest']=json.dumps({v.index:list(v.co)for v,part in zip(me.vertices,pv)if part==1})
 original=json.loads(body['round2_wrap_rest'])
 for i,co in original.items():me.vertices[int(i)].co=co
 me.calc_loop_triangles()
 for v,part in zip(me.vertices,pv):
  x,y,z=v.co
  if part==0 and abs(x)<.25 and .89<z<1.10:
   pel=max(0,min(1,(z-.89)/.09));pel=max(pel,max(0,min(1,(.055-abs(x))/.035))*max(0,min(1,(z-.89)/.04)));side='L' if x>0 else 'R'
   for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
   for name,weight in [('B_Pelvis',pel),(f'B_{side}_Thigh',1-pel)]:
    if weight:body.vertex_groups[name].add([v.index],weight,'REPLACE')
 faces=[tuple(t.vertices) for t in me.loop_triangles if all(pv[i]==0 for i in t.vertices) and .55<t.center.z<1.17]
 tree=BVHTree.FromPolygons([v.co for v in me.vertices],faces);weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups}for v in me.vertices]
 for v,part in zip(me.vertices,pv):
  if part!=1:continue
  point,normal,fi,dist=tree.find_nearest(v.co);a,b,c=faces[fi];w=barycentric_transform(point,me.vertices[a].co,me.vertices[b].co,me.vertices[c].co,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));out={}
  for i,k in zip([a,b,c],w):
   for n,t in weights[i].items():out[n]=out.get(n,0)+max(0,k)*t
  total=sum(out.values())
  for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
  for n,w in out.items():
   if w>1e-8:body.vertex_groups[n].add([v.index],w/total,'REPLACE')

 # The fitted wrap needs clearance over the moving hip; the waistband retains its original width.
 for v,part in zip(me.vertices,pv):
  if part!=1:continue
  x,y,z=v.co;t=max(0,min(1,(1.08-z)/.12));t=t*t*(3-2*t);r=max(math.hypot(x,y),.01);v.co.x+=.04*t*x/r;v.co.y+=.04*t*y/r
