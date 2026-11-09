import bpy,bmesh,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
def begin():return [],[],[]
def vertex(vs,uvs,pt,px):vs.append(tuple(pt));uvs.append((px[0]/1464,1-px[1]/1075));return len(vs)-1
def tube(vs,fs,uvs,points,radius,sides=8,patch=(450,72,548,112)):
 rings=[]
 for j,p in enumerate(points):
  p=Vector(p);d=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])).normalized();ref=Vector((1,0,0))if abs(d.x)<.8 else Vector((0,1,0));u=d.cross(ref).normalized();v=d.cross(u);ring=[]
  for k in range(sides):
   a=k*math.tau/sides;ring.append(vertex(vs,uvs,p+radius*(u*math.cos(a)+v*math.sin(a)),(patch[0]+(patch[2]-patch[0])*k/sides,patch[1]+(patch[3]-patch[1])*j/max(1,len(points)-1))))
  rings.append(ring)
 for a,b in zip(rings,rings[1:]):
  for k in range(sides):fs.append((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
 fs.extend([tuple(reversed(rings[0])),tuple(rings[-1])])
def finish(name,vs,fs,uvs,tag):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();uv=me.uv_layers.new(name='UVMap')
 for f in me.polygons:
  for li,vi in zip(f.loop_indices,f.vertices):uv.data[li].uv=uvs[vi]
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 mat=bpy.data.materials.new(name+'_A');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/f'textures/{tag}_basecolor_1k.png'));nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.78;bs.inputs['Metallic'].default_value=.5 if tag=='blade'else 0;me.materials.append(mat)
 for f in me.polygons:f.use_smooth=True
 return ob
# Blade silhouette digitized from the selected side design; six-sided bevels and a raised central face.
vs,fs,uvs=begin();ys=[38,65,115,145,210,280,350,440,530,620,710,800,900,980,1028];left=[401,375,336,351,349,344,344,347,359,380,409,452,508,559,588];right=[406,412,414,413,414,420,414,418,433,457,491,530,563,582,588];rings=[];scale=.65/990
for y in np.linspace(38,1028,29):
 l=float(np.interp(y,ys,left));r=float(np.interp(y,ys,right));w=max(r-l,1);profile=[(l,0),(l+w*.18,-.0035),(r-w*.18,-.0035),(r,0),(r-w*.18,.0035),(l+w*.18,.0035)];rings.append([vertex(vs,uvs,((x-385)*scale,d,(y-38)*scale),(x,y))for x,d in profile])
for a,b in zip(rings,rings[1:]):
 for j in range(6):fs.append((a[j],a[(j+1)%6],b[(j+1)%6],b[j]))
fs.extend([tuple(reversed(rings[0])),tuple(rings[-1])])
# Two leather cuffs match the native forearm mounting; the hand remains open beneath the blade.
for z,rad in [(.035,.043),(.145,.033)]:
 rr=[]
 for zz,r in [(z-.015,rad),(z-.012,rad+.003),(z+.012,rad+.003),(z+.015,rad)]:
  rr.append([vertex(vs,uvs,(-rad+r*math.cos(k*math.tau/24),r*math.sin(k*math.tau/24),zz),(430+k/24*117,63+(zz-z+.015)/.03*61))for k in range(24)])
 for a,b in zip(rr,rr[1:]):
  for k in range(24):fs.append((a[k],a[(k+1)%24],b[(k+1)%24],b[k]))
 for dz in [-.012,.012]:
  pts=[(-rad+(rad+.004)*math.cos(k*math.tau/24),(rad+.004)*math.sin(k*math.tau/24),z+dz)for k in range(25)];tube(vs,fs,uvs,pts,.0013,4)
for y in [75,128,214]:
 x=float(np.interp(y,ys,left)*.35+np.interp(y,ys,right)*.65);xx=(x-385)*scale;zz=(y-38)*scale;tube(vs,fs,uvs,[(xx,-.003,zz),(xx,-.008,zz)],.005,10,(381,66,400,85))
blade=finish('ForearmBlade',vs,fs,uvs,'blade')
# Convex hide shield. The UVs project the real design front/back; bevelled rim, lacing and rear grip are geometry.
vs,fs,uvs=begin();outline=json.loads((P/'work/shield_outline.json').read_text());miny,maxy=outline[0][0],outline[-1][0];maxwidth=max(r-l for y,l,r in outline);rings=[]
for back in [False,True]:
 side=[]
 for y,l,r in outline:
  row=[]
  for u in np.linspace(-1,1,7):
   x=(r-l)*.5/maxwidth*.35*u;z=.61-1.22*(y-miny)/(maxy-miny);d=-.030*(1-u*u)+(.009 if back else -.009);px=740+u*(r-l)*.49 if back else (l+r)*.5+u*(r-l)*.5;row.append(vertex(vs,uvs,(x,d,z),(px,y)))
  side.append(row)
 rings.append(side)
 for a,b in zip(side,side[1:]):
  for k in range(6):fs.append((a[k],a[k+1],b[k+1],b[k]))
for k in [0,6]:
 for j in range(len(outline)-1):fs.append((rings[0][j][k],rings[0][j+1][k],rings[1][j+1][k],rings[1][j][k]))
for end in [0,-1]:
 for k in range(6):fs.append((rings[0][end][k],rings[1][end][k],rings[1][end][k+1],rings[0][end][k+1]))
for side in [-1,1]:
 points=[(side*(r-l)*.5/maxwidth*.35,0,.61-1.22*(y-miny)/(maxy-miny))for y,l,r in outline];tube(vs,fs,uvs,points,.0055,6,(186,240,198,570))
 # Raised rawhide stitches across the rim, following the native narrow edge.
 for j in range(2,len(points)-2,2):
  x,y,z=points[j];tube(vs,fs,uvs,[(x-side*.006,-.012,z-.005),(x+side*.003,-.006,z),(x+side*.004,.006,z+.005)],.0015,4,(192,292,197,312))
tube(vs,fs,uvs,[(0,.012,-.54),(0,.016,.53)],.010,10,(731,108,749,855));tube(vs,fs,uvs,[(-.075,.045,.26),(.075,.045,.26)],.012,16,(661,299,811,328))
for x in [-.076,.076]:tube(vs,fs,uvs,[(x,-.015,.26),(x,.045,.26)],.009,8,(653,300,672,326))
# The lower retaining strap is an arched leather band with separate bevelled edges.
path=[(x,.025+.025*(1-(x/.085)**2),.055)for x in np.linspace(-.085,.085,9)]
rr=[]
for x,y,z in path:rr.append([vertex(vs,uvs,(x,y+dy,z+dz),(670+(x+.085)/.17*140,466+(dz+.025)/.05*47))for dy,dz in [(-.002,-.025),(.002,-.023),(.002,.023),(-.002,.025)]])
for a,b in zip(rr,rr[1:]):
 for k in range(4):fs.append((a[k],a[(k+1)%4],b[(k+1)%4],b[k]))
for py in [200,450,735]:
 y,l,r=min(outline,key=lambda t:abs(t[0]-py));z=.61-1.22*(y-miny)/(maxy-miny);x=(r-l)*.5/maxwidth*.35-.014
 for side in [-1,1]:tube(vs,fs,uvs,[(side*x,-.011,z),(side*x,-.019,z)],.007,10,(192,441,207,456))
shield=finish('LeafShield',vs,fs,uvs,'shield');report={o.name:{'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'vertices':len(o.data.vertices)}for o in [blade,shield]};assert all(1000<=r['triangles']<=3000 for r in report.values()),report
(P/'work/prop_geometry.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/props.blend'))
common.workbench_clay(bpy.context.scene,textured=True)
for ob,tag,c,h in [(blade,'blade',.325,.78),(shield,'shield',0,1.35)]:
 for o in [blade,shield]:o.hide_render=o!=ob
 common.render_views(str(P/f'review/{tag}_detail'),c,h,views=('front','three_quarter','back'),resolution=(700,1000))
print('PROPS',report,flush=True)
