"""Native trident proportions, volumetric shaft/tines; UVs project the selected painted prop reference."""
import bpy,bmesh,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bm=bmesh.new();uv=bm.loops.layers.uv.new('UVMap')
# Prop +Y points to the tines. The shaft is slender; reverse grip lies 0.82 m behind the tip.
def py(row):
    return .82-(row-30)*(.40/380) if row<=410 else .42-(row-410)*(1.40/1080)
def point(x,row,z=0):return Vector(((x-512)*(.40/380),py(row),z))
def face(vs,coords):
    f=bm.faces.new(vs)
    for loop,(x,y) in zip(f.loops,coords):loop[uv].uv=(x/1024,1-y/1536)
def tube(profile,sides=8):
    rings=[]
    for i,(x,row,r) in enumerate(profile):
        c=point(x,row);a=point(*profile[max(0,i-1)][:2]);b=point(*profile[min(len(profile)-1,i+1)][:2])
        tangent=(b-a).normalized();side=Vector((-tangent.y,tangent.x,0));front=Vector((0,0,1))
        ring=[];tex=[]
        for k in range(sides):
            th=math.tau*k/sides;offset=side*(math.cos(th)*r*.00105)+front*(math.sin(th)*r*.0006)
            ring.append(bm.verts.new(c+offset));tex.append((x+math.cos(th)*r*.85,row))
        rings.append((ring,tex))
    for (a,au),(b,bu) in zip(rings[:-1],rings[1:]):
        for k in range(sides):
            j=(k+1)%sides;face([a[k],a[j],b[j],b[k]],[au[k],au[j],bu[j],bu[k]])
    for ring,tex in (rings[0],rings[-1]):face(list(reversed(ring)),list(reversed(tex)))
# Shaft bands and blue-violet collar are in the image; rings hold their silhouette.
shaft=[]
for row,r in [(410,18),(422,19),(443,19),(451,17),(478,17),(489,19),(518,19),(526,12),(710,12),(719,18),(744,18),(752,12),(1022,12),(1029,18),(1052,18),(1060,12),(1392,12),(1401,18),(1427,18),(1436,14),(1473,14),(1487,18),(1494,4)]:shaft.append((512,row,r))
tube(shaft)
tube([(512,30,1),(512,85,9),(512,174,24),(512,209,12),(512,245,10),(512,360,12),(512,396,22),(512,410,18)],4)
for sign in (-1,1):
    prof=[(512,399,12),(512+sign*39,372,10),(512+sign*69,343,10),(512+sign*86,311,9),(512+sign*88,276,8),(512+sign*81,244,7),(512+sign*69,210,6),(512+sign*56,179,4),(512+sign*48,136,1)]
    tube(prof,6)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bmesh.ops.triangulate(bm,faces=bm.faces[:])
me=bpy.data.meshes.new('TridentMesh');bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('TridentMesh',me);bpy.context.collection.objects.link(ob)
for f in me.polygons:f.use_smooth=True
mat=bpy.data.materials.new('Trident');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.6
im=bpy.data.images.load(str(P/'references_props/trident.png'));tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
assert len(me.polygons)<1200
print('TRIDENT triangles',len(me.polygons),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/trident.blend'))
