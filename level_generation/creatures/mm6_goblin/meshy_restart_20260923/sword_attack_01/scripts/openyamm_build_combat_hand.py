import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];m=s.objects['Goblin_Combat_Body'];m.data=bpy.data.objects['Goblin_SkirtClearance_10577'].data.copy();H=r.data.bones['mixamorig:RightHand'].matrix_local.copy();inv=H.inverted()@m.matrix_world;back=inv.inverted();bm=bmesh.new();bm.from_mesh(m.data);bm.verts.ensure_lookup_table();count0=sum(len(f.verts)-2 for f in bm.faces)
region=[f for f in bm.faces if all((m.matrix_world@v.co).x<-.36 and (m.matrix_world@v.co).z<1.10 for v in f.verts)];edges=set(e for f in region for e in f.edges);verts=set(v for f in region for v in f.verts);plane=back@Vector((0,.045,0));normal=back.to_3x3()@Vector((0,1,0));bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+region,dist=.000001,plane_co=plane,plane_no=normal,clear_outer=True,clear_inner=False)
# Cut boundary is the original wrist surface, retained exactly.
bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if abs((inv@v.co).y-.045)<.00002 and (m.matrix_world@v.co).x<-.36],dist=.00001)
boundary=[v for v in bm.verts if abs((inv@v.co).y-.045)<.00002 and (m.matrix_world@v.co).x<-.36];boundary.sort(key=lambda v:math.atan2((inv@v.co).z,(inv@v.co).x));deform=bm.verts.layers.deform.verify();uv=bm.loops.layers.uv.verify();handgroup=m.vertex_groups['mixamorig:RightHand'].index
for v in boundary:v[deform].clear();v[deform][handgroup]=1
bone_specs=[];grip={};finger_info=[]
for index,(name,z,factor) in enumerate([('Index',-.043,.98),('Middle',-.012,1.03),('Ring',.019,.96),('Little',.046,.82)]):
 start=Vector((.006,.100,z));lengths=[.046*factor,.039*factor,.033*factor];joints=[start.copy()]
 for length in lengths:joints.append(joints[-1]+Vector((0,length,0)))
 R=.035;theta=0;angles=[]
 for L in lengths:angles.append(2*math.asin(L/(2*R)))
 for j in range(3):
  bn='Finger.R.'+name+'.'+str(j+1);bone_specs.append((bn,joints[j],joints[j+1],'mixamorig:RightHand' if j==0 else 'Finger.R.'+name+'.'+str(j)))
  grip[bn]=-(angles[0]/2 if j==0 else (angles[j-1]+angles[j])/2)
 finger_info.append({'name':name,'z':z,'start':list(start),'lengths':lengths,'radii':[.0115,.012,.0112,.0105,.0095,.0085,.0065],'bones':['Finger.R.'+name+'.'+str(j+1) for j in range(3)]})
# Thumb has its own opposed chain; its grip targets are set after inspecting the palm contact.
thumb=[Vector((0,.053,-.046)),Vector((0,.082,-.078)),Vector((0,.113,-.092)),Vector((0,.141,-.092))]
for j in range(3):bone_specs.append(('Finger.R.Thumb.'+str(j+1),thumb[j],thumb[j+1],'mixamorig:RightHand' if j==0 else 'Finger.R.Thumb.'+str(j)))
bpy.context.view_layer.objects.active=r;r.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for old in list(r.data.edit_bones):
 if old.name.startswith('Finger.R.') or old.name=='Weapon.R':r.data.edit_bones.remove(old)
for name,head,tail,parent in bone_specs:
 b=r.data.edit_bones.new(name);b.head=H@head;b.tail=H@tail;b.parent=r.data.edit_bones[parent];b.use_connect=False;b.align_roll(H.to_3x3()@Vector((1,0,0)))
b=r.data.edit_bones.new('Weapon.R');b.head=H@Vector((.041,.100,0));b.tail=H@Vector((.041,.100,-.15));b.parent=r.data.edit_bones['mixamorig:RightHand'];b.use_connect=False;b.align_roll(H.to_3x3()@Vector((1,0,0)))
bpy.ops.object.mode_set(mode='OBJECT')
for name,_,_,_ in bone_specs:
 if not m.vertex_groups.get(name):m.vertex_groups.new(name=name)
 r.pose.bones[name].rotation_mode='QUATERNION'
def vertex(co,weights):
 v=bm.verts.new(back@Vector(co))
 for name,w in weights.items():v[deform][m.vertex_groups[name].index]=w
 return v
def face(vs):
 try:
  f=bm.faces.new(vs);f.smooth=True
  for loop in f.loops:loop[uv].uv=(.25,.75)
  return f
 except ValueError:return None
# Loft from the existing wrist boundary. Cross-section follows the goblin's broad palm.
prev=boundary;n=len(prev)
for y,rx,rz,blend in [(.058,.030,.050,.25),(.075,.027,.057,.60),(.091,.024,.063,.90),(.106,.020,.060,1)]:
 ring=[]
 for v0 in boundary:
  p=inv@v0.co;t=math.atan2(p.z,p.x);q=p.lerp(Vector((-.004+rx*math.cos(t),y,rz*math.sin(t))),blend);q.y=y;ring.append(vertex(q,{'mixamorig:RightHand':1}))
 for j in range(n):face([prev[j],prev[(j+1)%n],ring[(j+1)%n],ring[j]])
 prev=ring
face(list(reversed(prev)))
def digit(name,points,radii,bones):
 # Three articulated segments, three rings per segment with blended joint influences.
 total=sum((points[i+1]-points[i]).length for i in range(3));lengths=[(points[i+1]-points[i]).length for i in range(3)];cum=[0,lengths[0],lengths[0]+lengths[1],total];rings=[];spec=[]
 for j in range(3):
  for t in [0,.38,.72]:spec.append((j,t))
 spec.extend([(2,1),(2,1.10)])
 for row,(j,t) in enumerate(spec):
  c=points[j].lerp(points[j+1],t);along=cum[j]+lengths[j]*t;u=Vector((1,0,0));axis=(points[j+1]-points[j]).normalized();v=axis.cross(u).normalized();rad=(.012*(1-.40*min(1,along/total)))
  if name=='Little':rad*=.80
  if name=='Thumb':rad*=1.14
  if t>1:rad=.0025
  weights={bones[j]:1}
  if j>0 and t==0:weights={bones[j-1]:.5,bones[j]:.5}
  elif j<2 and t==.72:weights={bones[j]:.8,bones[j+1]:.2}
  ring=[vertex(c+rad*(math.cos(k*math.tau/8)*u+math.sin(k*math.tau/8)*v),weights) for k in range(8)];rings.append(ring)
  if len(rings)>1:
   old=rings[-2]
   for k in range(8):face([old[k],old[(k+1)%8],ring[(k+1)%8],ring[k]])
 face(list(reversed(rings[0])));face(rings[-1])
for f in finger_info:
 pts=[Vector(f['start'])]
 for L in f['lengths']:pts.append(pts[-1]+Vector((0,L,0)))
 digit(f['name'],pts,f['radii'],f['bones'])
digit('Thumb',thumb,[],['Finger.R.Thumb.'+str(j+1) for j in range(3)])
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if all((m.matrix_world@v.co).x<-.36 and (m.matrix_world@v.co).z<1.10 for v in f.verts)]);bm.to_mesh(m.data);bm.free();m.data.update();r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
# Finger curl is around the hand's width axis; express each hinge in its own bind frame.
for name,angle in grip.items():
 pb=r.pose.bones[name];axis=pb.bone.matrix_local.to_quaternion().inverted()@(H.to_quaternion()@Vector((0,0,1)));pb.rotation_quaternion=Quaternion(axis,angle)
# A continuous opposed thumb frame with minimal twist follows three anatomical grip landmarks.
thumb_matrices=[]
thumb_targets=[Vector((0,.053,-.046)),Vector((.027,.079,-.071)),Vector((.054,.103,-.050)),Vector((.063,.111,-.022))]
for j in range(3):
 name='Finger.R.Thumb.'+str(j+1);pb=r.pose.bones[name];head=H@thumb_targets[j];tail=H@thumb_targets[j+1];bind=pb.bone.matrix_local;q=(pb.bone.tail_local-pb.bone.head_local).rotation_difference(tail-head)@bind.to_quaternion();desired=Matrix.Translation(head)@q.to_matrix().to_4x4();parent=r.pose.bones[pb.parent.name];parent_pose=H if j==0 else thumb_matrices[-1];pb.matrix_basis=bind.inverted()@parent.bone.matrix_local@parent_pose.inverted()@desired;thumb_matrices.append(desired);bpy.context.view_layer.update()
pose={name:{'rotation':list(r.pose.bones[name].rotation_quaternion),'location':list(r.pose.bones[name].location)} for name,_,_,_ in bone_specs};(OUT/'grip_pose.json').write_text(json.dumps(pose,indent=2));(OUT/'hand_build.json').write_text(json.dumps({'before_body_triangles':count0,'after_body_triangles':sum(len(p.vertices)-2 for p in m.data.polygons),'wrist_boundary_vertices':n,'finger_bones':15,'weapon_bone':'Weapon.R','grip_center_hand_local':[.041,.100,0],'handle_radius_m':.0205,'finger_specs':finger_info},indent=2));print('Rebuilt connected wrist/palm and articulated digits;',sum(len(p.vertices)-2 for p in m.data.polygons),'body triangles')
