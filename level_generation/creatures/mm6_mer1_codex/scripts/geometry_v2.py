import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/death_audition.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;pv=np.array([a.value for a in me.attributes['piece'].data]);gn={g.index:g.name for g in o.vertex_groups}
bpy.data.actions.remove(bpy.data.actions['Death']);bpy.data.actions['Death1'].name='Death'
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
def put(v,w):
 for e in v.groups[:]:o.vertex_groups[e.group].remove([v.index])
 total=sum(w.values())
 for n,x in w.items():
  if x>1e-8:o.vertex_groups[n].add([v.index],float(x/total),'REPLACE')
for v in me.vertices:
 part=pv[v.index];x,y,z=v.co;s='L'if x>0 else'R'
 if part==1:
  # The native shoulder line is wider than the belly; retain depth and the fitted shoulder seam.
  v.co.x*=1-.16*(1-smooth((z-1.12)/.23))*smooth((z-.86)/.13)
  # The torso follows the spine, apart from the small shoulder cap.
  b=smooth((z-1.04)/.28);w={'B_Pelvis':1-b,'B_Spine2':b};a=.45*smooth((abs(x)-.16)/.09)*smooth((z-1.23)/.1);w={n:q*(1-a)for n,q in w.items()};w[f'B_{s}_UpperArm']=a;put(v,w)
 elif part in [8,9]:
  sh,el,wr=[r.data.bones[f'B_{s}_{n}'].head_local for n in ['UpperArm','Forearm','Hand']];u=(wr-el).normalized();t=(v.co-el).dot(u);f=smooth((t+.045)/.09);put(v,{f'B_{s}_UpperArm':1-f,f'B_{s}_Forearm':f})
 elif part==5:
  pel=smooth((z-.72)/.12);cal=1-smooth((z-.45)/.12);left=smooth((x+.035)/.07);w={'B_Pelvis':pel}
  for sd,share in [('L',left),('R',1-left)]:w[f'B_{sd}_Thigh']=(1-pel)*(1-cal)*share;w[f'B_{sd}_Calf']=(1-pel)*cal*share
  v.co.x*=.96;v.co.y*=.96;put(v,w)
 elif part in [6,7] and z<.016:v.co.z=0
 elif part in [10,13,16]:v.co.y-=.03
# Small pre-existing holes inside a sleeve and palm are modelling faults, not openings in the costume.
import bmesh
bm=bmesh.new();bm.from_mesh(me);seen=set();count=0
for e in list(bm.edges):
 if not e.is_boundary or e in seen:continue
 stack=[e];es=[]
 while stack:
  q=stack.pop()
  if q in seen:continue
  seen.add(q);es.append(q)
  for v in q.verts:stack +=[a for a in v.link_edges if a.is_boundary and a not in seen]
 if len(es)==4:bmesh.ops.holes_fill(bm,edges=es,sides=4);count+=1
# Join each open sleeve root to an inset ring on the shoulder shell, carrying interpolated host weights.
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import Vector
bm.verts.ensure_lookup_table();part=bm.verts.layers.int['piece'];deform=bm.verts.layers.deform.active
shell=[f for f in bm.faces if f.verts[0][part]==1];tree=BVHTree.FromPolygons([tuple(v.co)for v in bm.verts],[[v.index for v in f.verts]for f in shell]);newfaces=[]
for sd,pid in [('R',8),('L',9)]:
 edges=[e for e in bm.edges if e.is_boundary and all(v[part]==pid for v in e.verts) and min(v.co.z for v in e.verts)>1.18];verts=set(v for e in edges for v in e.verts);mapping={}
 for v in verts:
  loc,n,fi,d=tree.find_nearest(v.co);host=shell[fi];nv=bm.verts.new(loc-n*.003);nv[part]=pid;nv[deform].clear();vs=list(host.verts);ws=barycentric_transform(loc,*[a.co for a in vs[:3]],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
  for hv,w in zip(vs,ws):
   for gi,g in hv[deform].items():nv[deform][gi]=nv[deform].get(gi,0)+max(0,w)*g
  total=sum(nv[deform].values())
  for gi in list(nv[deform].keys()):nv[deform][gi]/=total
  mapping[v]=nv
 for e in edges:
  a,b=e.verts;newfaces.append(bm.faces.new((a,b,mapping[b],mapping[a])))
bmesh.ops.recalc_face_normals(bm,faces=newfaces)
print('BRIDGED sleeve roots',len(newfaces),'quads')
bm.to_mesh(me);bm.free();print('PATCHED accidental holes',count)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/actions_geometry_v2.blend'))
