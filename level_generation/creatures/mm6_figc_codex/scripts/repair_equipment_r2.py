"""Image-guided equipment: dimensional forge work and curved shield; preserve fitted bone frames."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round2/before/work/final_motion.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
ATLAS=2048
class Mesh:
 def __init__(self):self.v=[];self.f=[];self.uv=[];self.smooth=[]
 def vert(self,p):self.v.append(tuple(p));return len(self.v)-1
 def face(self,ids,coords,smooth=True):
  self.f.append(ids);self.uv.append([(x/ATLAS,1-y/ATLAS) for x,y in coords]);self.smooth.append(smooth)
 def patch(self,ids,kind='steel',smooth=True):
  x0,y0,x1,y1=TILES[kind]
  self.face(ids,[(x0+(x1-x0)*(.5+.46*math.cos(i*2*math.pi/len(ids))),y0+(y1-y0)*(.5+.46*math.sin(i*2*math.pi/len(ids)))) for i in range(len(ids))],smooth)
 def save(self,name):
  me=bpy.data.meshes.new(name+'_review2');me.from_pydata(self.v,[],self.f);me.update();uv=me.uv_layers.new(name='UVMap')
  for poly,coords,smooth in zip(me.polygons,self.uv,self.smooth):
   poly.use_smooth=smooth
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
  ob=bpy.data.objects[name];ob.data=me;ob.vertex_groups.clear();ob.vertex_groups.new(name=name).add(list(range(len(me.vertices))),1,'REPLACE')
  me.calc_loop_triangles();uv=me.uv_layers.active
  for tri in me.loop_triangles:
   a,b,c=[uv.data[i].uv for i in tri.loops]
   assert abs((b-a).x*(c-a).y-(b-a).y*(c-a).x)>1e-11,(name,tri.polygon_index)
  return len(me.loop_triangles)
 def tube(self,a,b,radii,kind,n=12):
  a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.orthogonal().normalized();v=axis.cross(u).normalized();rings=[]
  for t,r in radii:rings.append([self.vert(a.lerp(b,t)+(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n))*r) for i in range(n)])
  x0,y0,x1,y1=TILES[kind]
  for j in range(len(rings)-1):
   for i in range(n):
    k=(i+1)%n;self.face([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],[(x0+(x1-x0)*s,y1-(y1-y0)*t) for s,t in [(i/n,j/(len(rings)-1)),((i+1)/n,j/(len(rings)-1)),((i+1)/n,(j+1)/(len(rings)-1)),(i/n,(j+1)/(len(rings)-1))]])
  self.patch(rings[0][::-1],kind);self.patch(rings[-1],kind)
TILES=json.loads((P/'textures/figc_gear_tiles.json').read_text())
eq=json.loads((P/'work/equipment.json').read_text());c=Vector(eq['axe_centre']);axis=Vector(eq['axe_axis']);edge=Vector(eq['axe_edge']);normal=axis.cross(edge).normalized()
M=Mesh()
def axe_point(x,y,d):return c+axis*(-.11+(1455-y)*(.58/1430))+edge*((x-512)*(.366/826))+normal*d
def axe_uv(x,y):return (1024+x,y)
# Paired crescent forgings: full volume tapers from the eye to the sharpened curved perimeter.
outline=[(410,205),(372,204),(325,188),(291,164),(263,123),(240,73),(227,26),(194,62),(161,113),(134,176),(114,236),(101,300),(103,372),(114,434),(138,492),(171,545),(227,590),(241,542),(252,494),(274,449),(306,416),(348,404),(377,407),(410,420)]
for bit in [-1,1]:
 side_rings=[]
 for side in [-1,1]:
  rings=[];pixels=[]
  for scale,depth in [(1,.0009),(.91,.0065),(.73,.0125),(.40,.016)]:
   pts=[(325+(x-325)*scale,307+(y-307)*scale) for x,y in outline];ids=[]
   for i,(x,y) in enumerate(pts):
    # The socket-facing edge retains its thick section instead of sharpening every edge.
    thickness=depth if 5<=i<=17 else max(depth,.011+(x-325)*.00004)
    xx=x if bit<0 else 1024-x;ids.append(M.vert(axe_point(xx,y,side*thickness)))
   rings.append(ids);pixels.append([axe_uv(x if bit<0 else 1024-x,y) for x,y in pts])
  for j in range(len(rings)-1):
   for i in range(len(outline)):
    k=(i+1)%len(outline);M.face([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],[pixels[j][i],pixels[j][k],pixels[j+1][k],pixels[j+1][i]],smooth=j>0)
  hub=M.vert(axe_point(325 if bit<0 else 699,307,side*.017));huv=axe_uv(325 if bit<0 else 699,307)
  for i in range(len(outline)):
   k=(i+1)%len(outline);M.face([rings[-1][i],rings[-1][k],hub],[pixels[-1][i],pixels[-1][k],huv])
  side_rings.append(rings[0])
 for i in range(len(outline)):
  k=(i+1)%len(outline);M.patch([side_rings[0][i],side_rings[0][k],side_rings[1][k],side_rings[1][i]],'edge',False)
# Wooden haft and eight raised leather turns, with the original 11.5 mm grip radius.
M.tube(c-axis*.105,c+axis*.43,[(0,.0104),(.4,.0096),(1,.011)],'wood',12)
turns=8;steps=turns*16;rings=[]
for i in range(steps+1):
 theta=i/16*2*math.pi;off=-.085+i/steps*.19;radial=edge*math.cos(theta)+normal*math.sin(theta)
 rings.append([M.vert(c+axis*(off+delta)+radial*r) for delta,r in [(0,.0108),(.002,.0115),(.019,.0115),(.021,.0108)]])
x0,y0,x1,y1=TILES['leather']
for i in range(steps):
 for k in range(3):
  u=(i%16)/16;v=(i%16+1)/16;M.face([rings[i][k],rings[i+1][k],rings[i+1][k+1],rings[i][k+1]],[(x0+(x1-x0)*s,y0+(y1-y0)*t) for s,t in [(u,k/3),(v,k/3),(v,(k+1)/3),(u,(k+1)/3)]])
for a,b,r,kind in [(-.116,-.087,.014,'steel'),(.112,.128,.0124,'leather')]:M.tube(c+axis*a,c+axis*b,[(0,r*.76),(.20,r),(.75,r),(1,r*.82)],kind,12)
# Oval socket; its image-projected front and rear carry forged texture rather than a colour swatch.
rings=[];pixels=[]
for py,rx,rz in [(150,.026,.017),(171,.030,.021),(452,.029,.020),(486,.025,.017)]:
 ids=[];uv=[]
 for i in range(16):
  angle=i*2*math.pi/16;xx=512+rx*math.cos(angle)/(.366/826);ids.append(M.vert(axe_point(xx,py,rz*math.sin(angle))));uv.append(axe_uv(512+53*math.cos(angle),py))
 rings.append(ids);pixels.append(uv)
for j in range(3):
 for i in range(16):
  k=(i+1)%16;coords=[pixels[j][i],pixels[j][k],pixels[j+1][k],pixels[j+1][i]]
  M.face([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],coords)
M.patch(rings[0][::-1],'steel');M.patch(rings[-1],'steel')
# Visible narrow langets and four rivets on each side of the head; nothing buried inside the eye.
for side in [-1,1]:
 for x in [432,594]:
  a=axe_point(x,215,side*.012);b=axe_point(x,421,side*.012)
  M.tube(a,b,[(0,.008),(.08,.009),(.92,.009),(1,.007)],'steel',6)
  for y in [245,373]:
   a=axe_point(x,y,side*.016);b=axe_point(x,y,side*.023)
   M.tube(a,b,[(0,.006),(.55,.007),(1,.003)],'steel',8)
axe_tri=M.save('Axe')
# Frozen original standing grip frame supplies the shield basis.
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
lh=rig.pose.bones['B_L_Hand'].matrix.copy();grip=json.loads((P/'work/grip_pose_left.json').read_text());centre=lh@Vector(grip['handle_centre_hand_local']);handle_world=lh.to_3x3()@Vector(grip['handle_axis_hand_local']);D=rig.data.bones['B_L_Hand'].matrix_local@lh.inverted()
c2=D@centre;right=(D.to_3x3()@Vector((1,0,0))).normalized();up=(D.to_3x3()@Vector((0,0,1))).normalized();out=(D.to_3x3()@Vector((0,-1,0))).normalized();handle=(D.to_3x3()@handle_world).normalized();center=c2+out*.075+up*.05
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
M=Mesh();M.tube(c2-handle*.075,c2+handle*.075,[(0,.011),(1,.011)],'leather',12)
def xy(px,py):return ((px-510)*(.366/663),.370-(py-28)*(.767/1449))
def curve(px,py):
 x,z=xy(px,py);return .042*(1-(x/.192)**2)+.005*(1-(z/.43)**2)
def point(px,py,d):
 x,z=xy(px,py);return center+right*x+up*z+out*d
outer=[(342,28),(678,28),(841,411),(696,1413),(654,1477),(372,1477),(328,1413),(178,411)]
inner=[(369,78),(650,77),(800,422),(659,1404),(637,1428),(389,1428),(363,1404),(227,420)]
def subdiv(poly,n=4):
 return [(a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n) for a,b in zip(poly,poly[1:]+poly[:1]) for j in range(n)]
outer=subdiv(outer);inner=subdiv(inner);N=len(outer)
# Raised rolled rim is a bevelled cross-section around the complete curved perimeter.
prev=None;prevpx=None
for t,offset in [(0,-.014),(0,.003),(.16,.011),(.86,.011),(1,0)]:
 px=[(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for a,b in zip(outer,inner)];ring=[M.vert(point(x,y,curve(x,y)+offset)) for x,y in px]
 if prev:
  for i in range(N):
   j=(i+1)%N;ids=[prev[i],prev[j],ring[j],ring[i]]
   if t==0:M.patch(ids,'wood',False)
   else:M.face(ids,[prevpx[i],prevpx[j],px[j],px[i]])
 else:back=ring
 prev=ring;prevpx=px
# Four concentric face rings follow a cylindrical dome; paint contains the worn four-point star.
for s in [.75,.5,.25]:
 px=[(510+(x-510)*s,750+(y-750)*s) for x,y in inner];ring=[M.vert(point(x,y,curve(x,y))) for x,y in px]
 for i in range(N):
  j=(i+1)%N;M.face([prev[i],prev[j],ring[j],ring[i]],[prevpx[i],prevpx[j],px[j],px[i]])
 prev=ring;prevpx=px
hub=M.vert(point(510,750,curve(510,750)))
for i in range(N):j=(i+1)%N;M.face([prev[i],prev[j],hub],[prevpx[i],prevpx[j],(510,750)])
# Back has the same actual curve and inexpensive wood planks, not a hidden dense duplicate front.
backcenter=M.vert(point(510,750,curve(510,750)-.018))
for i in range(N):j=(i+1)%N;M.patch([back[j],back[i],backcenter],'wood')
# Boss is a raised elliptical dome; its UV follows the painted boss exactly.
prev=None;prevpx=None
for radius,height in [(1,0),(.96,.004),(.82,.018),(.48,.030)]:
 px=[(510+70*radius*math.cos(i*2*math.pi/16),599+110*radius*math.sin(i*2*math.pi/16)) for i in range(16)];ring=[M.vert(point(x,y,curve(x,y)+height+.002)) for x,y in px]
 if prev:
  for i in range(16):j=(i+1)%16;M.face([prev[i],prev[j],ring[j],ring[i]],[prevpx[i],prevpx[j],px[j],px[i]])
 prev=ring;prevpx=px
hub=M.vert(point(510,599,curve(510,599)+.035))
for i in range(16):j=(i+1)%16;M.face([prev[i],prev[j],hub],[prevpx[i],prevpx[j],(510,599)])
studs=[(360,49),(663,49),(291,193),(727,193),(214,375),(801,375),(215,545),(810,545),(243,731),(779,728),(267,939),(757,938),(288,1142),(729,1146),(343,1381),(682,1380),(392,1447),(632,1446)]
for px,py in studs:
 prev=None;prevpx=None
 for radius,d in [(15,0),(14,.004),(8,.008)]:
  pixels=[(px+radius*math.cos(i*2*math.pi/8),py+radius*math.sin(i*2*math.pi/8)) for i in range(8)];ring=[M.vert(point(x,y,curve(x,y)+.010+d)) for x,y in pixels]
  if prev:
   for i in range(8):j=(i+1)%8;M.face([prev[i],prev[j],ring[j],ring[i]],[prevpx[i],prevpx[j],pixels[j],pixels[i]])
  prev=ring;prevpx=pixels
 hub=M.vert(point(px,py,curve(px,py)+.020))
 for i in range(8):j=(i+1)%8;M.face([prev[i],prev[j],hub],[prevpx[i],prevpx[j],(px,py)])
# Two leather supports reach from the wood core to the retained fitted hand grip.
for sign in [-1,1]:
 a=c2+handle*.060*sign;b=a+out*.055;M.tube(a,b,[(0,.013),(.25,.013),(1,.010)],'leather',8)
shield_tri=M.save('Shield')
# Recheck the dropped props against the floor; new bevels must not sink below the previous floor fit.
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for name in ['Axe','Shield']:
 ob=bpy.data.objects[name];rest=rig.data.bones[name].matrix_local;local=[rest.inverted()@v.co for v in ob.data.vertices];keys=[]
 for f in range(26,int(act.frame_range[1])+1):
  scene.frame_set(f);mat=rig.pose.bones[name].matrix.copy();low=min((mat@v).z for v in local);mat.translation.z+=max(0,.008-low);keys.append((f,mat))
 for f,mat in keys:
  scene.frame_set(f);rig.pose.bones[name].matrix=mat;rig.pose.bones[name].keyframe_insert('location',frame=f)
 scene.frame_set(int(act.frame_range[1]));q=rig.pose.bones[name].rotation_quaternion.copy();loc=rig.pose.bones[name].location.copy();dead=bpy.data.actions['Dead'];rig.animation_data.action=dead;rig.animation_data.action_slot=dead.slots[0]
 for f in [0,30]:pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.location=loc;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
eq.update(axe_triangles=axe_tri,shield_triangles=shield_tri,shield_height_m=.767,review_round=2,rim_studs=len(studs),axe_tip_m=.47,shield_crown_m=.047,texture_source='references_hd/round2_equipment')
(P/'work/equipment.json').write_text(json.dumps(eq,indent=2)+'\n')
assert 1000<=axe_tri<=3000 and 1000<=shield_tri<=3000,(axe_tri,shield_tri)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_motion.blend'));print('REVIEW2_EQUIPMENT',eq)
