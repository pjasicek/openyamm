"""Replace only carried geometry on the frozen final rig; retain all body animation and grips."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector, Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round1/before/work/final_motion.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
tiles=json.loads((P/'textures/figc_gear_tiles.json').read_text())
class Mesh:
 def __init__(self):self.v=[];self.f=[];self.uv=[]
 def vert(self,p):self.v.append(tuple(p));return len(self.v)-1
 def face(self,ids,tile,uv=None):
  self.f.append(ids);x0,y0,x1,y1=tiles[tile]
  if uv is None:uv=[(.5+.46*math.cos(i*2*math.pi/len(ids)),.5+.46*math.sin(i*2*math.pi/len(ids))) for i in range(len(ids))]
  self.uv.append([((x0+u*(x1-x0))/1024,1-(y1-v*(y1-y0))/1024) for u,v in uv])
 def save(self,name):
  me=bpy.data.meshes.new(name+'_review1');me.from_pydata(self.v,[],self.f);me.update();uv=me.uv_layers.new(name='UVMap')
  for poly,coords in zip(me.polygons,self.uv):
   for li,co in zip(poly.loop_indices,coords):uv.data[li].uv=co
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
  ob=bpy.data.objects[name];ob.data=me;ob.vertex_groups.clear();ob.vertex_groups.new(name=name).add(list(range(len(me.vertices))),1,'REPLACE')
  assert all(len(f.vertices)>=3 for f in me.polygons)
  me.calc_loop_triangles()
  for tri in me.loop_triangles:
   a,b,c=[uv.data[i].uv for i in tri.loops]
   assert abs((b-a).x*(c-a).y-(b-a).y*(c-a).x)>1e-10,(name,tri.polygon_index)
  return sum(len(f.vertices)-2 for f in me.polygons)
 def tube(self,a,b,radii,tile,n=10):
  a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.orthogonal().normalized();v=axis.cross(u).normalized();rings=[]
  for t,r in radii:
   rings.append([self.vert(a.lerp(b,t)+(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n))*r) for i in range(n)])
  for j in range(len(rings)-1):
   for i in range(n):
    k=(i+1)%n;self.face([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],tile,[(i/n,j/(len(rings)-1)),((i+1)/n,j/(len(rings)-1)),((i+1)/n,(j+1)/(len(rings)-1)),(i/n,(j+1)/(len(rings)-1))])
  self.face(rings[0][::-1],tile);self.face(rings[-1],tile)
eq=json.loads((P/'work/equipment.json').read_text());c=Vector(eq['axe_centre']);axis=Vector(eq['axe_axis']);edge=Vector(eq['axe_edge']);normal=axis.cross(edge).normalized()
M=Mesh()
M.tube(c-axis*.105,c+axis*.445,[(0,.0105),(.4,.0095),(1,.012)],'wood',12)
# Real socket and ferrules have bevelled ends; the sharpened crescent bits meet this socket.
for a,b,r,tile in [(.273,.425,.022,'steel'),(-.111,-.091,.014,'dark'),(.113,.13,.012,'dark')]:
 M.tube(c+axis*a,c+axis*b,[(0,r*.83),(.12,r),(.88,r),(1,r*.83)],tile,12)
# Open helical leather strip: geometry carries the wrap silhouette without hidden inner faces.
turns=9;steps=turns*10;ra=[];rb=[]
for i in range(steps+1):
 theta=i/10*2*math.pi;offset=-.083+i/steps*.19;radial=(edge*math.cos(theta)+normal*math.sin(theta))*.0115
 ra.append(M.vert(c+axis*offset+radial));rb.append(M.vert(c+axis*(offset+.015)+radial))
for i in range(steps):M.face([ra[i],ra[i+1],rb[i+1],rb[i]],'leather',[(i/10%1,.05),((i+1)/10%1 or 1,.05),((i+1)/10%1 or 1,.85),(i/10%1,.85)])
# Concave beard, curved cutting bit, thickness and a separate continuous sharpened bevel.
outline=[(.287,.018),(.266,.061),(.245,.103),(.231,.134),(.270,.162),(.313,.180),(.359,.186),(.403,.180),(.447,.160),(.471,.134),(.435,.099),(.414,.057),(.408,.018)]
for sign in [-1,1]:
 outer=[];inner=[]
 for face_sign in [-1,1]:
  outer.append([M.vert(c+axis*a+edge*w*sign+normal*.0008*face_sign) for a,w in outline])
  inner.append([M.vert(c+axis*(a*.89+.35*.11)+edge*(w*.78+.04*.22)*sign+normal*.008*face_sign) for a,w in outline])
 uv=[((a-.22)/.27,w/.20) for a,w in outline]
 inneruv=[((a*.89+.35*.11-.22)/.27,(w*.78+.04*.22)/.20) for a,w in outline]
 for side in [0,1]:
  # A gently domed main bit replaces the old sharp pyramid faces.
  hub=M.vert(c+axis*.352+edge*.070*sign+normal*.0095*(-1 if side==0 else 1))
  for i in range(len(outline)):
   j=(i+1)%len(outline)
   M.face([inner[side][i],inner[side][j],hub],'steel',[inneruv[i],inneruv[j],(.49,.35)])
   M.face([outer[side][i],outer[side][j],inner[side][j],inner[side][i]],'edge' if 3<=i<=8 else 'steel',[uv[i],uv[j],inneruv[j],inneruv[i]])
 for i in range(len(outline)):
  j=(i+1)%len(outline);M.face([outer[0][i],outer[0][j],outer[1][j],outer[1][i]],'edge',[(i/len(outline),0),((i+1)/len(outline),0),((i+1)/len(outline),1),(i/len(outline),1)])
axe_tri=M.save('Axe')
# Recover the original rest-space shield axes from its standing hand pose; its socket remains unchanged.
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
lh=rig.pose.bones['B_L_Hand'].matrix.copy();grip=json.loads((P/'work/grip_pose_left.json').read_text());centre=lh@Vector(grip['handle_centre_hand_local']);handle_world=lh.to_3x3()@Vector(grip['handle_axis_hand_local']);D=rig.data.bones['B_L_Hand'].matrix_local@lh.inverted()
c2=D@centre;right=(D.to_3x3()@Vector((1,0,0))).normalized();up=(D.to_3x3()@Vector((0,0,1))).normalized();out=(D.to_3x3()@Vector((0,-1,0))).normalized();handle=(D.to_3x3()@handle_world).normalized();center=c2+out*.075+up*.05
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
M=Mesh();M.tube(c2-handle*.075,c2+handle*.075,[(0,.011),(1,.011)],'leather',10)
def point(x,z,d):return center+right*x+up*z+out*d
outline=[(-.113,.370),(.113,.370),(.183,.175),(.133,-.346),(.105,-.397),(-.105,-.397),(-.133,-.346),(-.183,.175)]
rings=[]
for scale,depth in [(1,-.012),(1,.006),(.968,.014),(.875,.014),(.875,.003)]:
 rings.append([M.vert(point(x*scale,z*scale,depth)) for x,z in outline])
for k in range(len(rings)-1):
 for i in range(8):
  j=(i+1)%8;M.face([rings[k][i],rings[k][j],rings[k+1][j],rings[k+1][i]],'edge' if k==1 else 'steel')
M.face(rings[0][::-1],'back')
# Front crown carries the full projection-mapped native panel design.
front=[M.vert(point(x*.875,z*.875,.003)) for x,z in outline];peak=M.vert(point(0,0,.031))
uv=[((x*.875+.20)/.40,(z*.875+.42)/.82) for x,z in outline]
for i in range(8):j=(i+1)%8;M.face([front[i],front[j],peak],'shield',[uv[i],uv[j],(.5,.42/.82)])
# Raised, blackened four-point star, with narrow exposed steel bevels.
star=[(0,.298),(.030,.043),(.144,0),(.030,-.04),(0,-.318),(-.03,-.04),(-.144,0),(-.03,.043)]
def crown(x,z):return .031-.027*max(abs(x)/.17,abs(z)/.36)
st0=[M.vert(point(x,z,crown(x,z)+.004)) for x,z in star]
st1=[M.vert(point(x*.94,z*.94,crown(x*.94,z*.94)+.007)) for x,z in star]
hub=M.vert(point(0,0,.043))
for i in range(8):
 j=(i+1)%8;M.face([st0[i],st0[j],st1[j],st1[i]],'steel');M.face([st1[i],st1[j],hub],'dark')
# Elliptical bronze boss and a dark recessed collar, no dense sphere behind the shield.
prev=None
for rx,rz,d,tile in [(.027,.053,.042,'dark'),(.027,.053,.047,'dark'),(.020,.043,.054,'brass'),(.012,.028,.068,'brass')]:
 ring=[M.vert(point(rx*math.cos(i*2*math.pi/12),rz*math.sin(i*2*math.pi/12),d)) for i in range(12)]
 if prev:
  for i in range(12):j=(i+1)%12;M.face([prev[i],prev[j],ring[j],ring[i]],tile)
 prev=ring
M.face(prev,'brass')
# 22 visible low-sided rivet caps; the small stems and buried rear caps are omitted.
studs=[]
for i,(x,z) in enumerate(outline):
 xx,zz=outline[(i+1)%8];length=math.hypot(xx-x,zz-z);count=max(1,round(length/.09))
 for j in range(count):
  t=(j+.5)/count;studs.append(((x+(xx-x)*t)*.926,(z+(zz-z)*t)*.926))
for x,z in studs:
 ring=[M.vert(point(x+.005*math.cos(i*math.pi/3),z+.005*math.sin(i*math.pi/3),.015)) for i in range(6)];tip=M.vert(point(x,z,.018))
 for i in range(6):M.face([ring[i],ring[(i+1)%6],tip],'dark')
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
eq.update(axe_triangles=axe_tri,shield_triangles=shield_tri,shield_height_m=.767,review_round=1,rim_studs=len(studs));(P/'work/equipment.json').write_text(json.dumps(eq,indent=2)+'\n')
assert axe_tri<800 and shield_tri<650,(axe_tri,shield_tri)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_motion.blend'));print('REVIEW1_EQUIPMENT',eq)
