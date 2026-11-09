"""Concept revision: riveted core-window maul and articulated front/back hull apron."""
import bpy,bmesh,json,math,sys,os
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_concept_20261024/forge_complete.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene;r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
for o in list(bpy.data.objects):
 if o.name.startswith('Apron_') or o.name=='Thunder_Maul':bpy.data.objects.remove(o,do_unlink=True)
plate=bpy.data.materials['HKR_Plate'];dark=bpy.data.materials['Lancer_Resin'];glow=bpy.data.materials['HKR_Glow']
gold=bpy.data.materials.get('Forge_Brass') or bpy.data.materials.new('Forge_Brass');gold.use_nodes=True
bs=gold.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.40,.225,.065,1);bs.inputs['Metallic'].default_value=.8;bs.inputs['Roughness'].default_value=.38
bs=dark.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.018,.014,.013,1);bs.inputs['Metallic'].default_value=.7;bs.inputs['Roughness'].default_value=.62
bs=glow.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.14,.018,.002,1);bs.inputs['Emission Color'].default_value=(1,.16,.008,1);bs.inputs['Emission Strength'].default_value=1
glow['openyamm_bloom']=True
layout=json.loads((P/'work/armour_layout.json').read_text());rect=layout['plates']['back']['rect'];atlas=layout['atlas']
parts=[];chains=[]
def bone(n,parent,point):
 bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');eb=r.data.edit_bones;b=eb.get(n) or eb.new(n);b.head=point;b.tail=Vector(point)+Vector((0,0,-.10));b.parent=eb[parent];b.use_connect=False;bpy.ops.object.mode_set(mode='OBJECT')
def mesh(n,bn,boxes=(),tubes=(),transform=None):
 bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap')
 for c,size,mi,bevel in boxes:
  vv=bmesh.ops.create_cube(bm,size=1)['verts']
  for v in vv:v.co=Vector((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))+Vector(c)
  for f in {f for v in vv for f in v.link_faces}:f.material_index=mi
  if bevel:
   result=bmesh.ops.bevel(bm,geom=list({e for v in vv for e in v.link_edges}),offset=bevel,segments=1,affect='EDGES')
   for f in result['faces']:f.material_index=mi
 for a,b,rad,mi in tubes:
  axis=Vector(b)-Vector(a);rot=Vector((0,0,1)).rotation_difference(axis.normalized()).to_matrix();vv=bmesh.ops.create_cone(bm,cap_ends=True,segments=10,radius1=rad,radius2=rad,depth=axis.length)['verts']
  for v in vv:v.co=rot@v.co+(Vector(a)+Vector(b))/2
  for f in {f for v in vv for f in v.link_faces}:f.material_index=mi
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 for f in bm.faces:
  axis=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=axis];lo=[min(v.co[i] for v in f.verts) for i in axes];hi=[max(v.co[i] for v in f.verts) for i in axes]
  for loop in f.loops:
   u,v=[(loop.vert.co[i]-a)/max(b-a,1e-6) for i,a,b in zip(axes,lo,hi)];loop[uv].uv=((rect[0]+(0.01+.98*u)*rect[2])/atlas,1-(rect[1]+(0.01+.98*v)*rect[3])/atlas)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));me=bpy.data.meshes.new(n);bm.to_mesh(me);bm.free()
 if transform is not None:me.transform(transform)
 for m in (plate,dark,glow,gold):me.materials.append(m)
 o=bpy.data.objects.new(n,me);sc.collection.objects.link(o);o.parent=r;o.vertex_groups.new(name=bn).add(list(range(len(me.vertices))),1,'REPLACE');o.modifiers.new('Armature','ARMATURE').object=r;o['bone']=bn;o['lancer_atlas_rect']=rect;o['lancer_atlas_size']=atlas
 parts.append(o);return o
# The old grip coordinate frame stays exact; the core is recessed behind the outer frame.
M=r.data.bones['Thunder_Maul'].matrix_local
boxes=[((0,1.02,0),(.59,.32,.32),1,.025)]
for sign in (-1,1):
 for y in (.875,1.165):boxes.append(((sign*.285,y,0),(.12,.09,.40),0,.018))
 for z in (-.165,.165):boxes.append(((sign*.285,1.02,z),(.12,.20,.07),0,.012))
 boxes.append(((sign*.318,1.02,0),(.015,.11,.25),2,.005))
 for y in (.95,1.09):boxes.append(((sign*.34,y,0),(.012,.018,.28),3,.003))
# Two broad faces: a real open channel between ivory cheek plates, black frame and orange core.
for z in (-1,1):
 for x in (-.135,.135):boxes.append(((x,1.02,z*.185),(.17,.315,.052),0,.012))
 for y in (.85,1.19):boxes.append(((0,y,z*.185),(.48,.045,.05),1,.009))
 boxes.append(((0,1.02,z*.167),(.074,.22,.018),2,.007))
 for x in (-.052,.052):boxes.append(((x,1.02,z*.19),(.015,.25,.03),3,.003))
 for x in (-.228,.228):boxes.append(((x,1.02,z*.186),(.009,.25,.015),2,.002))
 for y in (.875,1.165):boxes.append(((0,y,z*.19),(.42,.009,.012),2,.002))
tubes=[((0,-.58,0),(0,.88,0),.023,1),((0,-.60,0),(0,-.53,0),.034,3),((0,.74,0),(0,.90,0),.05,1),((0,.785,0),(0,.81,0),.053,2)]
for y in (-.49,-.30,-.11,.08,.27,.46,.65):tubes.append(((0,y,0),(0,y+.023,0),.029,3))
for y in (-.44,-.39,-.25,-.20,-.06,-.01,.13,.18,.32,.37,.51,.56):tubes.append(((0,y,0),(0,y+.014,0),.0255,1))
mesh('Thunder_Maul','Thunder_Maul',boxes,tubes,M)
# Broad rigid plates on three-bone strips: gaps/straps carry the flex, ivory panels retain their shape.
for side,sgn,y in [('Front',-1,-.48),('Back',1,.065)]:
 pts=[Vector((0,y,z)) for z in (1.49,1.145,.91,.48)];names=[]
 for k in range(3):
  bn=f'B_ForgeApron_{side}_{k}';bone(bn,'B_Spine2' if k==0 else names[-1],pts[k]);names.append(bn)
  top,bot=pts[k].z-.015,pts[k+1].z+.018;wid=(.35,.34,.30)[k];c=(top+bot)/2
  if side=='Back' and k==1:wid=.34
  bb=[((0,y,c),(wid,.030,top-bot),0,.013),((0,y-sgn*.022,c),(wid+.025,.018,top-bot+.025),1,.012)]
  # Corner seams and two broad black straps, with brass buckle faces.
  for x in (-wid*.44,wid*.44):
   bb.append(((x,y+sgn*.018,c),( .006,.008,(top-bot)*.75),2,.001))
  for x in (-wid*.37,wid*.37):
   bb.append(((x,y-sgn*.025,c),(.032,.016,top-bot+.05),1,.003))
   bb.append(((x,y+sgn*.023,top-.025),(.035,.012,.025),3,.003))
  if side=='Back' and k==0:continue
  if side=='Back' and k==2:
   bb=bb[2:]
   for x in (-.10,.10):bb.extend([((x,y,c),(.10,.030,top-bot),0,.01),((x,y-sgn*.022,c),(.12,.018,top-bot+.025),1,.008)])
   bb.extend([((0,y,bot+.09),(.12,.030,.18),0,.01),((0,y-sgn*.022,bot+.09),(.13,.018,.20),1,.008)])
  o=mesh('Apron_'+side+str(k),bn,bb);o['cloth_chain']=side;o['chain_index']=k
 chains.append({'side':side,'sign':sgn,'bones':names,'points':[list(v) for v in pts]})
# Shoulder straps bridge the bib over the shoulder; existing harness remains underneath.
for side,sgn in [('L',1),('R',-1)]:
 mesh('Apron_Strap_'+side,'B_Spine2',boxes=[((sgn*.13,-.37,1.515),(.043,.24,.028),1,.008),((sgn*.13,-.478,1.485),(.058,.018,.05),3,.005)])
# Expand the solid forearm/shin shell and add a third substantial shoulder tier.
for side,sgn in [('L',1),('R',-1)]:
 for name,bn,grow in [('forearm',f'B_{side}_Forearm',.026),('shin',f'B_{side}_Calf',.025)]:
  ob=bpy.data.objects['Arm_'+name+'_'+side];bone0=r.data.bones[bn];axis=(bone0.tail_local-bone0.head_local).normalized()
  for v in ob.data.vertices:
   rel=v.co-bone0.head_local;rad=rel-axis*rel.dot(axis)
   if rad.length>.01:v.co+=rad.normalized()*grow
 # Shoulder lames follow the upper arm's measured surface instead of floating on the old cap helper.
 upper=r.data.bones[f'B_{side}_UpperArm'];end=r.data.bones[f'B_{side}_Forearm'].head_local;axis=(end-upper.head_local).normalized();length=(end-upper.head_local).length
 up=Vector((0,0,1));up=(up-axis*up.dot(axis)).normalized();across=axis.cross(up)
 for k,name in enumerate((f'Arm_pauldron_{side}',f'Arm_pauldron_lower_{side}',f'Apron_Shoulder_{side}')):
  if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
  nu,nv=9,4;V=[];F=[];U=[]
  for layer in (0,1):
   for j in range(nv):
    v=j/(nv-1);along=(-.04,.12,.28)[k]+v*(.25,.22,.20)[k];radius=(.175,.158,.143)[k]+.018*v+(.018 if layer==0 else 0)
    for i in range(nu):
     u=i/(nu-1);angle=math.radians(-100+200*u);d=up*math.cos(angle)+across*math.sin(angle)
     V.append(upper.head_local+axis*length*along+d*radius);U.append(((rect[0]+u*rect[2])/atlas,1-(rect[1]+v*rect[3])/atlas))
  G=nu*nv
  for layer in range(2):
   for j in range(nv-1):
    for i in range(nu-1):
     q=(layer*G+j*nu+i,layer*G+j*nu+i+1,layer*G+(j+1)*nu+i+1,layer*G+(j+1)*nu+i);F.append(q if layer==0 else q[::-1])
  border=list(range(nu))+[j*nu+nu-1 for j in range(1,nv)]+list(range(G-2,G-nu-1,-1))+[j*nu for j in range(nv-2,0,-1)]
  for a,b in zip(border,border[1:]+border[:1]):F.append((a,b,b+G,a+G))
  me=bpy.data.meshes.new(name);me.from_pydata(V,[],F);me.materials.append(plate);uv=me.uv_layers.new(name='UVMap')
  for po in me.polygons:
   for li in po.loop_indices:uv.data[li].uv=U[me.loops[li].vertex_index]
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
  ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob);ob.parent=r;bn=f'B_{side}_UpperArm';ob.vertex_groups.new(name=bn).add(list(range(len(V))),1,'REPLACE');ob.modifiers.new('Armature','ARMATURE').object=r;ob['bone']=bn
  parts.append(ob)
sc['forge_apron_chains']=json.dumps(chains)
# Start the armour review from the preserved clips. The attack receives a separate measured fitting pass.
sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_concept_parts.blend'))
(P/'review/forge_concept_geometry.json').write_text(json.dumps({'new_parts':{o.name:len(o.data.polygons) for o in parts},'apron_chains':chains,'source':'work/before_concept_20261024/forge_complete.blend'},indent=2)+'\n')
print('CONCEPT_PARTS_READY',flush=True);os._exit(0)
