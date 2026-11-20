"""Selected-to-active rebake of all runtime maps, including source detail in tangent-space normals."""
import bpy,bmesh,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
PREFIX={'Mep_A':'mep','MepHead_A':'mep_head','MepStaff_A':'mep_staff'}
def bake(target,mesh_name,level):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1
    with bpy.data.libraries.load(str(P/'work/textured.blend'),link=False) as (src,dst):dst.meshes=[mesh_name]
    source=bpy.data.objects.new('BakeHigh',dst.meshes[0]);bpy.context.collection.objects.link(source)
    if 'MergedUV' in source.data.uv_layers:
        source.data.uv_layers.active=source.data.uv_layers['MergedUV'];source.data.uv_layers['MergedUV'].active_render=True
    if 'MergedUV' in target.data.uv_layers:
        target.data.uv_layers.active=target.data.uv_layers['MergedUV'];target.data.uv_layers['MergedUV'].active_render=True
    folder=P/f'textures/lod{level}';folder.mkdir(exist_ok=True)
    size=[1024,1024,512,256][level];source_indices=[f.material_index for f in source.data.polygons];target_indices=[f.material_index for f in target.data.polygons]
    semantics=['Mep_A','MepHead_A'] if mesh_name=='Body' else ['MepStaff_A']
    source.data.materials.clear();target.data.materials.clear();pairs=[]
    def tex(nt,path,space):
        node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(path),check_existing=False);node.image.colorspace_settings.name=space;node.image.alpha_mode='CHANNEL_PACKED';return node
    for name in semantics:
        prefix=PREFIX[name]
        high=bpy.data.materials.new('BakeSource');high.use_nodes=True;source.data.materials.append(high);nt=high.node_tree;bs=nt.nodes.get('Principled BSDF')
        inputs={}
        for key,suffix,space in [('base','basecolor_1k','sRGB'),('orm','orm_1k','Non-Color'),('mask','region_mask','Non-Color')]:
            inputs[key]=tex(nt,P/f'textures/{prefix}_{suffix}.png',space)
        inputs['normal']=tex(nt,P/f'work/{prefix}_normal_gl.png','Non-Color')
        nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(inputs['normal'].outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        emit=nt.nodes.new('ShaderNodeEmission')
        stable=name if level==0 else name.replace('_A',f'_L{level}_A')
        old=bpy.data.materials.get(stable)
        if old:old.name=stable+'_unused'
        low=bpy.data.materials.new(stable);low.use_nodes=True;target.data.materials.append(low)
        pairs.append((name,prefix,high,low,inputs,emit))
    for f,i in zip(source.data.polygons,source_indices):f.material_index=i
    for f,i in zip(target.data.polygons,target_indices):f.material_index=i
    bpy.ops.object.select_all(action='DESELECT');target.select_set(True);bpy.context.view_layer.objects.active=target
    if mesh_name=='Body':
        # Face selection must be explicit: inherited vertex selection packed the whole body into the head atlas.
        bpy.context.tool_settings.mesh_select_mode=(False,False,True)
        for index in range(len(semantics)):
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
            for face in target.data.polygons:face.select=face.material_index==index
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
    source.select_set(True)
    bake_pairs=[(source,target)];temporary=[];target_visibility=target.hide_render
    if mesh_name=='Body' and level>0:
        # Bake each clothing/anatomy piece separately so rays cannot paint the coat onto the sash or skin.
        def subset(obj,piece):
            clone=bpy.data.objects.new('BakePiece',obj.data.copy());bpy.context.collection.objects.link(clone)
            bm=bmesh.new();bm.from_mesh(clone.data);attribute=bm.verts.layers.int['piece']
            bpy.ops.object.select_all(action='DESELECT')
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[attribute]!=piece],context='VERTS')
            bm.to_mesh(clone.data);bm.free();clone.hide_render=True;temporary.append(clone);return clone
        piece_ids=[x.value for x in target.data.attributes['piece'].data]
        ids={piece_ids[f.vertices[0]] for f in target.data.polygons}
        source_ids=set(x.value for x in source.data.attributes['piece'].data);assert ids<=source_ids
        bake_pairs=[(subset(source,i),subset(target,i)) for i in sorted(ids)]
        source.hide_render=True;target.hide_render=True
    results={}
    for channel in ['base','orm','mask','mask_alpha','normal']:
        images=[]
        for name,prefix,high,low,inputs,emit in pairs:
            nt=high.node_tree
            if channel=='normal':nt.links.new(nt.nodes.get('Principled BSDF').outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
            else:
                nt.links.new(inputs['mask' if channel=='mask_alpha' else channel].outputs['Alpha' if channel=='mask_alpha' else 'Color'],emit.inputs['Color'])
                nt.links.new(emit.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
            image=bpy.data.images.new(f'{prefix}_{channel}_lod{level}',width=size,height=size,alpha=False,float_buffer=False)
            image.colorspace_settings.name='sRGB' if channel=='base' else 'Non-Color'
            node=low.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;low.node_tree.nodes.active=node
            images.append((name,prefix,image,node,low))
        for high_part,low_part in bake_pairs:
            bpy.ops.object.select_all(action='DESELECT');high_part.hide_render=False;low_part.hide_render=False
            high_part.select_set(True);low_part.select_set(True);bpy.context.view_layer.objects.active=low_part
            bpy.ops.object.bake(type='NORMAL' if channel=='normal' else 'EMIT',normal_space='TANGENT',use_selected_to_active=True,use_clear=False,use_cage=False,cage_extrusion=(.075 if level else .006) if mesh_name=='Body' else .006,max_ray_distance=.16 if mesh_name=='Body' else .015,margin=max(2,round(size/350)))
            if temporary:high_part.hide_render=True;low_part.hide_render=True
        for name,prefix,image,node,low in images:
            results[name,channel]=(image,node)
            if channel not in ['mask','mask_alpha']:
                suffix={'base':'basecolor','orm':'orm','normal':'normal'}[channel];image.filepath_raw=str(folder/f'{prefix}_{suffix}.png');image.file_format='PNG';image.save();image.pack()
    for name,prefix,high,low,inputs,emit in pairs:
        rgb=results[name,'mask'][0];alpha=results[name,'mask_alpha'][0];c=np.empty(size*size*4,np.float32);a=c.copy();rgb.pixels.foreach_get(c);alpha.pixels.foreach_get(a);c=c.reshape(-1,4);c[:,3]=a.reshape(-1,4)[:,0]
        mask=bpy.data.images.new(prefix+'_mask',width=size,height=size,alpha=True);mask.colorspace_settings.name='Non-Color';mask.alpha_mode='CHANNEL_PACKED';mask.pixels.foreach_set(c.ravel());mask.filepath_raw=str(folder/f'{prefix}_region_mask.png');mask.file_format='PNG';mask.save()
        nt=low.node_tree;bs=nt.nodes.get('Principled BSDF');nt.links.new(results[name,'base'][1].outputs['Color'],bs.inputs['Base Color'])
        sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(results[name,'orm'][1].outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
        normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(results[name,'normal'][1].outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);nt.nodes.active=results[name,'base'][1]
    for obj in temporary:
        mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
    target.hide_render=target_visibility
    bpy.data.objects.remove(source,do_unlink=True)
    print('REBAKED_RUNTIME',mesh_name,level,size,flush=True)
