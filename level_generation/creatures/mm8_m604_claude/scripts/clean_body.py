"""Repair source-confirmed equipment omissions; keep every selected anatomical surface."""
from pathlib import Path
import sys
import json
import math
import bpy
import bmesh
import numpy as np
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
assert len(parts)==58
# These two single triangles bridge otherwise separate chain/belt surfaces.
for name in ('P56','P57'):
    assert len(parts[name].data.polygons)==1
    bpy.data.objects.remove(parts.pop(name),do_unlink=True)
mantle=parts['P01']
for v in mantle.data.vertices:
    w=max(0.0,min(1.0,(v.co.y+0.01)/0.08))
    if v.co.z<1.55:
        v.co.z+=w*(1.55-v.co.z)*0.72
chain_ids=[9,12,13,14,15,16,17,19,20,21,23,25,26,28,54]
from mathutils import Vector
from mathutils.bvhtree import BVHTree
skin_tree=BVHTree.FromObject(parts['P00'],bpy.context.evaluated_depsgraph_get())
for side in (-1,1):
    vertices=[]; faces=[]
    for z in np.linspace(1.14,1.51,14):
        x=side*0.091
        hit,normal,index,distance=skin_tree.ray_cast(Vector((x,1.0,float(z))),Vector((0,-1,0)))
        assert hit is not None,(x,z)
        for dx,dy in ((-0.012,0.004),(0.012,0.004),(0.012,0.010),(-0.012,0.010)):
            vertices.append((x+dx,hit.y+dy,float(z)))
    for i in range(13):
        for j in range(4):
            a=i*4+j; b=i*4+(j+1)%4
            faces.append((a,b,b+4,a+4))
    faces.extend(((3,2,1,0),(52,53,54,55)))
    mesh=bpy.data.meshes.new('RearChainStrip'); mesh.from_pydata(vertices,[],faces); mesh.update()
    bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(mesh); bm.free()
    target=bpy.data.objects.new('P58' if side<0 else 'P59',mesh)
    bpy.context.scene.collection.objects.link(target)
    target.data.materials.append(parts['P09'].data.materials[0])
    parts[target.name]=target
labels={}
for name,o in parts.items():
    ident=int(name[1:])
    if ident==0: label='body'
    elif ident in (1,55): label='mantle'
    elif ident==18: label='front_panel'
    elif ident==24: label='rear_panel'
    elif ident in (10,11): label='head_ridge'
    elif ident in (3,4): label='kneecap'
    elif ident in (7,8): label='ankle_ring'
    elif ident in (5,6) or 40<=ident<=53: label='arm_ring'
    elif ident in chain_ids or ident>=58: label='chain'
    elif ident==22: label='hip_garment'
    else: label='belt'
    labels[ident]=label
    attr=o.data.attributes.new('piece','INT','POINT')
    attr.data.foreach_set('value',[ident]*len(o.data.vertices))
    o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00']
bpy.ops.object.join()
body=bpy.context.view_layer.objects.active
body.name=body.data.name='Body'
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
(p/'work/garments.json').write_text(json.dumps(labels,indent=2))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/clean_body'),0.925,2.05,views=('front','back','left'),resolution=(600,900))
# Temporary, neutral texture satisfies the rigging upload contract; final UVs/textures come after the rig.
body.data.materials.clear()
material=bpy.data.materials.new('RiggingPreview'); material.use_nodes=True
image=bpy.data.images.new('rigging_preview',width=4,height=4)
image.pixels=[0.65,0.65,0.65,1.0]*16; image.pack()
node=material.node_tree.nodes.new('ShaderNodeTexImage'); node.image=image
material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(material)
for face in body.data.polygons: face.material_index=0
if not body.data.uv_layers:
    uv=body.data.uv_layers.new(name='ProvisionalUV')
    for loop in body.data.loops:
        v=body.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=((v.x+0.7)/1.4,v.z/1.85)
for o in bpy.data.objects: o.select_set(o==body)
bpy.ops.export_scene.gltf(filepath=str(p/'export/body_for_rig.glb'),use_selection=True,export_format='GLB',
    export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
assert (p/'export/body_for_rig.glb').stat().st_size>10000
print('CLEAN',len(body.data.vertices),'vertices',len(labels),'parts; rear mantle and straps corrected')
