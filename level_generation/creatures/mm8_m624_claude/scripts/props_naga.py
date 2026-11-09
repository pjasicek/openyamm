import bpy,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/grip_v1.blend'));rig=bpy.data.objects['Rig']
mat=bpy.data.materials.new('NagaWeapons');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.38;bs.inputs['Metallic'].default_value=0
image=bpy.data.images.new('NagaWeaponColors',width=128,height=128);pixels=[]
for y in range(128):
 for x in range(128):
  q=x//32;color=[(.64,.69,.73),(.64,.41,.12),(.14,.085,.04),(.25,.28,.30)][q];grain=1+.04*math.sin(x*3.7+y*.7) if q!=2 else 1+.16*math.cos(y*1.7)
  pixels.extend([min(1,c*grain)for c in color]+[1])
image.pixels=pixels;image.filepath_raw=str(P/'textures/weapon_basecolor.png');image.file_format='PNG';image.save();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
report=[]
for sd in ['L1','L2','L3','R1','R2','R3']:
 verts=[];faces=[];classes=[]
 def ringmesh(rings,label):
  offset=len(verts);num=len(rings[0]);verts.extend([v for ring in rings for v in ring])
  for i in range(len(rings)-1):
   for j in range(num):faces.append((offset+i*num+j,offset+i*num+(j+1)%num,offset+(i+1)*num+(j+1)%num,offset+(i+1)*num+j));classes.append(label)
  faces.append(tuple(offset+j for j in reversed(range(num))));classes.append(label);faces.append(tuple(offset+(len(rings)-1)*num+j for j in range(num)));classes.append(label)
 def cylinder(a,b,r,label,n=8):
  a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1))).normalized();v=d.cross(u)
  ringmesh([[tuple(p+r*(math.cos(k*2*math.pi/n)*u+math.sin(k*2*math.pi/n)*v))for k in range(n)]for p in [a,b]],label)
 cylinder((0,-.085,0),(0,.085,0),.017,2)
 cylinder((0,-.105,0),(0,-.082,0),.029,1)
 # Swept guards preserve each native sword's distinctive outline.
 guard=[(-.105,.13,0),(-.075,.092,0),(0,.088,0),(.075,.092,0),(.105,.13,0)]
 if sd in ['L1','R1']:guard=[(-.075,.115,0),(0,.09,0),(.075,.115,0)]
 for a,b in zip(guard[:-1],guard[1:]):cylinder(a,b,.012,1)
 curve={'L1':0,'L2':.18,'L3':0,'R1':0,'R2':0,'R3':.12}[sd];width={'L1':.022,'L2':.042,'L3':.042,'R1':.023,'R2':.035,'R3':.025}[sd];length={'L1':.94,'L2':.75,'L3':.85,'R1':.90,'R2':.82,'R3':.8}[sd];rings=[]
 for i in range(25 if sd=='R1'else 13):
  t=i/(24 if sd=='R1'else 12);cx=curve*t*t+(.011*math.sin(t*math.pi*16)*(1-t*.5)if sd=='R1'else 0);y=.125+length*t;w=width*(1-.45*t)*max(.012,min(1,(1-t)*8));th=.0045*(1-.7*t)
  rings.append([(cx-w,y,0),(cx-w*.6,y,-th),(cx+w*.6,y,-th),(cx+w,y,0),(cx+w*.6,y,th),(cx-w*.6,y,th)])
 ringmesh(rings,0)
 me=bpy.data.meshes.new(sd+'_Weapon');me.from_pydata(verts,[],faces);me.materials.append(mat);me.update();uv=me.uv_layers.new(name='UVMap')
 for f,label in zip(me.polygons,classes):
  for loop in f.loop_indices:uv.data[loop].uv=((label+.5)/4,.5)
 o=bpy.data.objects.new(sd+'_Weapon',me);bpy.context.collection.objects.link(o);me.transform(rig.data.bones[sd+'_Sword'].matrix_local);group=o.vertex_groups.new(name=sd+'_Sword');group.add(list(range(len(verts))),1.,'REPLACE');mod=o.modifiers.new('RigidSword','ARMATURE');mod.object=rig;o.parent=rig;rig.data.bones[sd+'_Sword'].use_deform=True;me.calc_loop_triangles();report.append({'hand':sd,'triangles':len(me.loop_triangles),'profile':{'L1':'rapier','L2':'scimitar','L3':'broadsword','R1':'flamberge','R2':'straight sword','R3':'sabre'}[sd]})
(P/'work/weapons.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/armed_rig.blend'));print(report)
