"""Component-built weapons: diamond blades, tapered axe cheeks, sockets and round hafts.
Blender --background --python build_weapons.py -- <icon> ...
"""
import json,math,sys
from pathlib import Path
import bmesh,bpy
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rest_pose import rest_weapon
P=Path(__file__).resolve().parents[1]
DESIGNS=json.loads((P/'designs.json').read_text())
CELLS={'steel':0,'worn':1,'iron':2,'brass':3,'ash':4,'walnut':5,'brown':6,'ochre':7,
       'red':8,'black':9,'ivory':10,'crystal':11,'violet':12,'filigree':13,'redgold':14,'silverwork':15}
COLOURS=[(.72,.75,.78),(.61,.64,.67),(.26,.28,.3),(.8,.6,.25),(.57,.37,.15),(.32,.16,.08),
         (.36,.19,.09),(.59,.35,.12),(.53,.075,.045),(.13,.12,.11),(.8,.75,.6),(.6,.75,.84),
         (.47,.43,.6),(.8,.6,.25),(.7,.19,.09),(.73,.75,.78)]
MAT=None


def material():
 global MAT
 MAT=bpy.data.materials.new('weapon_material_atlas');MAT.use_nodes=True
 nt=MAT.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.42
 files=[P/'textures'/f'materials_{kind}.png' for kind in ['basecolor','mr','normal']]
 if all(f.exists() for f in files):
  nodes=[]
  for f in files:
   node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(f));nodes.append(node)
  nodes[1].image.colorspace_settings.name=nodes[2].image.colorspace_settings.name='Non-Color'
  nt.links.new(nodes[0].outputs['Color'],bs.inputs['Base Color'])
  sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(nodes[1].outputs['Color'],sep.inputs['Color'])
  nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
  normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nodes[2].outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 else:
  bs.inputs['Base Color'].default_value=(.55,.57,.6,1);bs.inputs['Metallic'].default_value=1


def mesh(name,verts,faces,cell,uvs=None,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 mat=MAT
 if cell=='stone':
  mat=bpy.data.materials.get('carved stone')
  if mat is None:
   mat=bpy.data.materials.new('carved stone');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.28,.21,.12,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.83
   file=P/'textures/stone_basecolor.png'
   if file.exists():
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(file));nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 me.materials.append(mat)
 uv=me.uv_layers.new();c=CELLS.get(cell,0);cx=c%4;cy=3-c//4
 for face in me.polygons:
  face.use_smooth=smooth
  axes=sorted(range(3),key=lambda a:abs(face.normal[a]))[:2]
  if abs(face.normal.z)>.5:axes=[0,1]
  for n,loop in enumerate(face.loop_indices):
   point=me.vertices[me.loops[loop].vertex_index].co
   a,b=uvs[face.index][n] if uvs else (point[axes[0]]+.5,point[axes[1]]+.5)
   assert -.01<=a<=1.01 and -.01<=b<=1.01,(name,a,b)
   if not uvs and face.normal.x>0:b=1-b
   uv.data[loop].uv=(a,b) if cell=='stone' else ((cx+.012+.976*a)/4,(cy+.012+.976*b)/4)
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);return ob


def tube(name,path,radius,cell,sides=10):
 path=[Vector(p) for p in path];radii=radius if isinstance(radius,list) else [radius]*len(path)
 verts=[];distance=[0]
 for a,b in zip(path,path[1:]):distance.append(distance[-1]+(b-a).length)
 for n,p in enumerate(path):
  tangent=(path[min(n+1,len(path)-1)]-path[max(n-1,0)]).normalized();u=tangent.cross(Vector((0,0,1)))
  if u.length<.01:u=tangent.cross(Vector((0,1,0)))
  u.normalize();v=tangent.cross(u).normalized()
  verts.extend(tuple(p+radii[n]*(math.cos(math.tau*j/sides)*u+math.sin(math.tau*j/sides)*v)) for j in range(sides))
 faces=[];uvs=[]
 for n in range(len(path)-1):
  v0=distance[n]%.9+.02;v1=v0+distance[n+1]-distance[n]
  if v1>.99:v0=.02;v1=.02+min(distance[n+1]-distance[n],.97)
  circumference=math.tau*max(radii[n],radii[n+1])
  for j in range(sides):
   k=(j+1)%sides;faces.append((n*sides+j,n*sides+k,(n+1)*sides+k,(n+1)*sides+j))
   uvs.append(((j/sides*circumference+.3,v0),((j+1)/sides*circumference+.3,v0),((j+1)/sides*circumference+.3,v1),(j/sides*circumference+.3,v1)))
 for n in [0,len(path)-1]:
  ids=list(range(n*sides,(n+1)*sides))
  while len(ids)>2:
   tri=(ids.pop(0),ids[0],ids[-1]);tri=tri if n else tri[::-1];faces.append(tri);uvs.append(tuple((.3+radii[n]*math.cos(math.tau*(v%sides)/sides),.3+radii[n]*math.sin(math.tau*(v%sides)/sides)) for v in tri))
   if len(ids)>2:
    tri=(ids.pop(),ids[0],ids[-1]);tri=tri if n else tri[::-1];faces.append(tri);uvs.append(tuple((.3+radii[n]*math.cos(math.tau*(v%sides)/sides),.3+radii[n]*math.sin(math.tau*(v%sides)/sides)) for v in tri))
 ob=mesh(name,verts,faces,cell,uvs,True)
 for face in list(ob.data.polygons)[-2*(sides-2):]:face.use_smooth=False
 return ob


def rod(name,y0,y1,radius,cell,sides=12):
 return tube(name,[(0,y0,0),(0,y1,0)],radius,cell,sides)


def collar(y,radius,width,cell='brass'):
 return rod('metal ferrule',y-width/2,y+width/2,[radius*.92,radius],cell)


def jewel(x,y,radius,colour='red'):
 colours={'red':(.65,.025,.015,1),'green':(.04,.5,.12,1),'blue':(.04,.3,.65,1),'black':(.08,.07,.065,1),'white':(.7,.75,.8,1)}
 mat=bpy.data.materials.get('jewel_'+colour)
 if mat is None:
  mat=bpy.data.materials.new('jewel_'+colour);mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=colours[colour];bs.inputs['Roughness'].default_value=.22
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=radius,location=(x,y,.03));ob=bpy.context.object;ob.name='faceted inset jewel';ob.scale.z=.55;ob.data.materials.append(mat)
 # A separate opaque material preserves the dielectric jewel.
 uv=ob.data.uv_layers.new()
 for loop in uv.data:loop.uv=(.5,.5)
 return ob


def blade(rows,cell='steel',thickness=.012,name='diamond blade'):
 # Cross-section has a real central ridge, two finite cutting edges and a complete back.
 verts=[];faces=[]
 for y,left,right in rows:
  mid=(left+right)/2;half=max((right-left)/2,.0007);depth=min(thickness,half*.36)
  verts.extend([(left,y,.0006),(mid,y,depth),(right,y,.0006),(right,y,-.0006),(mid,y,-depth),(left,y,-.0006)])
 for n in range(len(rows)-1):
  for j in range(6):faces.append((n*6+j,n*6+(j+1)%6,(n+1)*6+(j+1)%6,(n+1)*6+j))
 for n in [0,len(rows)-1]:
  for j in range(1,5):faces.append((n*6,n*6+j,n*6+j+1))
 return mesh(name,verts,faces,cell)


def dagger(d):
 guard=.5-d['guard'];bottom=-.47;g=guard
 blade([(g+( .49-g)*t,c-w,c+w) for t,w,c in d['blade']],d.get('blade_cell','steel'),d.get('blade_depth',.012))
 radius=d.get('grip_radius',.021)
 rod('oval leather grip',bottom+.025,g-.015,radius,d.get('grip_cell','brown'),12)
 # Separate tang bands and end furniture, with round depth rather than an extruded image outline.
 for y in [bottom+.018,g-.02]:collar(y,radius*1.2,.014,d.get('furniture','brass'))
 if d.get('wrap',True):
  turns=d.get('turns',7);y0=bottom+.035;y1=g-.033
  for n in range(turns):
   y=y0+(y1-y0)*n/turns
   path=[]
   for j in range(13):
    a=math.tau*j/12;path.append((radius*1.04*math.cos(a),y+(y1-y0)/turns*j/12,radius*1.04*math.sin(a)))
   tube('spiral grip binding',path,.0026,d.get('wrap_cell',d.get('grip_cell','brown')),5)
 w=d['guard_width'];s=d.get('guard_shape','up')
 if s=='straight':path=[(-w,g,0),(0,g,0),(w,g,0)]
 elif s=='down':path=[(-w,g-.018,0),(-w*.6,g+.01,0),(0,g+.018,0),(w*.6,g+.01,0),(w,g-.018,0)]
 else:path=[(-w,g+.075,0),(-w*.87,g+.035,0),(-w*.5,g+.006,0),(0,g,0),(w*.5,g+.006,0),(w*.87,g+.035,0),(w,g+.075,0)]
 tube('solid curved crossguard',path,d.get('guard_radius',.009),d.get('furniture','brass'),8)
 if d.get('gem'):
  tube('lozenge gem bezel',[(-.027,g,.025),(0,g+.019,.025),(.027,g,.025),(0,g-.019,.025),(-.027,g,.025)],.004,d.get('furniture','brass'),6)
  jewel(0,g,.019,d['gem'])
 if d.get('pommel_gem'):jewel(0,bottom+.006,.024,d['pommel_gem'])
 else:
  tube('solid pommel',[(0,bottom-.013,0),(0,bottom+.013,0)],[radius*.65,radius*1.15],d.get('furniture','brass'),10)


def axe_cheek(profile,side,cell='steel',depth=.021):
 # The outboard edge stays thin; the cheek grows into a thick inner spine at the haft/socket.
 rows=[]
 for row in profile:
  y,x,*inner=row
  a,b=(side*x,side*(inner[0] if inner else .008));rows.append((y,min(a,b),max(a,b)))
 ob=blade(rows,cell,depth,'tapered forged axe cheek')
 # Shift each ridge toward the socket: an axe wedge rather than a symmetrical dagger cross-section.
 for n,(y,left,right) in enumerate(rows):
  ridge=side*.025 if left+.001<side*.025<right-.001 else (left+right)/2
  ob.data.vertices[n*6+1].co.x=ridge;ob.data.vertices[n*6+4].co.x=ridge
 return ob


def pierced(ob,holes):
 for x,y,radius in holes:
  bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=.2,location=(x,y,0))
  cutter=bpy.context.object;cut=ob.modifiers.new('real open blade piercing','BOOLEAN');cut.operation='DIFFERENCE';cut.solver='EXACT';cut.object=cutter
  bpy.context.view_layer.objects.active=ob
  bpy.ops.object.modifier_apply(modifier=cut.name);bpy.data.objects.remove(cutter,do_unlink=True)


def axe(d):
 top=d.get('head_top',.43);bottom=-.47;headmid=d.get('head_mid',.34);r=d.get('haft_radius',.016)
 rod('continuous round haft through socket',bottom,top+.005,[r*1.05,r*.9],d.get('haft_cell','ash'),12)
 for y0,y1,cell in d.get('grips',[[bottom+.02,bottom+.26,'brown']]):
  rod('round grip sleeve',y0,y1,r*1.17,cell,12)
  for y in [y0,y1]:collar(y,r*1.27,.012,d.get('furniture','steel'))
  if d.get('grip_wrap',True):
   turns=max(4,round((y1-y0)*35));path=[]
   for n in range(turns*8+1):
    a=math.tau*n/8;path.append((r*1.23*math.cos(a),y0+(y1-y0)*n/(turns*8),r*1.23*math.sin(a)))
   tube('spiral leather lashing',path,.0026,cell,5)
 # A separate deep eye/socket surrounds the actual continuous haft at the joint.
 rod('deep steel socket',headmid-.06,headmid+.06,r*1.58,d.get('furniture','steel'),12)
 for y in [headmid-.063,headmid+.063]:collar(y,r*1.7,.011,d.get('furniture','steel'))
 left=axe_cheek(d['left'], -1,d.get('head_cell','steel'),d.get('head_depth',.024))
 if d.get('holes_left'):pierced(left,d['holes_left'])
 if d.get('right'):
  right=axe_cheek(d['right'],1,d.get('head_cell','steel'),d.get('head_depth',.024))
  if d.get('holes_right'):pierced(right,d['holes_right'])
 elif d.get('forked_poll'):
  for sign in [-1,1]:tube('open fork poll',[(.01,headmid+sign*.02,0),(.065,headmid+sign*.025,0),(.085,headmid+sign*.015,0)],[.009,.007,.002],d.get('head_cell','steel'),8)
 elif d.get('beak'):
  y=headmid;w=d['beak'];blade([(y-.027,.003,w*.25),(y,.003,w),(y+.027,.003,w*.25)],d.get('head_cell','steel'),.019,'thick poll beak')
 if d.get('spike'):
  rod('tapered top spike',top-.02,.497,[r*1.25,.0008],d.get('head_cell','steel'),8)
 if d.get('pommel_gem'):jewel(0,bottom+.008,r*1.25,d['pommel_gem'])
 for y,width,radius in d.get('extra_bands',[]):collar(y,radius,width,d.get('furniture','brass'))


def finish(icon):
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for ob in objects:
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob.select_set(False)
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7);bmesh.ops.triangulate(bm,faces=bm.faces[:],quad_method='SHORT_EDGE');bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(ob.data);bm.free()
  bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update();uv=bm.loops.layers.uv.active
  # Tiled material swatches can overlap; inset just the hard-boundary facets to separate their tangent frames.
  isolated=set()
  for e in bm.edges:
   if len(e.link_faces)!=2 or e.calc_face_angle()<=math.radians(40):continue
   if e.smooth and all(f.smooth for f in e.link_faces):continue
   a,b=e.link_faces;lookup=lambda f:{l.vert:l[uv].uv.copy() for l in f.loops};au,bu=lookup(a),lookup(b)
   if all((au[v]-bu[v]).length<1e-5 for v in e.verts):isolated.add(b)
  for f in isolated:
   centre=sum((l[uv].uv for l in f.loops),Vector((0,0)))/len(f.loops)
   offset=Vector((.0015,.001))
   for l in f.loops:l[uv].uv=centre+(l[uv].uv-centre)*.98+offset
  bm.to_mesh(ob.data);bm.free()
 support=rest_weapon(objects)
 bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='w02_'+icon
 # Export normals split at actual hard edges; UV projection is already split at their face boundaries.
 for poly in ob.data.polygons:
  assert poly.area>1e-10,(icon,'degenerate triangle')
 tris=len(ob.data.polygons);assert 20<tris<15000,(icon,tris)
 assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
 assert all(0<=c<=1 for uv in ob.data.uv_layers.active.data for c in uv.uv),icon
 for folder in ['blends','work/exports']: (P/folder).mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'blends'/f'w02_{icon}.blend'))
 bpy.ops.export_scene.gltf(filepath=str(P/'work/exports'/f'w02_{icon}_export.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_tangents=False)
 report=P/'work'/f'{icon}_geometry.json';report.write_text(json.dumps({'triangles':tris,**support,'origin':'footprint centred; lowest real vertex at zero','route':'Blender components'},indent=2)+'\n')
 print('BUILT',icon,tris,flush=True)


def main():
 args=sys.argv[sys.argv.index('--')+1:]
 for icon in args:
  d=DESIGNS['w02_'+icon];assert d['route']=='blender'
  bpy.ops.wm.read_factory_settings(use_empty=True);material()
  {'daggers':dagger,'axes':axe}[d['family']](d);finish(icon)

if __name__=='__main__':main()
