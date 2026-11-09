import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v5h.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
def setact(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def reset():
 setact(None)
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()
# A guarded left arm supports the kite shield; retain a small amount of each clip's original arm motion.
setact(bpy.data.actions['Attack']);scene.frame_set(14)
guard={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']}
for act in list(bpy.data.actions):
 if act.name not in ['Standing','Walking','Running','Attack','Hit','Fidget']:continue
 setact(act);poses=[]
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f);poses.append({n:guard[n].slerp(rig.pose.bones[n].rotation_quaternion,.08 if act.name in ['Standing','Walking','Running'] else .2) for n in guard})
 for f,p in enumerate(poses):
  for n,q in p.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
reset()
def bone(name,parent,c,axis):
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new(name);b.head=c;b.tail=c+axis*.15;b.parent=rig.data.edit_bones[parent];bpy.ops.object.mode_set(mode='OBJECT')
def build(name,parent,c,axis):
 bone(name,parent,c,axis);bm=bmesh.new();cl=bm.faces.layers.int.new('prop_class');return bm,cl
colors=[(.16,.07,.025,1),(.52,.55,.60,1),(.83,.86,.89,1),(.55,.32,.07,1),(.07,.055,.045,1)]
def finish(name,bm):
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.parent=rig;m=o.modifiers.new('Armature','ARMATURE');m.object=rig;o.vertex_groups.new(name=name).add(list(range(len(me.vertices))),1,'REPLACE')
 me.uv_layers.new(name='UVMap')
 for i,col in enumerate(colors):
  mat=bpy.data.materials.get('Prop'+str(i)) or bpy.data.materials.new('Prop'+str(i));mat.diffuse_color=col;me.materials.append(mat)
 for f in me.polygons:f.material_index=me.attributes['prop_class'].data[f.index].value
 return o
def cone(bm,cl,a,b,r0,r1,kind,n=12):
 a,b=Vector(a),Vector(b);d=b-a;old=set(bm.faces);r=bmesh.ops.create_cone(bm,cap_ends=True,segments=n,radius1=r0,radius2=r1,depth=d.length);bmesh.ops.transform(bm,matrix=Matrix.Translation((a+b)*.5)@d.to_track_quat('Z','Y').to_matrix().to_4x4(),verts=r['verts'])
 for f in set(bm.faces)-old:f[cl]=kind
G=json.loads((P/'work/grip_pose.json').read_text());hm=rig.data.bones['B_R_Hand'].matrix_local;c=hm@Vector(G['handle_centre_hand_local']);ax=(hm.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
# Fix blade roll from the actual target-facing cut velocity in hand space.
setact(bpy.data.actions['Attack']);tips=[];mats=[]
for f in [22,23]:
 scene.frame_set(f);m=rig.pose.bones['B_R_Hand'].matrix@hm.inverted();mats.append(m.copy());tips.append(m@(c+ax*.43))
v=mats[0].to_3x3().inverted()@(tips[1]-tips[0]);side=(v-ax*v.dot(ax)).normalized();flat=ax.cross(side).normalized();reset()
bm,cl=build('Axe','B_R_Hand',c,ax)
cone(bm,cl,c-ax*.10,c+ax*.44,.0115,.009,0);cone(bm,cl,c-ax*.112,c-ax*.096,.014,.014,1);cone(bm,cl,c+ax*.30,c+ax*.43,.018,.016,1)
# Two crescent blades; forged central ridge and a thin continuous cutting edge.
for sign in [-1,1]:
 coords=[(.27,.018),(.235,.12),(.28,.16),(.35,.17),(.42,.145),(.47,.11),(.405,.018)]
 vs=[]
 for a,w in coords:vs.append(bm.verts.new(c+ax*a+side*w*sign))
 ridge1=bm.verts.new(c+ax*.35+side*.07*sign+flat*.008);ridge2=bm.verts.new(c+ax*.35+side*.07*sign-flat*.008)
 for i in range(len(vs)):
  j=(i+1)%len(vs)
  for ridge in [ridge1,ridge2]:f=bm.faces.new([vs[i],vs[j],ridge]);f[cl]=2 if 1<=i<=4 else 1
axe=finish('Axe',bm)
# Shield basis chosen in the standing guard, then mapped back to the immutable rest rig.
setact(bpy.data.actions['Standing']);scene.frame_set(0);lh=rig.pose.bones['B_L_Hand'].matrix.copy();L=json.loads((P/'work/grip_pose_left.json').read_text());centre=lh@Vector(L['handle_centre_hand_local']);back=lh.to_3x3()@Vector(L['handle_axis_hand_local']);rest=rig.data.bones['B_L_Hand'].matrix_local;D=rest@lh.inverted();c2=D@centre;right=D.to_3x3()@Vector((1,0,0));up=D.to_3x3()@Vector((0,0,1));normal=D.to_3x3()@Vector((0,-1,0));handle=(D.to_3x3()@back).normalized();reset()
bm,cl=build('Shield','B_L_Hand',c2,up)
cone(bm,cl,c2-handle*.075,c2+handle*.075,.011,.011,0)
# Bevelled steel kite rim and ochre panel, raised silver four-point reinforcement and brass boss.
center=c2+normal*.075+up*.05
outline=[(-.145,.34),(.145,.34),(.18,.02),(.10,-.35),(0,-.42),(-.10,-.35),(-.18,.02)]
rings=[]
for scale,depth in [(1,-.012),(1,0),(.91,.009)]:
 rings.append([bm.verts.new(center+right*x*scale+up*z*scale+normal*depth) for x,z in outline])
for r0,r1 in zip(rings[:-1],rings[1:]):
 for i in range(len(outline)):f=bm.faces.new([r0[i],r0[(i+1)%len(outline)],r1[(i+1)%len(outline)],r1[i]]);f[cl]=1
f=bm.faces.new(list(reversed(rings[0])));f[cl]=4
peak=bm.verts.new(center+normal*.037)
for i in range(len(outline)):f=bm.faces.new([rings[-1][i],rings[-1][(i+1)%len(outline)],peak]);f[cl]=3
star=[(0,.29),(.023,.025),(.14,0),(.023,-.025),(0,-.34),(-.023,-.025),(-.14,0),(-.023,.025)]
sv=[bm.verts.new(center+right*x+up*z+normal*(.041-.025*abs(z)/.34)) for x,z in star]
for i in range(len(sv)):f=bm.faces.new([sv[i],sv[(i+1)%len(sv)],bm.verts.new(center+normal*.043)]);f[cl]=2
cone(bm,cl,center+normal*.036,center+normal*.063,.04,.014,3,n=16)
shield=finish('Shield',bm)
# Both held props reset their transforms in all clips. Death remains held initially; clearance determines release.
for act in bpy.data.actions:
 if not act.use_fake_user:continue
 setact(act)
 for name in ['Axe','Shield']:
  b=rig.pose.bones[name];b.rotation_mode='QUATERNION'
  for f in [0,int(act.frame_range[1])]:b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped.blend'))
(P/'work/equipment.json').write_text(json.dumps({'axe_axis':list(ax),'axe_edge':list(side),'axe_centre':list(c),'axe_tip_m':.47,'shield_height_m':.76,'body_triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'axe_triangles':sum(len(p.vertices)-2 for p in axe.data.polygons),'shield_triangles':sum(len(p.vertices)-2 for p in shield.data.polygons)},indent=2))
