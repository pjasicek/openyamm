"""Low-poly solid sword, +Y toward its tip, origin at the solved grip centre."""
from pathlib import Path
import bpy,bmesh,json,math,sys
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
p=Path(__file__).resolve().parents[1];P=json.load(open(p/'textures/sword_profile.json'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap');px=P['metres_per_pixel'];cx=P['axis_x'];cy=P['grip_row']
def point(x,y,z):return ((x-cx)*px,(cy-y)*px,z)
def tex(x,y):return ((x-390)/300,1-y/1536)
def face(verts,coords):
 f=bm.faces.new(verts)
 for l,(x,y) in zip(f.loops,coords):l[uv].uv=tex(x,y)
 return f
poly=P['outline'];N=len(poly)
# Outer cutting edge and two broad bevelled surfaces. Back uses the same painted surface intentionally.
front=[bm.verts.new(point(x,y,0.0025)) for x,y in poly]
back=[bm.verts.new(point(x,y,-0.0025)) for x,y in poly]
tri=tessellate_polygon([[Vector((x,y,0)) for x,y in poly]])
lookup={(float(x),float(y)):i for i,(x,y) in enumerate(poly)}
for triangle in tri:
 ids=list(triangle)
 face([front[i] for i in ids],[poly[i] for i in ids])
 face([back[i] for i in reversed(ids)],[poly[i] for i in reversed(ids)])
for i in range(N):
 j=(i+1)%N;face([front[i],back[i],back[j],front[j]],[poly[i],poly[i],poly[j],poly[j]])
# Twelve-sided grip, steel ferrules and a faceted pommel.
rings=[]
for row,radius in [(1215,.021),(1250,.019),(1260,.016),(1340,.016),(1430,.016),(1442,.019),(1452,.018),(1470,.028),(1492,.016),(1510,.001)]:
 ring=[bm.verts.new((radius*math.cos(k*math.tau/12),(cy-row)*px,radius*math.sin(k*math.tau/12))) for k in range(12)]
 rings.append((row,ring))
for (ra,a),(rb,b) in zip(rings[:-1],rings[1:]):
 for k in range(12):
  j=(k+1)%12;u0=518+45*k/12;u1=518+45*(k+1)/12
  face([a[k],b[k],b[j],a[j]],[(u0,ra),(u0,rb),(u1,rb),(u1,ra)])
for row,ring in (rings[0],rings[-1]):face(list(reversed(ring)),[(540,row)]*12)
# Forged crossguard: three rectangular sections bevelled at the ends.
prev=None
for x,half,z in [(420,10,.006),(435,20,.009),(515,12,.012),(540,29,.019),(565,12,.012),(647,20,.009),(662,10,.006)]:
 coords=[(x,1225-half),(x,1225+half)]
 r=[bm.verts.new(point(x,y,zz)) for y,zz in [(1225-half,-z),(1225+half,-z),(1225+half,z),(1225-half,z)]]
 if prev:
  xp,rr,hp=prev
  for k in range(4):
   j=(k+1)%4
   face([rr[k],r[k],r[j],rr[j]],[(xp,1225+(-hp if k in (0,3) else hp)),(x,1225+(-half if k in (0,3) else half)),(x,1225+(-half if j in (0,3) else half)),(xp,1225+(-hp if j in (0,3) else hp))])
 else:face(list(reversed(r)),[(x,1225)]*4)
 prev=(x,r,half)
face(prev[1],[(662,1225)]*4)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
me=bpy.data.meshes.new('SwordMesh');bm.to_mesh(me);bm.free();assert not me.validate()
o=bpy.data.objects.new('SwordMesh',me);bpy.context.scene.collection.objects.link(o)
m=bpy.data.materials.new('Sword_A');m.use_nodes=True;nt=m.node_tree
bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(p/'textures/m604_sword_basecolor.png'));nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.4;nt.nodes.active=tx
me.materials.append(m)
bpy.context.view_layer.objects.active=o;o.select_set(True)
bevel=o.modifiers.new('Forged edge bevel','BEVEL');bevel.width=0.0012;bevel.segments=1;bevel.limit_method='ANGLE';bevel.angle_limit=0.65
bpy.ops.object.modifier_apply(modifier=bevel.name)
print('SWORD',len(me.polygons),'triangles')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/props.blend'))
sys.path.insert(0,str(p/'scripts'));import common
# Present the local +Y blade upright for the prop review only.
o.rotation_euler.x=math.pi/2
common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/sword'),.36,1.1,views=('front','three_quarter','left'),resolution=(360,700))
