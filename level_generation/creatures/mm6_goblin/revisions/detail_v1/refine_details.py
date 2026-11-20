"""Refine the goblin's scowl and transfer an aligned, reviewed hand-detail image onto the actual posed surface."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import look_at
SCENE='MM6 Goblin detail studio'

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
    camera.data.type='ORTHO';camera.data.ortho_scale=.45;camera.location=(1,-2,1);look_at(camera,(.42,-.06,.85))
    scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    bpy.context.view_layer.update()
    skin=next(o for o in scene.objects if o.name.startswith('Goblin body | connected skin'))
    evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=evaluated.to_mesh()
    uv=skin.data.uv_layers.new(name='Hand restored projection')
    mask=skin.data.color_attributes.new(name='Hand reference blend',type='FLOAT_COLOR',domain='CORNER')
    direction=(camera.location-Vector((.42,-.06,.85))).normalized()
    # Cache evaluated positions/normals before writing source attributes. Vertex ordering is unchanged by skinning.
    projected=[];weights=[]
    for source,vertex in zip(skin.data.vertices,posed.vertices):
        world=skin.matrix_world @ vertex.co
        point=world_to_camera_view(scene,camera,world);projected.append((point.x,point.y))
        x,y,z=source.co
        region=max(0,min(1,(x-.32)/.04))*max(0,min(1,(.982-z)/.035))
        facing=max(0,vertex.normal.dot(direction))**.8
        weights.append(.88*region*facing)
    evaluated.to_mesh_clear()
    for loop in skin.data.loops:
        uv.data[loop.index].uv=projected[loop.vertex_index]
        w=weights[loop.vertex_index];mask.data[loop.index].color=(w,w,w,1)
    material=skin.data.materials[0].copy();skin.data.materials[0]=material
    n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF')
    previous=bs.inputs['Base Color'].links[0].from_socket
    image=n.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(ROOT/'textures/hand_surface.png'),check_existing=True)
    image.image.pack();image.extension='EXTEND'
    coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;l.new(coord.outputs[0],image.inputs[0])
    region=n.new('ShaderNodeVertexColor');region.layer_name=mask.name
    confidence=n.new('ShaderNodeTexImage');confidence.image=bpy.data.images.load(str(ROOT/'textures/hand_surface_confidence.png'),check_existing=True)
    confidence.image.colorspace_settings.name='Non-Color';confidence.image.pack();l.new(coord.outputs[0],confidence.inputs[0])
    factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(region.outputs[0],factor.inputs[0])
    l.new(confidence.outputs['Color'],factor.inputs[1])
    mix=n.new('ShaderNodeMixRGB');l.new(factor.outputs[0],mix.inputs[0]);l.new(previous,mix.inputs[1])
    l.new(image.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    (ROOT/'details').mkdir(exist_ok=True)
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    bpy.data.libraries.write(str(ROOT/'details/detail_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    for name,position,target,scale in [('head',(-.6,-2,1.70),(0,0,1.68),.58),
        ('hand_match',(1,-2,1),(.42,-.06,.85),.45),('hand_side',(2,-.1,.95),(.42,-.06,.85),.45),
        ('full_front',(0,-5,1),(0,0,1),2.16),('full_oblique',(-3,-4,1),(0,0,1),2.16)]:
        camera.location=position;look_at(camera,target);camera.data.ortho_scale=scale
        scene.render.filepath=str(ROOT/'review'/f'detail_v1_{name}.png');bpy.ops.render.render(write_still=True)
    print('Detail candidate rendered in matched and oblique views; assess projection and scowl before accepting')

if __name__=='__main__':build()
