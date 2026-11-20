"""Native kni scimitar: curved cutting edge, three root notches, long warm grip and steel pommel."""
import bpy,bmesh,math,json
import numpy as np
from mathutils import Vector,Quaternion
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def build(rig):
 scene=bpy.context.scene;G=json.loads((P/'work/grip_pose.json').read_text());Hm=rig.data.bones['B_R_Hand'].matrix_local
 c=Hm@Vector(G['handle_centre_hand_local']);ax=(Hm.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
 base=(rig.data.bones['B_R_Finger2'].head_local-c);base=(base-ax*base.dot(ax)).normalized()
 # Fit the cutting direction to the real slash, evaluated in the hand's frame.
 ac=bpy.data.actions['Attack'];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows=[];prev=None
 for f in np.arange(0,float(ac.frame_range[1])+.01,.5):
  scene.frame_set(int(f),subframe=float(f-int(f)));M=rig.pose.bones['B_R_Hand'].matrix@Hm.inverted();tip=M@(c+ax*.85)
  axis=(M.to_3x3()@ax).normalized()
  if prev is not None and axis.dot(Vector((0,-1,0)))>.5:
   vel=tip-prev;rows.append((vel.length,f,M.to_3x3().inverted()@vel))
  prev=tip
 assert rows;peak=max(rows,key=lambda r:r[0]);v=peak[2];side=(v-ax*v.dot(ax)).normalized();flat=ax.cross(side).normalized()
 if (P/'work/weapon_roll.json').exists():
  delta=json.loads((P/'work/weapon_roll.json').read_text())['selected']['roll_delta_deg'];side=Quaternion(ax,math.radians(delta))@side;flat=ax.cross(side).normalized()
 roll=math.degrees(math.atan2(base.cross(side).dot(ax),base.dot(side)))
 (P/'work/weapon_fit.json').write_text(json.dumps({'roll_from_knuckle_deg':roll,'initial_blow_s':(peak[1]-.25)/30,'cut_direction_rest':list(side),'axis_rest':list(ax),'centre_rest':list(c)},indent=2))
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 eb=rig.data.edit_bones.new('Sword');eb.head=c;eb.tail=c+ax*.15;eb.parent=rig.data.edit_bones['B_R_Hand'];eb.align_roll(flat)
 eb=rig.data.edit_bones.new('SwordTip');eb.head=c+ax*.85-side*.18;eb.tail=eb.head+ax*.04;eb.parent=rig.data.edit_bones['Sword']
 bpy.ops.object.mode_set(mode='OBJECT');verts=[];faces=[];classes=[]
 def p(a,s,f):return tuple(c+ax*a+side*s+flat*f)
 def add(v):k=len(verts);verts.extend(v);return k
 def face(v,cl):faces.append(v);classes.append(cl)
 def tube(a,r,cl,n=12):
  ks=[add([p(t,rr*math.cos(2*math.pi*j/n),rr*math.sin(2*math.pi*j/n)) for j in range(n)]) for t,rr in zip(a,r)]
  for k,l in zip(ks[:-1],ks[1:]):
   for j in range(n):face((k+j,l+j,l+(j+1)%n,k+(j+1)%n),cl)
  face(tuple(ks[0]+j for j in reversed(range(n))),cl);face(tuple(ks[-1]+j for j in range(n)),cl)
 tube([-.20,-.16,-.04,.08,.12],[.013,.014,.014,.014,.014],'grip')
 tube([-.23,-.216,-.195],[.012,.023,.014],'pommel')
 tube([.115,.125,.135],[.018,.023,.018],'guard')
 # The blade bends away from the convex cutting edge, as in native kniatka0.
 rings=[]
 for t in [0,.035,.05,.075,.09,.115,.13,.17,.25,.35,.48,.62,.78,.9]:
  a=.135+.715*t;curve=-.18*t*t;back=-.04-(.027 if t in [.035,.075,.115] else 0);edge=.055
  if t>.78:edge*=max(.1,(1-t)/.22)
  rings.append(add([p(a,curve+edge,0),p(a,curve+.008,.005),p(a,curve+back,.0015),p(a,curve+back,-.0015),p(a,curve+.008,-.005)]))
 for k,l in zip(rings[:-1],rings[1:]):
  for j in range(5):face((k+j,l+j,l+(j+1)%5,k+(j+1)%5),'edge' if j in (0,4) else 'blade')
 tip=add([p(.85,-.18,0)])
 for j in range(5):face((rings[-1]+j,tip,rings[-1]+(j+1)%5),'edge' if j in (0,4) else 'blade')
 face(tuple(rings[0]+j for j in reversed(range(5))),'blade')
 me=bpy.data.meshes.new('KnightSword');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('Weapon',me);scene.collection.objects.link(ob)
 colors={'grip':(.2,.1,.045,1),'pommel':(.19,.21,.28,1),'guard':(.10,.12,.16,1),'blade':(.22,.24,.28,1),'edge':(.56,.59,.65,1)}
 for n,col in colors.items():m=bpy.data.materials.new(n);m.diffuse_color=col;me.materials.append(m)
 for poly,cl in zip(me.polygons,classes):poly.material_index=list(colors).index(cl);poly.use_smooth=cl in ['grip','pommel']
 vg=ob.vertex_groups.new(name='Sword');vg.add(list(range(len(verts))),1,'REPLACE');ob.parent=rig;md=ob.modifiers.new('Rig','ARMATURE');md.object=rig
 attr=me.attributes.new('piece','INT','POINT');attr.data.foreach_set('value',[100]*len(verts))
 print('NATIVE SWORD',len(verts),'vertices',sum(len(f)-2 for f in faces),'triangles','roll',round(roll,1),'source impact',peak[1]/30)
 return ob
