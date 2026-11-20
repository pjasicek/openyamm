import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];H=r.data.bones['mixamorig:RightHand'].matrix_local;orient=Matrix(((1,0,0),(0,0,1),(0,-1,0)));S=H@Matrix.Translation(Vector((.041,.100,0)))@orient.to_4x4();parts=[]
def mat(name,c,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;return m
steel=mat('Corsair - steel',(.33,.29,.245),.8,.32);edge=mat('Corsair - cutting edge',(.62,.60,.53),.85,.23);gold=mat('Corsair - aged gold',(.52,.28,.055),.75,.32);leather=mat('Corsair - dark leather',(.045,.016,.007),0,.74);ruby=mat('Corsair - red pommel inset',(.32,.008,.009),.28,.23)
def part(name,verts,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata([S@Vector(v) for v in verts],[],faces);me.update();o=bpy.data.objects.new(name,me);s.collection.objects.link(o);me.materials.append(material);g=o.vertex_groups.new(name='Weapon.R');g.add(list(range(len(me.vertices))),1,'REPLACE');o.parent=r;mod=o.modifiers.new('Rigid weapon attachment','ARMATURE');mod.object=r;o['goblin_weapon']=True;parts.append(o);return o
stations=[(.09,-.028,.029),(.16,-.027,.030),(.27,-.020,.036),(.34,-.016,.042),(.355,-.030,.046),(.40,-.022,.049),(.45,-.012,.057),(.465,-.025,.061),(.52,-.007,.077),(.565,.004,.095),(.58,-.008,.102),(.64,.025,.126),(.69,.063,.146),(.75,.110,.166),(.80,.157,.180),(.83,.187,.1875)];verts=[];faces=[]
for y,lo,hi in stations:
 for x,z in [(0,lo),(.0032,lo+(hi-lo)*.20),(.0032,hi-(hi-lo)*.12),(0,hi),(-.0032,hi-(hi-lo)*.12),(-.0032,lo+(hi-lo)*.20)]:verts.append((x,y,z))
for i in range(len(stations)-1):
 for j in range(6):faces.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
faces.extend([tuple(reversed(range(6))),tuple((len(stations)-1)*6+j for j in range(6))]);o=part('Corsair blade',verts,faces,steel);o.data.materials.append(edge)
for p in o.data.polygons:p.material_index=int(p.index%6 in [2,3])
def tube(name,pts,radius,material,sides=8):
 pts=[Vector(p) for p in pts];vs=[];fs=[]
 for i,p in enumerate(pts):
  axis=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();u=axis.cross(Vector((1,0,0)))
  if u.length<.01:u=axis.cross(Vector((0,0,1)))
  u.normalize();v=axis.cross(u)
  for j in range(sides):vs.append(p+radius*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*v))
 for i in range(len(pts)-1):
  for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 fs+=[tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))];o=part(name,vs,fs,material)
 for p in o.data.polygons:p.use_smooth=True
 return o
tube('Corsair grip',[(0,-.081,0),(0,.081,0)],.0205,leather,12)
tube('Corsair gold guard',[(0,.072,-.053),(0,.087,-.047),(0,.095,-.025),(0,.094,0),(0,.091,.030),(0,.080,.053),(0,.067,.054)],.006,gold)
tube('Corsair knuckle bow',[(0,-.090,0),(.009,-.084,.048),(.012,-.063,.069),(.012,.036,.070),(.007,.069,.058),(0,.084,.031)],.0048,gold)
tube('Corsair pommel',[(0,-.104,0),(0,-.086,0)],.025,gold,10)
tube('Corsair pommel red inset',[(0,-.107,0),(0,-.104,0)],.016,ruby,10)
tube('Corsair grip ferrule',[(0,.075,0),(0,.090,0)],.023,gold,10)
# Subtle wrap shading, no extra coil geometry.
n=leather.node_tree.nodes;l=leather.node_tree.links;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=95;tex.inputs['Detail'].default_value=1;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.001;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
# Node-only micrograin is optional authoring shading; flat leather remains the portable material.
report={'reference':'assets_dev/engine/icons/7item220.bmp (merged Corsair item 1305)','interpretation':'Corsair-inspired goblin sword; original goblin sprites govern proportion and gesture','sword_rest_transform':list(map(list,S)),'parts':[o.name for o in parts],'sword_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts),'handle_radius_m':.0205,'blade_length_m':.74};(OUT/'sword_build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
