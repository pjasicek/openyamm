"""Trace the selected MM8 axe reference into bevelled solids with two real blade openings."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
K=1.30/1444;CX=512;BOT=1492;objects=[]
def xy(x,y):return ((x-CX)*K,(BOT-y)*K)
outer=[(558,257),(603,254),(651,244),(689,219),(714,188),(720,156),(710,119),(690,85),(662,49),(716,64),(765,89),(809,125),(845,173),(872,225),(889,283),(894,343),(887,403),(869,460),(838,504),(797,539),(749,561),(700,574),(650,578),(679,555),(701,522),(715,488),(713,458),(700,430),(675,412),(644,399),(609,393),(559,400)]
hole=[(590,342),(609,311),(634,287),(664,273),(693,273),(718,285),(735,306),(744,332),(741,358),(731,380),(709,397),(683,401),(656,392),(632,377),(610,359)]
for side in [-1,1]:
 cv=bpy.data.curves.new('Blade','CURVE');cv.dimensions='2D';cv.resolution_u=1;cv.fill_mode='BOTH';cv.extrude=.009;cv.bevel_depth=.0025;cv.bevel_resolution=0
 for polygon in [outer,list(reversed(hole))]:
  sp=cv.splines.new('POLY');sp.points.add(len(polygon)-1)
  for q,(x,y) in zip(sp.points,polygon):a,z=xy(CX+side*(x-CX),y);q.co=(a,z,0,1)
  sp.use_cyclic_u=True
 ob=bpy.data.objects.new('Crescent blade',cv);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob=bpy.context.object
 for v in ob.data.vertices:x,z,d=v.co;v.co=(x,d,z)
 for layer in list(ob.data.uv_layers):ob.data.uv_layers.remove(layer)
 uv=ob.data.uv_layers.new(name='UVMap')
 for f in ob.data.polygons:
  for li in f.loop_indices:
   v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=((CX+v.x/K)/1024,1-(BOT-v.z/K)/1536)
 for v in ob.data.vertices:v.co.x*=.8;v.co.z=1.05+(v.co.z-1.05)*.8
 objects.append(ob);ob.select_set(False)
def tube(name,stations,n=12):
 vs=[];fs=[]
 for y,r in stations:
  for i in range(n):t=2*math.pi*i/n;vs.append((r*math.cos(t),r*math.sin(t),(BOT-y)*K))
 for j in range(len(stations)-1):
  for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 fs.extend([tuple(reversed(range(n))),tuple((len(stations)-1)*n+i for i in range(n))]);me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);objects.append(ob);uv=me.uv_layers.new(name='UVMap')
 for f in me.polygons:
  f.use_smooth=True
  for li in f.loop_indices:
   i=me.loops[li].vertex_index;y=stations[i//n][0];uv.data[li].uv=((476+(i%n)/n*72)/1024,1-y/1536)
 return ob
# A continuous shaft with texture-defined leather wraps: no spiral sliver geometry.
tube('Wood and leather shaft',[(390,.017),(550,.018),(768,.018),(972,.018),(1325,.018),(1395,.017)])
for y in [426,548,768,972,1325,1390]:tube('Brass ferrule',[(y-12,.018),(y-8,.022),(y+8,.022),(y+12,.018)])
tube('Steel socket',[(241,.030),(251,.038),(391,.038),(404,.030)])
tube('Brass top cap',[(186,0),(193,.017),(205,.027),(220,.030),(235,.029),(244,.037)])
tube('Steel pommel',[(1394,.019),(1410,.033),(1434,.043),(1460,.040),(1482,.024),(1492,0)])
mat=bpy.data.materials.new('MinotaurAxe');mat.use_nodes=True;tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/'references_hd/axe_reference.png'));tx.image.pack();bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.62
for o in bpy.data.objects:o.select_set(o in objects)
for o in objects:o.data.materials.clear();o.data.materials.append(mat)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=o.data.name='Axe';bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free();assert bad==0,bad
report={'triangles':len(o.data.polygons),'closed_edges':True,'shaft_radius_m':.018,'blade_width_m':.55,'reference':'references_hd/axe_reference.png','uv':'Projected blade design; intentionally shared front/back and wrapped shaft UVs'};(P/'review/axe_geometry.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/axe.blend'))
sc=bpy.context.scene;common.workbench_clay(sc,textured=True)
common.render_views(str(P/'review/axe'),.68,1.5,views=('front','three_quarter','left'),resolution=(600,1000))
