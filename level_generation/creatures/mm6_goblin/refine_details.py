"""Refine the goblin's scowl and transfer an aligned, reviewed hand-detail image onto the actual posed surface."""
import bpy
import json
import math
import sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import look_at
SCENE='MM6 Goblin detail studio'

def project_detail(scene,skin,label,position,target,scale):
    camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=scale
    camera.location=position;look_at(camera,target);bpy.context.view_layer.update()
    evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=evaluated.to_mesh()
    count=len(skin.data.vertices);assert len(posed.vertices)==count,'Projection requires unchanged skin vertex ordering'
    coords=np.empty(count*3,dtype=np.float32);posed.vertices.foreach_get('co',coords)
    normals=np.empty(count*3,dtype=np.float32);posed.vertices.foreach_get('normal',normals)
    rest=np.empty(count*3,dtype=np.float32);skin.data.vertices.foreach_get('co',rest)
    indices=np.empty(len(skin.data.loops),dtype=np.int32);skin.data.loops.foreach_get('vertex_index',indices)
    evaluated.to_mesh_clear();coords=coords.reshape(-1,3);normals=normals.reshape(-1,3);rest=rest.reshape(-1,3)
    matrix=np.array(camera.matrix_world.inverted() @ skin.matrix_world)
    local=coords @ matrix[:3,:3].T+matrix[:3,3]
    projected=(.5+local[:,:2]/scale).astype(np.float32)
    direction=np.array((camera.location-Vector(target)).normalized())
    facing=np.maximum(0,normals @ direction)**.8;x=rest[:,0];z=rest[:,2]
    if label=='hand':region=np.clip((x-.32)/.04,0,1)*np.clip((.982-z)/.035,0,1)
    elif label=='torso':
        region=np.clip((.28-np.abs(x))/.04,0,1)*np.clip((z-1.035)/.045,0,1)*np.clip((1.595-z)/.035,0,1)
    else:region=np.clip((.175-z)/.040,0,1)*np.clip((.28-np.abs(x))/.04,0,1)
    uv=skin.data.uv_layers.new(name=label.title()+' restored projection')
    uv.data.foreach_set('uv',projected[indices].reshape(-1))
    mask=skin.data.color_attributes.new(name=label.title()+' reference blend',type='FLOAT_COLOR',domain='CORNER')
    colors=np.ones((len(indices),4),dtype=np.float32);colors[:,:3]=(.88*region*facing)[indices,None]
    mask.data.foreach_set('color',colors.reshape(-1))
    material=skin.data.materials[0];n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF')
    previous=bs.inputs['Base Color'].links[0].from_socket
    image=n.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(ROOT/f'textures/{label}_surface.png'),check_existing=True)
    image.image.pack();image.extension='EXTEND'
    coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;l.new(coord.outputs[0],image.inputs[0])
    region=n.new('ShaderNodeVertexColor');region.layer_name=mask.name
    confidence=n.new('ShaderNodeTexImage');confidence.image=bpy.data.images.load(str(ROOT/f'textures/{label}_surface_confidence.png'),check_existing=True)
    confidence.image.colorspace_settings.name='Non-Color';confidence.image.pack();l.new(coord.outputs[0],confidence.inputs[0])
    factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(region.outputs[0],factor.inputs[0])
    l.new(confidence.outputs['Color'],factor.inputs[1])
    mix=n.new('ShaderNodeMixRGB');l.new(factor.outputs[0],mix.inputs[0]);l.new(previous,mix.inputs[1])
    l.new(image.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    return {'part':label,'camera':list(position),'target':list(target),'orthographic_scale':scale,'uv':uv.name,
        'input':f'textures/{label}_surface.png','pose':'Standing frame 1','scope':'Reference pigment only; geometry and rig remain real 3D'}

def build():
    assert bpy.data.scenes.get(SCENE) is None,'Archive the prior detail scene before reapplying reference-dependent changes'
    bpy.context.window.scene=bpy.data.scenes['MM6 Goblin surface studio'];bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE
    for obj in scene.objects:
        if obj.type!='MESH':continue
        if obj.name.startswith('Goblin head | continuous sculpt'):
            for vertex in obj.data.vertices:
                x,y,z=vertex.co
                relief=.010*math.exp(-((abs(x)-.050)/.035)**2)*math.exp(-((z-1.759)/.013)**2)
                vertex.co.y-=relief*max(0,min(1,(-.035-y)/.035))
        elif obj.name.startswith('Eyeball'):
            for vertex in obj.data.vertices:vertex.co.z*=.80
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions['Standing']
    scene.frame_set(1);camera=scene.camera
    scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    bpy.context.view_layer.update()
    skin=next(o for o in scene.objects if o.name.startswith('Goblin body | connected skin'))
    material=skin.data.materials[0].copy();skin.data.materials[0]=material
    projections=[]
    for args in [('hand',(1,-2,1),(.42,-.06,.85),.45),('torso',(-.7,-2,1.28),(0,0,1.25),.72),
        ('feet',(-.7,-2,.5),(0,-.06,.15),.56)]:projections.append(project_detail(scene,skin,*args))
    (ROOT/'details').mkdir(exist_ok=True)
    (ROOT/'details/projection_manifest.json').write_text(json.dumps(projections,indent=2)+'\n')
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    bpy.data.libraries.write(str(ROOT/'details/detail_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    for name,position,target,scale in [('head',(-.6,-2,1.70),(0,0,1.68),.58),
        ('hand_match',(1,-2,1),(.42,-.06,.85),.45),('hand_side',(2,-.1,.95),(.42,-.06,.85),.45),
        ('torso',(-.7,-2,1.28),(0,0,1.25),.72),('feet',(-.7,-2,.5),(0,-.06,.15),.56),
        ('full_front',(0,-5,1),(0,0,1),2.16),('full_oblique',(-3,-4,1),(0,0,1),2.16),
        ('full_back',(0,5,1),(0,0,1),2.16)]:
        camera.location=position;look_at(camera,target);camera.data.ortho_scale=scale
        scene.render.filepath=str(ROOT/'review'/f'detail_v2_{name}.png');bpy.ops.render.render(write_still=True)
    print('Detail candidate rendered in matched and oblique views; assess projection and scowl before accepting')

if __name__=='__main__':build()
