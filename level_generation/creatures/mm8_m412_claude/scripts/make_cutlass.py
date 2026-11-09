"""Reference-profile cutlass, in attachment space: +Y along the blade, origin at the grip centre."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];s=json.loads((p/'textures/props/cutlass_profile.json').read_text());px=s['metres_per_pixel'];cx,cy=s['grip_centre'];x0,y0,x1,y1=s['crop']
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[];faces=[];uvs=[]
def uv(x,y):return ((x-x0)/(x1-x0),1-(y-y0)/(y1-y0))
def add(x,y,z=0):
 verts.append(((x-cx)*px,(cy-y)*px,z));uvs.append(uv(x,y));return len(verts)-1
def face(ids):faces.append(ids)
# Six-sided bevel section, with the source image projected onto both broad faces.
rings=[]
for row,bounds in sorted(((int(k),v) for k,v in s['rows'].items()),reverse=True):
 l,r=bounds;w=r-l;th=.0025*min(1,w/20)
 ring=[add(l,row,0),add(l+.08*w,row,th),add(r-.12*w,row,th),add(r,row,0),add(r-.12*w,row,-th),add(l+.08*w,row,-th)]
 if row==1194:
  for i in ring:
   x,y,z=verts[i];verts[i]=(x,.078-.5*x-.003,z)
 rings.append(ring)
for a,b in zip(rings[:-1],rings[1:]):
 for k in range(6):face([a[k],b[k],b[(k+1)%6],a[(k+1)%6]])
face(rings[0][::-1]);face(rings[-1])
# Cylindrical green grip, fitted to the solved 12 mm handle radius.
last=None
for row in [1389,1375,1340,1300,1260,1225,1185]:
 rad=.012 if row not in [1389,1185] else .011
 ids=[]
 for k in range(12):
  t=2*math.pi*k/12;x=cx+rad/px*math.cos(t);z=rad*math.sin(t)
  ids.append(add(x,row,z))
  uvs[-1]=uv(478+21*math.cos(t),row)
 if last:
  for k in range(12):face([last[k],ids[k],ids[(k+1)%12],last[(k+1)%12]])
 else:face(ids[::-1])
 last=ids
face(last)
# Thin oval cup: broad enough for the knuckles, with a rolled rim and an open bowl underneath.
last=None
for r,dy in [(0,.004),(.45,.001),(1,0),(1,-.004),(.45,-.005),(0,-.006)]:
 ids=[]
 for k in range(24):
  t=2*math.pi*k/24;xx=.063*r*math.cos(t);zz=.040*r*math.sin(t);yy=.078+dy+.012*(1-r*r)-.5*xx-math.sin(math.radians(60))*zz;zz*=math.cos(math.radians(60))
  ids.append(add(cx+xx/px,cy-yy/px,zz))
  uvs[-1]=uv(cx+xx/px,cy-yy/px)
 if last:
  for k in range(24):face([last[k],ids[k],ids[(k+1)%24],last[(k+1)%24]])
 last=ids
# Knuckle bow follows the left-hand silhouette of the HD reference.
path=[(405,1145),(375,1125),(342,1145),(321,1180),(318,1225),(329,1287),(353,1348),(386,1383),(446,1400)]
last=None
for i,(x,y) in enumerate(path):
 tangent=Vector((path[min(i+1,len(path)-1)][0]-path[max(0,i-1)][0],path[min(i+1,len(path)-1)][1]-path[max(0,i-1)][1])).normalized()
 perp=Vector((-tangent.y,tangent.x));ids=[]
 for k in range(8):
  t=2*math.pi*k/8;rad=.0065;xx=x+perp.x*rad/px*math.cos(t);yy=y+perp.y*rad/px*math.cos(t)
  ids.append(add(xx,yy,rad*math.sin(t)))
 if last:
  for k in range(8):face([last[k],ids[k],ids[(k+1)%8],last[(k+1)%8]])
 else:face(ids[::-1])
 last=ids
face(last)
# Small steel pommel.
last=None
for j in range(9):
 a=math.pi*j/8;ids=[]
 for k in range(12):
  t=2*math.pi*k/12;r=.024*math.sin(a);x=477+r/px*math.cos(t);y=1412+.026/px*math.cos(a)
  ids.append(add(x,y,r*math.sin(t)))
 if last:
  for k in range(12):face([last[k],ids[k],ids[(k+1)%12],last[(k+1)%12]])
 last=ids
me=bpy.data.meshes.new('CutlassMesh');me.from_pydata(verts,[],faces);me.update();layer=me.uv_layers.new(name='UVMap')
for face0 in me.polygons:
 for li in face0.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free();assert not me.validate(verbose=True)
o=bpy.data.objects.new('CutlassMesh',me);bpy.context.scene.collection.objects.link(o)
mat=bpy.data.materials.new('PirateCutlass_A');mat.use_nodes=True;n=mat.node_tree.nodes;lk=mat.node_tree.links;bs=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'textures/props/cutlass_basecolor.png'));lk.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.4;me.materials.append(mat)
for f in me.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cutlass.blend'))
# Show the broad side upright for an easy reference comparison.
o.rotation_euler=(math.pi/2,0,0);bpy.context.view_layer.update();common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='TEXTURE'
common.render_views(str(p/'review/cutlass'),.38,1.05,views=('front','three_quarter'),resolution=(600,900),target=(.035,0))
print('CUTLASS',len(me.vertices),'vertices',len(me.polygons),'triangles')
