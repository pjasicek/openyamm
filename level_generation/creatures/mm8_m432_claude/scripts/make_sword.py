"""Long dark blade and gold two-hand hilt, modelled from the selected broadside master."""
import bpy,bmesh,math,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap');PX=1.65/1455;ORIGIN=1240;axis=512
# UVs project the actual reference on both broad faces; narrow edges reuse the matching edge colour.
def vertex(x,row,depth):return bm.verts.new(((x-axis)*PX,(ORIGIN-row)*PX,depth))
def face(vs,coords):
    f=bm.faces.new(vs)
    for loop,(x,row) in zip(f.loops,coords):loop[uv].uv=(x/1024,1-row/1536)
    return f
rows=[(40,512,512),(90,502,522),(160,494,530),(250,488,537),(600,488,537),(1000,486,539),(1138,481,544)]
prev=None
for r,lo,hi in rows:
    if r==40:
        tip=vertex(512,r,0);continue
    thick=.0045*min(1,(r-40)/140);xs=[lo,512,hi,512];depths=[0,thick,0,-thick]
    cur=[vertex(x,r,z) for x,z in zip(xs,depths)]
    for i in range(4):
        j=(i+1)%4
        if prev is None:face([tip,cur[j],cur[i]],[(512,40),(xs[j],r),(xs[i],r)])
        else:face([prev[i],prev[j],cur[j],cur[i]],[(pxs[i],pr),(pxs[j],pr),(xs[j],r),(xs[i],r)])
    prev,pxs,pr=cur,xs,r
face(list(reversed(prev)),[(x,pr) for x in reversed(pxs)])
# Curved guard: closed solid, centred on the blade.
outline=[(411,1144),(426,1152),(451,1157),(481,1147),(498,1144),(526,1144),(543,1147),(573,1157),(598,1152),(612,1144),(607,1157),(594,1169),(573,1175),(540,1176),(529,1185),(495,1185),(484,1176),(451,1175),(429,1169),(416,1157)]
a=[vertex(x,r,.009) for x,r in outline];b=[vertex(x,r,-.009) for x,r in outline]
face(a,outline);face(list(reversed(b)),list(reversed(outline)))
for i in range(len(a)):
    j=(i+1)%len(a);face([a[i],b[i],b[j],a[j]],[outline[i],outline[i],outline[j],outline[j]])
# Eight-sided wrapped grip, two ferrules and a faceted pointed pommel.
rings=[(1181,.016),(1191,.016),(1197,.012),(1240,.012),(1320,.012),(1414,.012),(1418,.016),(1426,.016),(1450,.030),(1495,.0008)]
prev=None
for row,rad in rings:
    cur=[];coords=[]
    for k in range(8):
        t=2*math.pi*k/8;x=axis+rad*math.cos(t)/PX;cur.append(vertex(x,row,rad*math.sin(t)));coords.append((x,row))
    if prev:
        for k in range(8):
            j=(k+1)%8;face([prev[k],prev[j],cur[j],cur[k]],[pc[k],pc[j],coords[j],coords[k]])
    else:face(list(reversed(cur)),list(reversed(coords)))
    prev,pc=cur,coords
face(cur,coords)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
me=bpy.data.meshes.new('SwordMesh');bm.to_mesh(me);bm.free();o=bpy.data.objects.new('SwordMesh',me);bpy.context.collection.objects.link(o)
mat=bpy.data.materials.new('Sword');mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.48
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'references_props/sword.png'));tex.image.pack()
mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
mat['openyamm_specular_mask']=True
assert len(me.polygons)<600
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/sword.blend'))
(P/'work/sword_geometry.json').write_text(json.dumps({'triangles':len(me.polygons),'length_m':1.65,'grip_radius_m':.012,'primary_hand_to_guard_m':(1240-1181)*PX,'hand_spacing_m':.115},indent=1))
print('SWORD',len(me.polygons),'triangles')
