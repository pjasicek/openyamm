"""Bake source surface shading into portable GameUV textures, retaining the upstream source scene."""
import bpy
import json
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SIZE=4096
SCENE='MM6 Goblin baked studio'

def target_image(materials,name,color=False):
    image=bpy.data.images.new(name,width=SIZE,height=SIZE,alpha=True)
    image.colorspace_settings.name='sRGB' if color else 'Non-Color'
    image.generated_color=(0,0,0,0)
    for mat in materials:
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.name='Bake destination '+name
        mat.node_tree.nodes.active=node
    return image

def save_image(image,name):
    path=ROOT/'textures/baked'/name;path.parent.mkdir(exist_ok=True)
    image.filepath_raw=str(path);image.file_format='PNG';image.save();image.pack()

def region_color(name):
    if any(s in name.lower() for s in ['skin','ear olive','ear warm']):return (1,0,0,1)
    if 'leather' in name.lower():return (0,1,0,1)
    if 'brass' in name.lower():return (1,1,0,1)
    if any(s in name.lower() for s in ['iron','steel']):return (0,0,1,1)
    if any(s in name.lower() for s in ['teeth','claws']):return (1,0,1,1)
    if 'eye' in name.lower():return (0,1,1,1)
    return (0,0,0,1)

def emission_bake(materials,kind):
    saved=[]
    for mat in materials:
        n=mat.node_tree.nodes;l=mat.node_tree.links;out=next(n for n in n if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        original=out.inputs['Surface'].links[0].from_socket
        emission=n.new('ShaderNodeEmission')
        if kind=='regions':emission.inputs['Color'].default_value=region_color(mat.name)
        else:
            bs=n.get('Principled BSDF');value=bs.inputs['Base Color' if kind=='base_color' else 'Metallic']
            if value.is_linked:l.new(value.links[0].from_socket,emission.inputs['Color'])
            elif kind=='base_color':emission.inputs['Color'].default_value=value.default_value
            else:emission.inputs['Color'].default_value=(value.default_value,)*3+(1,)
        l.new(emission.outputs[0],out.inputs['Surface']);saved.append((mat,out,original,emission))
    try:bpy.ops.object.bake(type='EMIT')
    finally:
        for mat,out,original,emission in saved:
            mat.node_tree.links.new(original,out.inputs['Surface']);mat.node_tree.nodes.remove(emission)

def build():
    assert bpy.data.scenes.get(SCENE) is None,'Archive the existing bake before repeating source-dependent baking'
    bpy.context.window.scene=bpy.data.scenes['MM6 Goblin export studio'];bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
    mesh=next(o for o in scene.objects if o.type=='MESH');bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
    materials=[]
    for slot in mesh.material_slots:slot.material=slot.material.copy();materials.append(slot.material)
    scene.render.engine='CYCLES';scene.cycles.samples=16
    scene.render.bake.use_selected_to_active=False;scene.render.bake.use_clear=True;scene.render.bake.margin=16
    scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
    images={}
    for name,kind in [('base_color','EMIT'),('normal','NORMAL'),('roughness','ROUGHNESS'),('metallic','EMIT'),('regions','EMIT')]:
        (ROOT/'bake_job_status.txt').write_text('RUNNING bake '+name)
        image=target_image(materials,'Goblin baked '+name,color=name in {'base_color','regions'})
        if name in {'base_color','metallic','regions'}:emission_bake(materials,name)
        else:bpy.ops.object.bake(type=kind)
        save_image(image,'goblin_'+name+'.png');images[name]=image
    # glTF's conventional packed occlusion/roughness/metallic texture. No baked AO is invented here.
    count=SIZE*SIZE;rgba=np.ones((count,4),dtype=np.float32);buffer=np.empty(count*4,dtype=np.float32)
    images['roughness'].pixels.foreach_get(buffer);rgba[:,1]=buffer.reshape(-1,4)[:,0]
    images['metallic'].pixels.foreach_get(buffer);rgba[:,2]=buffer.reshape(-1,4)[:,0]
    orm=bpy.data.images.new('Goblin packed ORM',width=SIZE,height=SIZE,alpha=True)
    orm.colorspace_settings.name='Non-Color';orm.pixels.foreach_set(rgba.reshape(-1));save_image(orm,'goblin_orm.png')
    # Shared atlases with per-region surface constants preserve skin/eye/metal response for the parity review.
    for index,source in enumerate(materials):
        material=bpy.data.materials.new('Portable '+source.name);material.use_nodes=True
        n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF')
        original=source.node_tree.nodes.get('Principled BSDF')
        for key in ['IOR','Specular IOR Level','Subsurface Weight','Subsurface Radius','Coat Weight','Coat Roughness']:
            bs.inputs[key].default_value=original.inputs[key].default_value
        uv=n.new('ShaderNodeUVMap');uv.uv_map='GameUV'
        def tex(image):
            node=n.new('ShaderNodeTexImage');node.image=image;l.new(uv.outputs[0],node.inputs[0]);return node
        base=tex(images['base_color']);l.new(base.outputs['Color'],bs.inputs['Base Color'])
        normal=tex(images['normal']);convert=n.new('ShaderNodeNormalMap');convert.uv_map='GameUV'
        l.new(normal.outputs['Color'],convert.inputs['Color']);l.new(convert.outputs[0],bs.inputs['Normal'])
        packed=tex(orm);separate=n.new('ShaderNodeSeparateColor');separate.mode='RGB'
        l.new(packed.outputs['Color'],separate.inputs[0]);l.new(separate.outputs['Green'],bs.inputs['Roughness'])
        l.new(separate.outputs['Blue'],bs.inputs['Metallic']);mesh.data.materials[index]=material
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    rig.animation_data.action=bpy.data.actions[manifest['clips']['Standing']['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    rig.data.pose_position='POSE';scene.frame_set(1)
    bpy.data.libraries.write(str(ROOT/'export_work/baked_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    report={'resolution':[SIZE,SIZE],'uv':'GameUV','portable_textures':['goblin_base_color.png','goblin_normal.png','goblin_orm.png'],
        'regions':'goblin_regions.png: red skin, green leather, blue iron/steel, yellow brass, magenta horn/teeth, cyan eyes, black cavities',
        'status':'Baked candidate; compare source and baked close views before accepting or exporting final assets'}
    (ROOT/'export_work/bake_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'bake_job_status.txt').write_text('COMPLETE candidate bake; visual parity pending')
    print(json.dumps(report))

if __name__=='__main__':build()
