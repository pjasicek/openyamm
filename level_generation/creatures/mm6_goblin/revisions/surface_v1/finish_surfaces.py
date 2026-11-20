"""Reference-based surface finishing in an isolated copy of the animated goblin; Blender MCP entry."""
import bpy
import math
import json
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import look_at
SCENE='MM6 Goblin surface studio'

def texture(nodes,path,uv=None):
    node=nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ROOT/path),check_existing=True)
    node.image.pack()
    return node

def multiply(nodes,links,a,b):
    node=nodes.new('ShaderNodeMath');node.operation='MULTIPLY'
    links.new(a,node.inputs[0]);links.new(b,node.inputs[1]);return node.outputs[0]

def fade(value,low,high,width=.03):
    return max(0,min(1,(value-low)/width))*max(0,min(1,(high-value)/width))

def finish_body(obj):
    mesh=obj.data;uv=mesh.uv_layers.new(name='Back reference projection')
    front=mesh.color_attributes.new(name='Front skin region',type='FLOAT_COLOR',domain='CORNER')
    back=mesh.color_attributes.new(name='Back skin region',type='FLOAT_COLOR',domain='CORNER')
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index];x,y,z=v.co;ax=abs(x)
        uv.data[loop.index].uv=((1460-367*x)/1672,1-(797.4-370*z)/941)
        region=0.
        if ax<.235:region=max(region,fade(z,1.05,1.58))
        if ax>.225:region=max(region,fade(z,1.185,1.435))
        if ax<.245:region=max(region,fade(z,.505,.95))
        for attr,normal in [(front,-v.normal.y),(back,v.normal.y)]:
            weight=.88*region*max(0,normal)**.65
            attr.data[loop.index].color=(weight,weight,weight,1)
    mat=mesh.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    base=next(node for node in n if node.type=='MIX_RGB' and node.blend_type=='MULTIPLY').outputs[0]
    for view,uv_name,attr_name in [('Front','Body reference projection','Front skin region'),
        ('Back','Back reference projection','Back skin region')]:
        coord=n.new('ShaderNodeUVMap');coord.uv_map=uv_name
        image=texture(n,'reference_restoration/turnaround_v1.png');l.new(coord.outputs[0],image.inputs[0])
        confidence=texture(n,'textures/restoration_skin_confidence.png');confidence.image.colorspace_settings.name='Non-Color'
        l.new(coord.outputs[0],confidence.inputs[0])
        region=n.new('ShaderNodeVertexColor');region.layer_name=attr_name
        factor=multiply(n,l,confidence.outputs['Color'],region.outputs['Color'])
        mix=n.new('ShaderNodeMixRGB');mix.name=view+' restored skin detail'
        l.new(factor,mix.inputs[0]);l.new(base,mix.inputs[1]);l.new(image.outputs['Color'],mix.inputs[2]);base=mix.outputs[0]
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.78,.83,.72,1);l.new(base,tint.inputs[1]);l.new(tint.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.66;bs.inputs['Specular IOR Level'].default_value=.26
    for node in n:
        if node.type=='BUMP':node.inputs['Strength'].default_value=.15;node.inputs['Distance'].default_value=.0004

def iron(mat):
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    coord=n.new('ShaderNodeAttribute');coord.attribute_name='SculptPosition'
    scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=2.8
    l.new(coord.outputs['Vector'],scale.inputs[0])
    image=texture(n,'textures/worn_iron.png');image.projection='BOX';image.projection_blend=.20
    l.new(scale.outputs[0],image.inputs[0]);l.new(image.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value=.78;bs.inputs['Roughness'].default_value=.52
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00065
    l.new(image.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])

def leather_wear(obj):
    attr=obj.data.color_attributes.new(name='Leather edge wear',type='FLOAT_COLOR',domain='CORNER')
    index=int(obj.name.split('Leather skirt strip ')[1][:2]);angle=index*2*math.pi/22
    length=.205+.026*math.sin(index*2.7)+.018*math.cos(index*1.3)
    for loop in obj.data.loops:
        x,y,z=obj.data.vertices[loop.vertex_index].co;t=(.998-z)/length
        a=math.atan2(x/(.176+.023*t),-y/(.125+.025*t))
        delta=(a-angle+math.pi)%(2*math.pi)-math.pi
        edge=max(0,min(1,(abs(delta)-.094)/.027))
        hem=max(0,min(1,(t-.94)/.055))
        wear=max(edge,hem)*(.45+.20*math.sin(z*270+index*2.1))
        attr.data[loop.index].color=(wear,wear,wear,1)

def build():
    assert bpy.data.scenes.get(SCENE) is None,'Inspect and archive the current surface scene before rebuilding'
    bpy.context.window.scene=bpy.data.scenes['MM6 Goblin animation studio'];bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE;materials={}
    # Explicit single-user materials preserve all upstream authoring and animation checkpoints.
    for obj in scene.objects:
        if obj.type!='MESH':continue
        for slot in obj.material_slots:
            old=slot.material
            if old not in materials:materials[old]=old.copy()
            slot.material=materials[old]
        if obj.name.startswith('Leather skirt strip '):leather_wear(obj)
    for mat in materials.values():
        n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
        if 'skin' in mat.name.lower() or 'ear olive' in mat.name:
            bs.inputs['Roughness'].default_value=.64;bs.inputs['Specular IOR Level'].default_value=.26
        if mat.name.startswith('Worn dark iron'):iron(mat)
        if mat.name.startswith('Brown leather'):
            base=bs.inputs['Base Color'].links[0].from_socket
            region=n.new('ShaderNodeVertexColor');region.layer_name='Leather edge wear'
            mix=n.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(.10,.039,.014,1)
            l.new(region.outputs['Color'],mix.inputs[0]);l.new(base,mix.inputs[1]);l.new(mix.outputs[0],bs.inputs['Base Color'])
            bs.inputs['Roughness'].default_value=.73
        if mat.name.startswith(('Aged brass fittings','Goblin worn brass')):bs.inputs['Roughness'].default_value=.49
    skin=next(o for o in scene.objects if o.name.startswith('Goblin body | connected skin'));finish_body(skin)
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions['Standing']
    scene.frame_set(1);camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.16
    scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.cycles.samples=32
    (ROOT/'surfaces').mkdir(exist_ok=True)
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    bpy.data.libraries.write(str(ROOT/'surfaces/surface_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    for angle,label in [(0,'front'),(45,'three_quarter'),(90,'profile'),(180,'back')]:
        a=-math.radians(angle);camera.location=(5*math.sin(a),-5*math.cos(a),1.0);look_at(camera,(0,0,1.0))
        scene.render.filepath=str(ROOT/'review'/f'surface_v1_{label}.png');bpy.ops.render.render(write_still=True)
    # Detail views use the same neutral light rig, so material and attachment differences remain visible.
    for name,position,target,scale in [('head',(-.6,-2,1.70),(0,0,1.68),.58),
        ('torso',(-.7,-2,1.28),(0,0,1.25),.72),('hand',(1,-2,1.0),(.42,-.06,.85),.45),
        ('feet',(-.7,-2,.5),(0,-.06,.15),.56)]:
        camera.location=position;look_at(camera,target);camera.data.ortho_scale=scale
        scene.render.resolution_x=800;scene.render.resolution_y=800
        scene.render.filepath=str(ROOT/'review'/f'surface_v1_detail_{name}.png');bpy.ops.render.render(write_still=True)
    camera.location=(0,-5,1);look_at(camera,(0,0,1));camera.data.ortho_scale=2.16
    print('Surface revision 1: four full views and four close-ups rendered; material acceptance pending')

if __name__=='__main__':build()
