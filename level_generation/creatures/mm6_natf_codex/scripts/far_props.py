"""Low-detail equipment retains the designed outline; tiny lacing is carried by the rebaked maps."""
import bpy,bmesh,json,sys,math,numpy as np
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduce_natf as red
from rebake_maps import bake
R=P/'review/far_props';W=P/'work/far_props';R.mkdir(exist_ok=True);W.mkdir(exist_ok=True)
def tube(V,F,points,r,sides):
 rings=[]
 for p in points:
  p=Vector(p);d=(Vector(points[-1])-Vector(points[0])).normalized();ref=Vector((1,0,0))if abs(d.x)<.8 else Vector((0,1,0));u=d.cross(ref).normalized();v=d.cross(u);ring=[]
  for i in range(sides):ring.append(len(V));V.append(tuple(p+r*(u*math.cos(i*math.tau/sides)+v*math.sin(i*math.tau/sides))))
  rings.append(ring)
 for a,b in zip(rings,rings[1:]):
  for i in range(sides):F.append((a[i],a[(i+1)%sides],b[(i+1)%sides],b[i]))
 F.extend([tuple(reversed(rings[0])),tuple(rings[-1])])
for part in ['ForearmBlade','LeafShield']:
 ob,rig=red.reset(part);ref=ob.copy();ref.data=ob.data.copy();bpy.context.collection.objects.link(ref);ref.name='BakeReference';ref.hide_render=True;V=[];F=[];M=rig.data.bones[part].matrix_local.copy()
 if part=='ForearmBlade':
  ys=[38,65,115,145,210,280,350,440,530,620,710,800,900,980,1028];left=[401,375,336,351,349,344,344,347,359,380,409,452,508,559,588];right=[406,412,414,413,414,420,414,418,433,457,491,530,563,582,588];rings=[];scale=.65/990
  for y in [38,115,210,350,530,710,900,980,1028]:
   l=float(np.interp(y,ys,left));r=float(np.interp(y,ys,right));w=max(r-l,1);z=(y-38)*scale;profile=[(l,0),(l+w*.18,-.0035),(r-w*.18,-.0035),(r,0),(r-w*.18,.0035),(l+w*.18,.0035)];rr=[]
   for x,d in profile:rr.append(len(V));V.append(((x-385)*scale+.010*min(1,max(0,(z-.17)/.065))+.003*max(0,1-abs(z-.205)/.1),d,z))
   rings.append(rr)
  for a,b in zip(rings,rings[1:]):
   for j in range(6):F.append((a[j],a[(j+1)%6],b[(j+1)%6],b[j]))
  F.extend([tuple(reversed(rings[0])),tuple(rings[-1])])
  for z,r in [(.035,.043),(.145,.033)]:tube(V,F,[(-r,0,z-.015),(-r,0,z+.015)],r+.003,6)
 else:
  outline=np.array(json.loads((P/'work/shield_outline.json').read_text()));ys=outline[:,0];width=outline[:,2]-outline[:,1];span=ys[-1]-ys[0];half=width/width.max()*.175;rings=[]
  for back in [False,True]:
   side=[]
   for y in np.linspace(ys[0],ys[-1],9):
    z=.61-1.22*(y-ys[0])/span;w=float(np.interp(y,ys,half))+.0055;row=[]
    for u in [-1,0,1]:
     depth=(.026*(1-abs(u))+.009*abs(u))if back else(-.039*(1-u*u)-.009*u*u);row.append(len(V));V.append((w*u,depth,z+math.copysign(.0035,z)*(abs(z)/.61)**8))
    side.append(row)
   rings.append(side)
   for a,b in zip(side,side[1:]):
    for k in range(2):F.append((a[k],a[k+1],b[k+1],b[k]))
  for k in [0,2]:
   for j in range(8):F.append((rings[0][j][k],rings[0][j+1][k],rings[1][j+1][k],rings[1][j][k]))
  for end in [0,-1]:
   for k in range(2):F.append((rings[0][end][k],rings[1][end][k],rings[1][end][k+1],rings[0][end][k+1]))
  tube(V,F,[(-.075,.045,.26),(.075,.045,.26)],.011,8)
  for x in [-.076,.076]:tube(V,F,[(x,.01,.26),(x,.045,.26)],.007,4)
 old=ob.data;mat=old.materials[0];me=bpy.data.meshes.new(part+'_Far');me.from_pydata([M@Vector(v)for v in V],[],F);me.update();me.uv_layers.new(name='UVMap');me.materials.append(mat);ob.data=me;ob.vertex_groups.clear();ob.vertex_groups.new(name=part).add(list(range(len(me.vertices))),1,'REPLACE');bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;maps=bake(ob,ref,R,part,size=256);bpy.data.objects.remove(ref,do_unlink=True);old.name=part+'_SourceUnused';me.name=part;blend=W/f'{part}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));row={'part':part,'lod':3,'ratio':'outline_preserving','triangles':red.count(ob),'blend':str(blend.relative_to(P)),'maps':maps};(R/f'{part}.json').write_text(json.dumps(row,indent=2));print('FAR_PROP',row,flush=True)
