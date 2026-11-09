"""Native spear and buckler, modelled from the selected generated prop designs."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
def mesh(name,v,f):
 d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return o
def cyl(name,r,depth,z,segments=20):
 bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=depth,location=(0,0,z));o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);return o
def tube(name,points,r,sides=6):
 v=[];f=[]
 for i,p in enumerate(points):
  d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);q=d.to_track_quat('Z','Y')
  for k in range(sides):v.append(Vector(p)+q@Vector((r*math.cos(k*2*math.pi/sides),r*math.sin(k*2*math.pi/sides),0)))
 for i in range(len(points)-1):
  for k in range(sides):a=i*sides+k;b=i*sides+(k+1)%sides;f.append((a,b,b+sides,a+sides))
 return mesh(name,v,f)
def finish(name,parts):
 for o in bpy.data.objects:o.select_set(o in parts)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.2,island_margin=.01);bpy.ops.uv.pack_islands(margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8;o.data.materials.append(mat)
 bpy.ops.export_scene.gltf(filepath=str(P/f'work/{name.lower()}_upload.glb'),use_selection=True,export_animations=False,export_skins=False,export_attributes=False)
 return o
# Spear lies on +Z, with a human-sized grip at the origin and forward point at +1.04 m.
parts=[cyl('Wooden shaft',.012,1.70,-.04,24)]
# Hollow socket collar and narrow leaf blade with an actual diamond cross-section and edge bevel.
parts.append(cyl('Steel socket',.014,.12,.81,20))
v=[];f=[];rings=[(.85,.007,.005),(.875,.030,.009),(.92,.028,.008),(1.015,.010,.004),(1.08,.0004,.0004)]
for z,w,t in rings:
 for x,y in [(-w,0),(-w*.78,-t*.35),(0,-t),(w*.78,-t*.35),(w,0),(w*.78,t*.35),(0,t),(-w*.78,t*.35)]:v.append((x,y,z))
for j in range(len(rings)-1):
 for k in range(8):a=j*8+k;b=j*8+(k+1)%8;f.append((a,b,b+8,a+8))
f.extend([tuple(reversed(range(8))),tuple(range(32,40))]);parts.append(mesh('Bevelled spear blade',v,f))
for c,h,r in [(-.025,.19,.014),(.35,.045,.0135),(.775,.065,.015),(-.865,.036,.0135)]:
 parts.append(cyl('Binding base',r,h,c,20));turns=round(h/.01);pts=[]
 for i in range(turns*7+1):
  t=i/(turns*7);a=t*turns*2*math.pi;pts.append((r*math.cos(a),r*math.sin(a),c-h/2+t*h))
 parts.append(tube('Raised wrap seam',pts,.0017,4))
for side in [-1,1]:
 pts=[(.013,side*.004,.75),(.025,side*.018,.65),(.034,side*.026,.58)];parts.append(tube('Tassel cord',pts,.002,6))
 a=Vector(pts[-1]);v=[a+Vector((x,y,z))for x,y,z in [(0,0,0),(-.010,0,-.045),(0,-.003,-.14),(.012,0,-.052),(0,.003,-.05)]];parts.append(mesh('Narrow black feather tassel',v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)]))
spear=finish('Spear',parts);spear.hide_set(True);spear.hide_render=True
# Buckler exterior faces -Y, vertical long axis Z.
v=[];f=[];N=48;R=6
for back in [False,True]:
 for j in range(R+1):
  r=max(.001,j/R)
  for k in range(N):
   a=k*2*math.pi/N;x=.18*r*math.cos(a);z=.235*r*math.sin(a);y=-.052*(1-r*r)+(0.012 if back else 0);v.append((x,y,z))
 for j in range(R):
  for k in range(N):
   a=(int(back)*(R+1)+j)*N+k;b=(int(back)*(R+1)+j)*N+(k+1)%N;f.append((a,b,b+N,a+N) if not back else (a,a+N,b+N,b))
parts=[mesh('Domed hide and wood shell',v,f)]
pts=[(.18*math.cos(k*2*math.pi/N),.004,.235*math.sin(k*2*math.pi/N))for k in range(N+1)];parts.append(tube('Bound leather rim',pts,.009,6))
for z in [-.09,.09]:
 # Broad arched straps leave room for the forearm; no boss or invented emblem.
 vv=[];ff=[]
 for j in range(9):
  x=-.13+j*.26/8;y=.020+.055*math.sin(math.pi*j/8)
  for dz,dy in [(-.026,0),(.026,0),(.026,.005),(-.026,.005)]:vv.append((x,y+dy,z+dz))
 for j in range(8):
  for k in range(4):a=j*4+k;b=j*4+(k+1)%4;ff.append((a,b,b+4,a+4))
 parts.append(mesh('Forearm leather strap',vv,ff))
buckler=finish('Buckler',parts);spear.hide_set(False);spear.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/props_untextured.blend'))
report={o.name:{'triangles':len(o.data.polygons),'dimensions_m':list(o.dimensions)}for o in [spear,buckler]};(P/'work/props_geometry.json').write_text(json.dumps(report,indent=2));assert report['Spear']['triangles']<3500 and report['Buckler']['triangles']<3500
print(report,flush=True)
