"""Native first-frame billboard presentation shared by Blender authoring and reference review.

These meshes are previews of native entity records, never exported as BModels.
The caller owns camera orientation and native serialization.
"""
import math
import bpy
from mathutils import Vector


def add_billboards(scene, records, root, scale=128, pack_images=False):
    collection=bpy.data.collections.new('Native decoration previews')
    scene.collection.children.link(collection)
    materials={}
    result=[]
    for entry in records:
        preview=entry['preview'];key=preview['decoded_path']
        if key not in materials:
            image=bpy.data.images.load(str(root/key),check_existing=True)
            if pack_images:image.pack()
            mat=bpy.data.materials.new('Native first frame '+entry['name']);mat.use_nodes=True
            nodes=mat.node_tree.nodes;nodes.clear()
            output=nodes.new('ShaderNodeOutputMaterial')
            texture=nodes.new('ShaderNodeTexImage');texture.image=image;texture.interpolation='Closest'
            diffuse=nodes.new('ShaderNodeBsdfDiffuse')
            transparent=nodes.new('ShaderNodeBsdfTransparent')
            mix=nodes.new('ShaderNodeMixShader');links=mat.node_tree.links
            links.new(texture.outputs['Color'],diffuse.inputs['Color'])
            links.new(texture.outputs['Alpha'],mix.inputs[0])
            links.new(transparent.outputs[0],mix.inputs[1]);links.new(diffuse.outputs[0],mix.inputs[2])
            links.new(mix.outputs[0],output.inputs[0]);materials[key]=mat
        w,h=[v*preview['scale']/scale for v in preview['pixels']]
        mesh=bpy.data.meshes.new('Decoration '+str(entry['index']))
        mesh.from_pydata([(-w/2,0,0),(w/2,0,0),(w/2,h,0),(-w/2,h,0)],[],[(0,1,2,3)])
        mesh.materials.append(materials[key]);uv=mesh.uv_layers.new()
        for loop,coord in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=coord
        obj=bpy.data.objects.new('Native decor #%d %s'%(entry['index'],entry['name']),mesh)
        obj.location=Vector(entry['position'])/scale;obj.rotation_euler=(math.pi/2,0,0)
        obj['levelgen_kind']='decoration_preview';obj['native_entity_index']=entry['index']
        obj['native_decoration_name']=entry['name']
        if 'semantic_id' in entry:obj['semantic_id']=entry['semantic_id']
        collection.objects.link(obj);result.append(obj)
    return result
