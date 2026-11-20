"""Build the native wavy sword as a small closed mesh from the reviewed reference silhouette."""
from pathlib import Path
import bpy,bmesh,json,math,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
P=json.loads((p/'textures/props/sword_profile.json').read_text());rows={int(k):v for k,v in P['rows'].items()};cols={int(k):v for k,v in P['guard_columns'].items()}
scale=P['length_m']/(max(rows)-min(rows));axis=P['axis_x'];gy=P['grip_row']
bpy.ops.wm.read_factory_settings(use_empty=True)
bm=bmesh.new();uvl=bm.loops.layers.uv.new('UVMap')
def point(x,r,z):return ((x-axis)*scale,(gy-r)*scale,z)
def uv(x,r):return ((x-340)/345,1-r/1536)
def face(vs,pixels):
 f=bm.faces.new(vs)
 for loop,xy in zip(f.loops,pixels):loop[uvl].uv=uv(*xy)
 return f
# Four vertices per blade ring preserve its edge waves and shallow central ridge.
prev=None
for r in [min(rows)+2]+list(range(28,1105,20))+[1105]:
 lo,hi=rows[r];cx=(lo+hi)/2;th=.0035*min(1,(r-min(rows)+1)/70)
 ring=[bm.verts.new(point(x,r,z)) for x,z in [(lo,0),(cx,th),(hi,0),(cx,-th)]]
 xs=[lo,cx,hi,cx]
 if prev:
  old,ox,rr=prev
  for i in range(4):
   j=(i+1)%4;face([old[i],old[j],ring[j],ring[i]],[(ox[i],rr),(ox[j],rr),(xs[j],r),(xs[i],r)])
 else:face(list(reversed(ring)),list(reversed([(x,r) for x in xs])))
 prev=(ring,xs,r)
face(prev[0],[(x,prev[2]) for x in prev[1]])
# Guard profile sampled vertically so its hooked tips and upper concavity remain visible.
prev=None
for x in sorted(set([min(cols),max(cols)]+list(range(min(cols),max(cols)+1,9)))):
 if x not in cols:continue
 top,bottom=cols[x];ring=[bm.verts.new(point(x,r,z)) for r,z in [(top,.012),(bottom,.012),(bottom,-.012),(top,-.012)]];rs=[top,bottom,bottom,top]
 if prev:
  old,orr,xx=prev
  for i in range(4):
   j=(i+1)%4;face([old[i],old[j],ring[j],ring[i]],[(xx,orr[i]),(xx,orr[j]),(x,rs[j]),(x,rs[i])])
 else:face(list(reversed(ring)),list(reversed([(x,r) for r in rs])))
 prev=(ring,rs,x)
face(prev[0],[(prev[2],r) for r in prev[1]])
# Grip and rounded pommel, octagonal rings; detail remains in the image.
prev=None
for r in [1142,1155,1170,1210,1275,1340,1394,1410,1424,1445,1470,1484,max(rows)]:
 lo,hi=rows[r];radius=max((hi-lo)*scale/2,.001);radius=min(radius,.016) if 1155<=r<=1394 else radius;depth=radius if r<1410 else radius*.42
 ring=[];pixels=[]
 for i in range(8):
  a=i*math.tau/8;x=axis+math.cos(a)*radius/scale;ring.append(bm.verts.new(point(x,r,math.sin(a)*depth)));pixels.append((x,r))
 if prev:
  old,op=prev
  for i in range(8):
   j=(i+1)%8;face([old[i],old[j],ring[j],ring[i]],[op[i],op[j],pixels[j],pixels[i]])
 else:face(list(reversed(ring)),list(reversed(pixels)))
 prev=(ring,pixels)
face(prev[0],prev[1]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
assert not any(e.is_boundary for e in bm.edges)
assert all(f.calc_area()>1e-10 for f in bm.faces)
me=bpy.data.meshes.new('Sword');bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('SwordMesh',me);bpy.context.collection.objects.link(ob)
mat=bpy.data.materials.new('SwordMat');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'textures/props/sword_base.png'));mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.65;bs.inputs['Metallic'].default_value=0;mat['openyamm_specular_mask']=True;me.materials.append(mat)
for f in me.polygons:f.use_smooth=False
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
assert len(me.polygons)<1000
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/sword.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'export/sword_static.glb'),use_selection=True,export_format='GLB',export_animations=False,export_yup=True)
print('SWORD',len(me.polygons),'triangles',round(scale*1536,3),'metres canvas')
assert len(me.polygons)<1000
