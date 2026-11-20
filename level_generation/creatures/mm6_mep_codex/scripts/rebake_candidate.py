import bpy

def rebake_preview(target,source,folder,tag):
    """Reproject tier-A appearance from unreduced surfaces, retaining atlas chart boundaries."""
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
    source.hide_render=False;source.hide_set(False)
    original_materials=list(target.data.materials)
    target_indices=[f.material_index for f in target.data.polygons];source_indices=[f.material_index for f in source.data.polygons]
    source.data.materials.clear();target.data.materials.clear()
    images=[]
    for i,original in enumerate(original_materials):
        high=original.copy();high.name=original.name+'_source'
        bs=high.node_tree.nodes.get('Principled BSDF');color=bs.inputs['Base Color'].links[0].from_node.outputs['Color']
        emission=high.node_tree.nodes.new('ShaderNodeEmission');high.node_tree.links.new(color,emission.inputs['Color'])
        high.node_tree.links.new(emission.outputs[0],high.node_tree.nodes.get('Material Output').inputs['Surface'])
        source.data.materials.append(high)
        low=original.copy();low.name=original.name+'_baked';target.data.materials.append(low)
        image=bpy.data.images.new(tag+'_'+str(i),width=1024,height=1024,alpha=False)
        tex=low.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;low.node_tree.nodes.active=tex
        images.append((image,tex,low,original.name))
    for f,i in zip(target.data.polygons,target_indices):f.material_index=i
    for f,i in zip(source.data.polygons,source_indices):f.material_index=i
    if 'MergedUV' in target.data.uv_layers:
        target.data.uv_layers.active=target.data.uv_layers['MergedUV'];target.data.uv_layers['MergedUV'].active_render=True
        source.data.uv_layers.active=source.data.uv_layers['MergedUV'];source.data.uv_layers['MergedUV'].active_render=True
    bpy.ops.object.select_all(action='DESELECT');source.select_set(True);target.select_set(True);bpy.context.view_layer.objects.active=target
    source.select_set(False)
    if len(original_materials)>1:
        for i in range(len(original_materials)):
            for f in target.data.polygons:f.select=f.material_index==i
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
    source.select_set(True)
    bpy.ops.object.bake(type='EMIT',use_selected_to_active=True,use_cage=False,cage_extrusion=.006,max_ray_distance=.015,margin=3)
    for image,tex,low,name in images:
        image.filepath_raw=str(folder/(tag+'_'+name+'.png'));image.file_format='PNG';image.save();image.pack()
        low.node_tree.links.new(tex.outputs['Color'],low.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        # Runtime exporter identifies the semantic material by its stable prefix.
        low['source_material']=name
    source.hide_render=True
