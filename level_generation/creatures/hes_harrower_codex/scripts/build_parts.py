"""Original Harrower equipment on the read-only shared Demon body; all dimensions in metres."""
from pathlib import Path
import json,sys,math
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/shell.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Keep every source-body face, including the tail and sculpted harness.
body.data.attributes['shell_hidden'].data.foreach_set('value',[0]*len(body.data.vertices))
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
L=json.loads((P/'work/armour_layout.json').read_text());AT=L['atlas']
RECT={'resin':(4,440,440,850),'cloth':(460,440,400,850),'ivory':(880,440,300,400),'gold':(1200,440,260,350),'hide':(1480,440,400,1000)}
for name,rect in RECT.items():
 style={'resin':'resin','cloth':'cloth','ivory':'spike','gold':'gold','hide':'hide'}[name]
 L['plates']['parts_'+name]={'rect':rect,'size_m':[rect[2]/950,rect[3]/950],'style':style,'glow':[],'studs':[]}
(P/'work/armour_layout.json').write_text(json.dumps(L,indent=2)+'\n')
MATS=[bpy.data.materials['HKR_Plate'],bpy.data.materials['HKR_Glow']]
def uv(kind,u,v):
 x,y,w,h=RECT[kind];return ((x+4+(w-8)*u)/AT,1-(y+4+(h-8)*v)/AT)
def bone(name,parent,mat):
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 b=rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name);b.head=(0,0,0);b.tail=(0,.08,0);b.matrix=mat;b.length=.08;b.parent=rig.data.edit_bones[parent];b.use_deform=True
 bpy.ops.object.mode_set(mode='OBJECT')
class Part:
 def __init__(self,name,bn,boss=False,tier=None):self.name=name;self.bn=bn;self.boss=boss;self.tier=tier;self.v=[];self.f=[];self.uv=[];self.mi=[];self.w=[]
 def add(self,V,F,kind='ivory',material=0,UV=None,weights=None):
  off=len(self.v);self.v.extend([tuple(x) for x in V]);self.f.extend([tuple(off+i for i in f) for f in F]);self.mi.extend([material]*len(F))
  self.uv.extend(UV or [uv(kind,(i%8)/7,(i//8)/max(1,(len(V)-1)//8)) for i in range(len(V))]);self.w.extend(weights or [{self.bn:1.} for x in V])
 def finish(self):
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update()
  for m in MATS:me.materials.append(m)
  layer=me.uv_layers.new(name='UVMap')
  for f,mi in zip(me.polygons,self.mi):
   f.material_index=mi;f.use_smooth=True
   for li in f.loop_indices:layer.data[li].uv=self.uv[me.loops[li].vertex_index]
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='SHORT_EDGE');bm.to_mesh(me);bm.free()
  ob=bpy.data.objects.new(self.name,me);sc.collection.objects.link(ob);ob.parent=rig
  for name in sorted({n for w in self.w for n in w}):
   group=ob.vertex_groups.new(name=name)
   for i,w in enumerate(self.w):
    if w.get(name,0)>0:group.add([i],w[name],'REPLACE')
  md=ob.modifiers.new('Armature','ARMATURE');md.object=rig
  ob['boss_only']=self.boss;ob['family_only']=self.name.startswith('Family_');ob['component']=self.name
  if self.tier:ob['tier']=self.tier
  return ob

def tube(part,points,radii,kind='ivory',sides=6,material=0,flatten=1.):
 pts=[Vector(p) for p in points];V=[];UV=[];F=[]
 for k,c in enumerate(pts):
  d=(pts[min(k+1,len(pts)-1)]-pts[max(k-1,0)]).normalized();ref=Vector((0,-1,0))
  if abs(d.dot(ref))>.94:ref=Vector((1,0,0))
  a=(ref-d*d.dot(ref)).normalized();b=d.cross(a)
  for j in range(sides):
   t=2*math.pi*j/sides;V.append(c+radii[k]*(a*math.cos(t)*flatten+b*math.sin(t)));UV.append(uv(kind,j/(sides-1),k/(len(pts)-1)))
 for k in range(len(pts)-1):
  for j in range(sides):F.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
 F.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);part.add(V,F,kind,material,UV)
def horn(part,start,end,r=.025,kind='ivory'):
 a,b=Vector(start),Vector(end);d=b-a;tube(part,[a,a+d*.45+Vector((0,-.01,.01)),a+d*.8,b],[r,r*.65,r*.3,.0018],kind,5)
def ring(part,c,axis,r,t=.006,kind='gold'):
 c=Vector(c);d=Vector(axis).normalized();a=d.orthogonal().normalized();b=d.cross(a);V=[];F=[]
 for i in range(8):
  radial=a*math.cos(2*math.pi*i/8)+b*math.sin(2*math.pi*i/8)
  for j in range(3):V.append(c+radial*(r+t*math.cos(j*2*math.pi/3))+d*t*math.sin(j*2*math.pi/3))
 for i in range(8):
  for j in range(3):F.append((i*3+j,i*3+(j+1)%3,((i+1)%8)*3+(j+1)%3,((i+1)%8)*3+j))
 part.add(V,F,kind)
# Blades are rigid child nodes in the calibrated fist's exact grip frame.
for sd in 'LR':
 H=rig.data.bones[f'B_{sd}_Hand'].matrix_local;z=Vector(G[sd]['handle_axis_hand_local']);x=Vector(G[sd]['blade_out_hand_local']);y=z.cross(x).normalized()
 local=Matrix((x,y,z)).transposed().to_4x4();local.translation=Vector(G[sd]['handle_centre_hand_local']);BM=H@local
 bone('Blade_'+sd,f'B_{sd}_Hand',BM)
 for boss,scale in ((False,1.),(True,1.25)):
  part=Part(('Vreth_' if boss else 'Family_')+'Blade_'+sd,'Blade_'+sd,boss)
  def world(p):return BM@Vector(p)
  def btube(points,radii,kind='ivory',sides=6,mat=0):tube(part,[world(p) for p in points],radii,kind,sides,mat)
  btube([(0,0,-.09),(0,0,.09)],[.017,.017],'resin',8)
  # A bone knuckle guard over the fist, with three gold studs and long root fins.
  btube([(.015,-.070,-.13),(.09,-.085,-.09),(.105,-.085,0),(.09,-.085,.09),(.015,-.070,.13)],[.019,.021,.021,.021,.019],'ivory',6)
  for zz in (-.09,0,.09):
   btube([(.095,-.095,zz),(.095,-.112-(.018 if boss and zz==0 else 0),zz)],[.013,.009],'gold',6)
  for direction,length in ((1,.79),(-1,.54)):
   N=9;centres=[];perps=[];widths=[]
   for k in range(N+1):
    t=k/N;z0=direction*(.12+length*t)*scale;x0=(.045+.26*math.sin(math.pi*t)-.15*t)*scale
    dx=(.26*math.pi*math.cos(math.pi*t)-.15)*scale;dz=direction*length*scale
    pe=Vector((abs(dz),0,-direction*dx)).normalized();centres.append(Vector((x0,0,z0)));perps.append(pe);widths.append((.035+.045*math.sin(math.pi*t))*(1-t)**.35*scale+.002)
   V=[];UV=[];F=[]
   for k,(c,e,w) in enumerate(zip(centres,perps,widths)):
    thick=(.018*(1-k/N)+.003)*scale
    for j,p in enumerate((c-e*w,c+Vector((0,-thick,0)),c+e*w,c+Vector((0,thick,0)))):V.append(world(p));UV.append(uv('resin',j/3,k/N))
   for k in range(N):
    for j in range(4):F.append((k*4+j,k*4+(j+1)%4,(k+1)*4+(j+1)%4,(k+1)*4+j))
   F.extend([(3,2,1,0),tuple(N*4+j for j in range(4))]);part.add(V,F,'resin',0,UV)
   # The glowing strip follows only the convex outer cutting edge.
   edge=[c+e*w for c,e,w in zip(centres,perps,widths)]
   btube(edge,[.0055*scale]*(N)+[.002],'gold',4,1)
   # The diamond section provides the raised rib; the atlas supplies the fine gold inlay.
   for k,fraction in enumerate((.19,.43,.66)):
    i=round(fraction*N);c=centres[i]-perps[i]*widths[i]*.8
    tip=c+Vector((-(.105-.019*k)*scale,0,-direction*(.075-.008*k)*scale))
    horn(part,world(c),world(tip),.021*scale)
   c=centres[0]-perps[0]*widths[0]*.6;horn(part,world(c),world(c+Vector((-.10,0,direction*.12))*scale),.025*scale)
   ring(part,world(centres[0]),world(centres[1])-world(centres[0]),.033*scale,.006)
   if boss:
    c=centres[6];horn(part,world(c),world(c+Vector((-.08,0,-direction*.055))),.016)
    ring(part,world(centres[-3]),world(centres[-2])-world(centres[-3]),widths[-3]*.65,.006)
  part.finish()
# Head crest and Vreth's rings follow the existing source head without changing either horn.
bone('Harrower_Crest','B_Head',rig.data.bones['B_Head'].matrix_local)
bone('Harrower_Trophies','B_Spine2',rig.data.bones['B_Spine2'].matrix_local)
CO=[v.co.copy() for v in body.data.vertices];faces=[tuple(f.vertices) for f in body.data.polygons]
TREE=BVHTree.FromPolygons(CO,faces)
def top(x,y):
 h=TREE.ray_cast(Vector((x,y,2.3)),Vector((0,0,-1)),2.)[0]
 return h.z if h else 1.67
CTRL=np.array([(0.040,-.285,1.640),(.118,-.287,1.685),(.172,-.268,1.790),(.128,-.240,1.880)])
def horn_curve(t):return (1-t)**3*CTRL[0]+3*(1-t)**2*t*CTRL[1]+3*(1-t)*t*t*CTRL[2]+t**3*CTRL[3]
for boss in (False,True):
 part=Part(('Vreth_' if boss else 'Family_')+'Crest','Harrower_Crest',boss)
 ys=np.linspace(-.31,-.09,5 if boss else 3)
 for i,y in enumerate(ys):
  z0=top(0,y)-.008;length=(.12 if len(ys)==3 else .13)+.06*(1-abs(i-(len(ys)-1)/2)/max(1,(len(ys)-1)/2))
  horn(part,(0,y,z0),(0,y+.045,z0+length),.022)
 if boss:
  for sg in (-1,1):
   for t in (.32,.61):
    c=horn_curve(t)*[sg,1,1];axis=(horn_curve(t+.01)-horn_curve(t-.01))*[sg,1,1]
    ring(part,c,axis,.035*(1-t)**.9+.006,.005)
 part.finish()
def front(x,z,offset=.035):
 p=TREE.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2.)[0]
 return Vector((x,(p.y if p else -.35)-offset,z))
for boss in (False,True):
 part=Part(('Vreth_' if boss else 'Family_')+'Trophies','Harrower_Trophies',boss,'BC')
 for sg in ((-1,1) if boss else (1,)):
  pts=[front(sg*(.17-.28*t),1.40-.28*t,.045) for t in np.linspace(0,1,7)]
  tube(part,pts,[.009]*7,'resin',5)
  for i in (1,3,5):
   c=pts[i];ring(part,c,(0,1,0),.023,.005);horn(part,c+Vector((0,-.006,-.02)),c+Vector((sg*.01,-.025,-.09)),.018)
 part.finish()
# Narrow wraps around the upper arms, with constant weights across each rigid band.
for sd in 'LR':
 a=rig.data.bones[f'B_{sd}_UpperArm'].head_local;b=rig.data.bones[f'B_{sd}_Forearm'].head_local
 part=Part('Wrap_'+sd,f'B_{sd}_UpperArm');ring(part,a.lerp(b,.45),b-a,.080,.015,'cloth');part.finish()
# Three narrow front/back strips and five long mantle strips. Each has its own three-bone chain.
chains=[];mantle=[]
def cloth(name,pts,width,boss=False,hide=False,parent='B_Pelvis',deg=0):
 names=[name+'_'+str(k) for k in range(3)]
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');par=rig.data.edit_bones[parent]
 for k,n in enumerate(names):
  b=rig.data.edit_bones.new(n);b.head=pts[k];b.tail=pts[k+1];b.parent=par;b.use_connect=k>0;par=b
 bpy.ops.object.mode_set(mode='OBJECT')
 ch={'deg':deg,'group':name,'pts':[list(p) for p in pts],'bones':names};(mantle if boss else chains).append(ch)
 part=Part(name,names[0],boss);V=[];UV=[];W=[];F=[];rows=5
 for layer in (-1,1):
  for i in range(rows):
   u=i/(rows-1);seg=min(2,int(u*3));t=u*3-seg;c=Vector(pts[seg]).lerp(Vector(pts[seg+1]),t)
   rag=1. if i<rows-2 else (.82 if i==rows-2 else .20)
   for j in range(3):
    side=(j-1)*width*.5*rag;zoff=(-.022 if j==1 and i==rows-1 else .0)
    V.append(c+Vector((side,layer*.0015,zoff)));UV.append(uv('hide' if hide else 'cloth',j/2,u));ww={names[seg]:1.}
    if seg<2:ww={names[seg]:1-t,names[seg+1]:t}
    W.append(ww)
 n=rows*3
 for layer in range(2):
  for i in range(rows-1):
   for j in range(2):
    q=(layer*n+i*3+j,layer*n+i*3+j+1,layer*n+(i+1)*3+j+1,layer*n+(i+1)*3+j);F.append(q if layer==0 else tuple(reversed(q)))
 border=[0,1,2]+[i*3+2 for i in range(1,rows)]+[n-2,n-3]+[i*3 for i in range(rows-2,0,-1)]
 for a,b in zip(border,border[1:]+border[:1]):F.append((a,b,b+n,a+n))
 part.add(V,F,'hide' if hide else 'cloth',0,UV,W)
 # Thin closed ember hems use the same weights as the cloth edge.
 for col in (0,2):
  v=[];w=[];ff=[]
  for i in range(rows):
   k=i*3+col;p0=Vector(V[k]);v.extend([p0+Vector((-.002,-.002,0)),p0+Vector((.002,-.002,0))]);w.extend([W[k],W[k]])
  for i in range(rows-1):ff.append((i*2,i*2+1,(i+1)*2+1,(i+1)*2))
  part.add(v,ff,'gold',1,weights=w)
 part.finish()
for frontside in (True,False):
 for k,x in enumerate((-.09,0,.09)):
  y=-.42 if frontside else .055;endz=.38+.035*(k%2);end_y=y+(-.04 if frontside else .16)
  pts=[Vector((x,y,.96)).lerp(Vector((x*1.25,end_y,endz)),t) for t in (0,1/3,2/3,1)]
  cloth('Cloth_'+('F' if frontside else 'B')+str(k),pts,.078,deg=180 if frontside else 0)
for k,x in enumerate((-.20,-.10,0,.10,.20)):
 pts=[Vector((x,.035,1.45)).lerp(Vector((x*1.5,.25,.30+.04*(k%2))),t) for t in (0,1/3,2/3,1)]
 cloth('Mantle_'+str(k),pts,.115,boss=True,hide=k%2==0,parent='B_Spine2',deg=0)
sc['cloth_chains']=json.dumps(chains);sc['mantle_chains']=json.dumps(mantle)
# Pale scars are narrow fitted overlays carried by the same body bones beneath them.
part=Part('Vreth_Scars','B_Spine1',True)
for x,z in ((-.11,1.20),(.09,1.27),(-.035,1.13)):
 pts=[front(x+.065*t,z+.045*t,.004) for t in (0,.5,1)];tube(part,pts,[.002,.003,.0015],'ivory',4)
part.finish()
# C shoulder caps are rigid, separable tier attachments; the family shell remains common.
for sd in 'LR':
 ob=bpy.data.objects['Arm_pauldron_'+sd]
 for g in list(ob.vertex_groups):ob.vertex_groups.remove(g)
 ob.vertex_groups.new(name=f'B_{sd}_Pauldron').add(list(range(len(ob.data.vertices))),1.,'REPLACE');ob['tier']='C'
assert len(rig.data.bones)<=128,len(rig.data.bones)
report={'bones':len(rig.data.bones),'components':{o.name:sum(len(f.vertices)-2 for f in o.data.polygons) for o in bpy.data.objects if o.type=='MESH'}}
for boss in (False,True):
 tris=sum(v for n,v in report['components'].items() if not (boss and n.startswith('Family_')) and not (not boss and (n.startswith('Vreth_') or n.startswith('Mantle_'))))
 report['vreth_triangles' if boss else 'family_max_triangles']=tris
 assert tris<=15000,(boss,tris,report['components'])
(P/'review/components.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipment.blend'))
