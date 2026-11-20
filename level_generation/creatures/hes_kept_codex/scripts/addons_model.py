"""Fitted, textured Kept add-ons from the generated HD prop references; body geometry stays unchanged."""
import bpy,bmesh,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/addons_v2/attack_candidates.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];sc=bpy.context.scene;rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for n in ('collar','plate','pick','club'):
 o=bpy.data.objects.get('hes_kept_'+n)
 if o:bpy.data.objects.remove(o,do_unlink=True)
# The control collar now follows the neck itself, with no floating fitted-head offset keys.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones['Kept_Collar'].parent=rig.data.edit_bones['B_Neck'];bpy.ops.object.mode_set(mode='OBJECT')
for a in bpy.data.actions:
 for l in a.layers:
  for s in l.strips:
   for cb in s.channelbags:
    for fc in list(cb.fcurves):
     if 'Kept_Collar' in fc.data_path:cb.fcurves.remove(fc)
D=np.load(P/'texturing/kept_m_uv.npz');pts=[v.co.copy() for v in body.data.vertices];head=BVHTree.FromPolygons(pts,D['faces'][D['piece']==1].tolist(),all_triangles=True);shirt=BVHTree.FromPolygons(pts,D['faces'][D['piece']==0].tolist(),all_triangles=True)
alltree=BVHTree.FromPolygons(pts,D['faces'].tolist(),all_triangles=True)
projection=json.loads((P/'textures/props_v2/projection.json').read_text());made={};report={}
def uv(name,x,y,back=False):
 box=projection[name]['boxes'][int(back)];return ((int(back)+(x-box[0])/(box[2]-box[0]))*.5,1-(y-box[1])/(box[3]-box[1]))
def mat(name):
 m=bpy.data.materials.new('KeptV2_'+name);m.use_nodes=True;m.use_backface_culling=True;m['openyamm_specular']=1.;m['openyamm_specular_mask']=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/'textures/props_v2'/f'{name}_{suffix}.png'));n.image.colorspace_settings.name=space;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return m
mats={n:mat(n) for n in ('collar','plate','pick','club')};glow=bpy.data.materials.new('KeptV2_OrangeSlot');glow.use_nodes=True;glow.use_backface_culling=True;bs=glow.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.55,.045,.003,1);bs.inputs['Emission Color'].default_value=(1,.14,.008,1);bs.inputs['Emission Strength'].default_value=2.;glow['openyamm_bloom']=True
class Mesh:
 def __init__(self,name):self.name=name;self.v=[];self.f=[];self.uv=[];self.mi=[]
 def face(self,points,coords,mi=0):
  k=len(self.v);self.v+=list(points);self.f.append(tuple(range(k,k+len(points))));self.uv+=list(coords);self.mi.append(mi)
 def finish(self):
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.materials.append(mats[self.name]);me.materials.append(glow);layer=me.uv_layers.new(name='UVMap')
  for l,t in zip(layer.data,self.uv):l.uv=t
  for p,i in zip(me.polygons,self.mi):p.material_index=i;p.use_smooth=False
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));assert all(f.calc_area()>1e-10 for f in bm.faces);bm.to_mesh(me);bm.free()
  o=bpy.data.objects.new('hes_kept_'+self.name,me);sc.collection.objects.link(o);made[self.name]=o;return o
 def box(self,center,size,uvbox,mi=0):
  c=Vector(center);s=Vector(size)*.5;v=[c+Vector((x*s.x,y*s.y,z*s.z)) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  for face in [(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5),(0,3,2,1),(4,5,6,7)]:self.face([v[i] for i in face],[uv(self.name,*p) for p in [(uvbox[0],uvbox[3]),(uvbox[2],uvbox[3]),(uvbox[2],uvbox[1]),(uvbox[0],uvbox[1])]],mi)
def tube(mesh,centers,radii,sides,mapper):
 rings=[]
 for i,(c,r) in enumerate(zip(centers,radii)):
  c=Vector(c);t=(Vector(centers[min(i+1,len(centers)-1)])-Vector(centers[max(0,i-1)])).normalized();x=t.cross(Vector((0,1,0)))
  if x.length<.1:x=t.cross(Vector((1,0,0)))
  x.normalize();y=t.cross(x);rings.append([c+r*(x*math.cos(j*math.tau/sides)+y*math.sin(j*math.tau/sides)) for j in range(sides)])
 for i in range(len(rings)-1):
  for j in range(sides):
   k=(j+1)%sides;ids=[(i,j),(i,k),(i+1,k),(i+1,j)];mesh.face([rings[a][b] for a,b in ids],[mapper(rings[a][b],a,b) for a,b in ids])
 for i,ids in [(0,list(reversed(range(sides)))),(len(rings)-1,list(range(sides)))]:mesh.face([rings[i][j] for j in ids],[mapper(rings[i][j],i,j) for j in ids])
def neckpoint(a,z,gap=0):
 c=Vector((-.03255,.034,z));direction=Vector((math.cos(a),math.sin(a),0));hit,n,idx,d=head.ray_cast(c+direction*.25,-direction,.5);assert hit is not None,(a,z)
 radius=max(.035,(hit-c).dot(direction));return c+direction*(radius+gap)
# Close inner liner, thick metal cuff, curved ivory segments, small upper spikes and a long throat slot.
m=Mesh('collar');N=24;zs=[1.432,1.451,1.469];rings=[]
for gap in (.0008,.008):
 for z in zs:rings.append([neckpoint(i*math.tau/N,z,gap) for i in range(N)])
for a,b in [(0,1),(1,2),(3,4),(4,5),(0,3),(2,5)]:
 for i in range(N):
  j=(i+1)%N;ids=[(a,i),(a,j),(b,j),(b,i)];m.face([rings[k][l] for k,l in ids],[uv('collar',380+22*(l%3)/2,425+(rings[k][l].z-1.432)/.037*160) for k,l in ids])
for i in range(12):
 a=(i+.5)*math.tau/12;rad=Vector((math.cos(a),math.sin(a),0));base=neckpoint(a,1.451,.007);centres=[neckpoint(a,1.451+z,gap) for gap,z in [(.017,.016),(.023,.007),(.028,-.009),(.024,-.026),(.019,-.032)]]
 tube(m,centres,[.008,.011,.010,.006,.0018],7,lambda p,k,j:uv('collar',112+25*(.5+.5*math.cos(j*math.tau/7)),440+k/4*158))
 if i%2==0 and math.sin(a)>-.3:
  q=neckpoint(a,1.469,.008);tube(m,[q,q+Vector((0,0,.009)),q+Vector((0,0,.019))],[.0055,.0035,.0008],6,lambda p,k,j:uv('collar',104+j*3,360-k*13))
front=neckpoint(-math.pi/2,1.451,.013);m.box((front.x,front.y-.004,1.442),(.026,.014,.060),(231,405,306,625));m.box((front.x,front.y-.012,1.442),(.006,.003,.046),(261,442,276,592),1);m.finish()
# Shaped ceramic chest shell, slightly proud of the actual shirt, plus a fitted leather harness.
m=Mesh('plate');cx=-.03255
Z=[1.12,1.16,1.22,1.28,1.32,1.345,1.365];W=[.10,.13,.142,.15,.145,.14,.135];rows=[]
def fronty(x,z):
 hit,n,idx,d=alltree.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)),1);assert hit is not None,(x,z);return hit.y
for z,w in zip(Z,W):
 row=[]
 for j in range(11):
  u=j/5-1;x=cx+w*u;zz=z+(.025*abs(u)-.018*(1-abs(u)) if z==Z[-1] else 0);y=fronty(x,zz)-.012-.009*(1-u*u);row.append(Vector((x,y,zz)))
 rows.append(row)
for back in (False,True):
 for i in range(len(rows)-1):
  for j in range(10):
   ids=[(i,j),(i,j+1),(i+1,j+1),(i+1,j)];ps=[rows[a][b]+Vector((0,.005 if back else 0,0)) for a,b in ids];ts=[uv('plate',300+(b/5-1)*240,825-(rows[a][b].z-Z[0])/(Z[-1]-Z[0])*580) for a,b in ids];m.face(ps,ts)
border=[rows[0][j] for j in range(11)]+[rows[i][-1] for i in range(1,len(rows))]+[rows[-1][j] for j in range(9,-1,-1)]+[rows[i][0] for i in range(len(rows)-2,0,-1)]
for a,b in zip(border,border[1:]+border[:1]):m.face([a,b,b+Vector((0,.005,0)),a+Vector((0,.005,0))],[uv('plate',x,y) for x,y in [(55,470),(60,480),(63,480),(58,470)]])
torsofs=[f for f,p in zip(D['faces'],D['piece']) if p==0 and all(abs(pts[int(i)].x-cx)<.195 for i in f)]
torso=BVHTree.FromPolygons(pts,torsofs,all_triangles=True)
def torusstrap(z,height):
 rings=[]
 for dz,gap in [(-height/2,.009),(height/2,.009),(-height/2,.014),(height/2,.014)]:
  ring=[]
  for i in range(32):
   a=i*math.tau/32;v=Vector((math.cos(a),math.sin(a),0));c=Vector((cx,.022,z+dz));hit,n,ix,d=torso.ray_cast(c+v*.4,-v,.8);assert hit is not None;ring.append(hit+v*gap)
  rings.append(ring)
 for a,b in [(0,1),(2,3),(0,2),(1,3)]:
  for j in range(32):
   k=(j+1)%32;m.face([rings[a][j],rings[a][k],rings[b][k],rings[b][j]],[uv('plate',x,y) for x,y in [(670+(j%4)*35,586),(705+(j%4)*35,586),(705+(j%4)*35,626),(670+(j%4)*35,626)]])
for z in (1.16,1.34):torusstrap(z,.027)
# Shoulder straps arc over the shirt rather than stretching flat across the torso.
for side in (-1,1):
 x=cx+side*.15;centres=[]
 for y,z in [(-.095,1.35),(-.075,1.40),(-.04,1.425),(0,1.435),(.045,1.435),(.085,1.41),(.115,1.37),(.12,1.33)]:
  point=Vector((x,y,z));hit,n,ix,dist=shirt.find_nearest(point);centres.append(hit+n*.012)
 left=[p+Vector((-.014,0,0)) for p in centres];right=[p+Vector((.014,0,0)) for p in centres]
 for i in range(len(left)-1):
  ps=[left[i],right[i],right[i+1],left[i+1]];uvs=[uv('plate',x,y) for x,y in [(100,120+i*20),(140,120+i*20),(140,140+i*20),(100,140+i*20)]]
  # A closed shallow leather strip, never a two-sided card.
  normal=(ps[1]-ps[0]).cross(ps[3]-ps[0]).normalized();other=[p-normal*.004 for p in ps];m.face(ps,uvs);m.face(list(reversed(other)),list(reversed(uvs)))
  for j in range(4):k=(j+1)%4;m.face([ps[j],ps[k],other[k],other[j]],[uvs[j],uvs[k],uvs[k],uvs[j]])
m.finish()
# Weapons retain the measured 2 cm grip radius; their +Z axes are the solved source-hand axis.
for name in ('pick','club'):
 m=Mesh(name)
 if name=='pick':
  stations=[(-.17,.020),(-.14,.020),(-.08,.020),(.02,.020),(.08,.020),(.2,.018),(.32,.020),(.40,.021),(.47,.018)]
  mapper=lambda p,k,j:uv('pick',410+p.x/.021*32,984-(p.z+.17)/.64*944)
 else:
  stations=[(-.17,.020),(-.14,.020),(-.08,.020),(.02,.020),(.09,.021),(.15,.034),(.18,.060),(.22,.066),(.28,.063),(.34,.068),(.40,.064),(.45,.051)]
  mapper=lambda p,k,j:uv('club',350+p.x/.074*132,988-(p.z+.17)/.62*954)
 centers=[Vector((0,0,z)) for z,r in stations];tube(m,centers,[r for z,r in stations],12,mapper)
 if name=='pick':
  outline=[(55,230),(137,159),(276,104),(373,79),(454,80),(610,119),(606,201),(470,158),(355,156),(245,159),(135,194)];front=[];back=[]
  for x,y in outline:
   p=Vector(((x-410)*.00062,0,984*.00066-y*.00066-.17));t=.013*max(.18,1-abs(x-410)/400);front.append(p+Vector((0,-t,0)));back.append(p+Vector((0,t,0)))
  m.face(front,[uv('pick',x,y) for x,y in outline]);m.face(list(reversed(back)),[uv('pick',x,y) for x,y in reversed(outline)])
  for j in range(len(outline)):
   k=(j+1)%len(outline);m.face([front[j],front[k],back[k],back[j]],[uv('pick',*outline[i]) for i in [j,k,k,j]])
  m.box((0,0,.39),(.052,.048,.073),(375,79,447,204))
 else:
  for z,r in [(.17,.066),(.32,.072)]:
   tube(m,[(0,0,z),(0,0,z+.046)],[r,r+.001],12,mapper)
 m.finish()
# World-space fitted weapon coordinates; same measured handle centre and grip radius on both weapons.
G=json.loads((P/'work/male/handle_R.json').read_text());A=Vector(G['handle_axis_hand_local']);S=json.loads((P/'work/male/source_rest.json').read_text());X=Matrix(S['B_R_Hand']['rot']).inverted()@(Vector(S['B_R_Finger2']['head'])-Vector(S['B_R_Hand']['head']));X=(X-A*X.dot(A)).normalized();grip=Matrix((X,A.cross(X),A)).transposed().to_4x4();grip.translation=Vector(G['handle_centre_hand_local']);grip=rig.data.bones['B_R_Hand'].matrix_local@grip
for name,o in made.items():
 if name in ('pick','club'):o.data.transform(grip@(Matrix.Rotation(math.pi,4,'Z') if name=='pick' else Matrix.Identity(4)))
 bone='Kept_'+name.capitalize();o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Carrier','ARMATURE');mod.object=rig;report[name]={'triangles':len(o.data.polygons),'vertices':len(o.data.vertices),'carrier':bone,'reference':f'references_props_v2/{name}.png'}
 # Reset stale basis even when an old action did not key the carrier.
 rig.pose.bones[bone].matrix_basis.identity()
# The breastplate follows the chest; straps follow their nearest skin/cloth surface.
from mathutils.geometry import barycentric_transform
alltree=BVHTree.FromPolygons(pts,D['faces'].tolist(),all_triangles=True)
o=made['plate'];o.vertex_groups.clear()
for g in body.vertex_groups:o.vertex_groups.new(name=g.name)
for v in o.data.vertices:
 hit,n,ix,dist=alltree.find_nearest(v.co);ids=D['faces'][ix];a,b,c=[pts[int(i)] for i in ids];w=barycentric_transform(hit,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));acc={}
 for i,weight in zip(ids,w):
  for g in body.data.vertices[int(i)].groups:acc[g.group]=acc.get(g.group,0)+max(0,weight)*g.weight
 acc=sorted(acc.items(),key=lambda x:-x[1])[:8];total=sum(x[1] for x in acc)
 for group,weight in acc:
  if weight>1e-6:o.vertex_groups[group].add([v.index],weight/total,'REPLACE')
report['plate']['carrier']='skinned chest and harness; nearest triangle barycentric body weights'
# Fitted finger channels are shared by the genuine armed candidates.
for a in [a for a in bpy.data.actions if a.name.startswith('Kept_Club')]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 from mathutils import Quaternion
 for n,q in G['finger_local'].items():
  for f in range(int(a.frame_range[1])+1):rig.pose.bones[n].rotation_quaternion=Quaternion(q);rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/addons_v2/equipped.blend'));(P/'review/addons_v2/geometry.json').write_text(json.dumps(report,indent=2)+'\n');print('ADDONS_V2',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
