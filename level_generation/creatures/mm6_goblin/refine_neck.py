"""Join the sculpted head into the body and smooth the exposed neck seam in a retained candidate scene."""
import bpy
import json
import sys
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import active,apply
from render_export_review import build as render_review
from prepare_export_mesh import freeze_coordinates,freeze_material

SCENE='MM6 Goblin neck studio'

def build():
    assert bpy.data.scenes.get(SCENE) is None
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    bpy.context.window.scene=bpy.data.scenes[manifest['scene']];bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
    body=next(o for o in scene.objects if o.name.startswith('Goblin body | connected skin'))
    head=next(o for o in scene.objects if o.name.startswith('Goblin head | continuous sculpt'))
    for obj in [body,head]:
        points=[obj.matrix_world @ v.co for v in obj.data.vertices]
        low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
        span=Vector(tuple(max(p[i] for p in points)-low[i] for i in range(3)))
        freeze_coordinates(obj)
        attr=obj.data.attributes.new(name='NeckRestPosition',type='FLOAT_VECTOR',domain='POINT')
        for vertex in obj.data.vertices:attr.data[vertex.index].vector=obj.matrix_world @ vertex.co
        for slot in obj.material_slots:
            slot.material=slot.material.copy();freeze_material(slot.material)
            # Boolean union does not reliably transfer the operand's POINT-domain generated coordinates.
            # Recover each material's original normalized coordinates from a common explicit rest position.
            n=slot.material.node_tree.nodes;l=slot.material.node_tree.links
            pos=n.new('ShaderNodeAttribute');pos.attribute_name='NeckRestPosition'
            subtract=n.new('ShaderNodeVectorMath');subtract.operation='SUBTRACT';subtract.inputs[1].default_value=low
            divide=n.new('ShaderNodeVectorMath');divide.operation='DIVIDE';divide.inputs[1].default_value=span
            l.new(pos.outputs['Vector'],subtract.inputs[0]);l.new(subtract.outputs[0],divide.inputs[0])
            for node in list(n):
                if node.type=='ATTRIBUTE' and node.attribute_name=='SourceGenerated':
                    for link in list(node.outputs['Vector'].links):l.new(divide.outputs[0],link.to_socket)
    # Boolean deform data uses group indices. Match both group layouts before creating intersection vertices.
    if body.vertex_groups.get('head') is None:body.vertex_groups.new(name='head')
    head.vertex_groups.clear()
    for group in body.vertex_groups:head.vertex_groups.new(name=group.name)
    head.vertex_groups['head'].add(list(range(len(head.data.vertices))),1,'REPLACE')
    head_material=head.data.materials[0]
    body.data.materials.append(head_material)
    head.data.materials.clear()
    for material in body.data.materials:head.data.materials.append(material)
    for polygon in head.data.polygons:polygon.material_index=len(body.data.materials)-1
    active(body)
    boolean=body.modifiers.new('Continuous neck union','BOOLEAN');boolean.operation='UNION'
    boolean.solver='EXACT';boolean.object=head
    while body.modifiers.find(boolean.name)>0:bpy.ops.object.modifier_move_up(modifier=boolean.name)
    apply(body,boolean)
    bpy.data.objects.remove(head,do_unlink=True)
    # Concentrate smoothing behind the jaw; retain the front chin and all facial relief.
    group=body.vertex_groups.new(name='Neck surface polish');count=0
    for vertex in body.data.vertices:
        p=body.matrix_world @ vertex.co
        z=max(0,1-abs(p.z-1.55)/.09)
        back=max(0,min(1,(p.y+.015)/.045))
        weight=z*back
        if weight>0:group.add([vertex.index],weight,'REPLACE');count+=1
    smooth=body.modifiers.new('Smooth neck intersection','SMOOTH');smooth.vertex_group=group.name
    smooth.factor=1.;smooth.iterations=18
    while body.modifiers.find(smooth.name)>0:bpy.ops.object.modifier_move_up(modifier=smooth.name)
    group_name=group.name
    apply(body,smooth);body.vertex_groups.remove(body.vertex_groups[group_name])
    rest_attr=body.data.attributes['NeckRestPosition']
    for vertex in body.data.vertices:rest_attr.data[vertex.index].vector=body.matrix_world @ vertex.co
    blend_attr=body.data.attributes.new(name='Neck pigment transition',type='FLOAT',domain='POINT')
    for vertex in body.data.vertices:
        p=body.matrix_world @ vertex.co
        band=max(0,min(1,(p.z-1.42)/.06,(1.65-p.z)/.07))
        back=max(0,min(1,(p.y+.025)/.045))
        blend_attr.data[vertex.index].value=band*back
    for material in body.data.materials:
        n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF')
        original=bs.inputs['Base Color'].links[0].from_socket
        pos=n.new('ShaderNodeAttribute');pos.attribute_name='NeckRestPosition'
        factor=n.new('ShaderNodeAttribute');factor.attribute_name='Neck pigment transition'
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=160
        noise.inputs['Detail'].default_value=3;l.new(pos.outputs['Vector'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.036,.05,.015,1)
        ramp.color_ramp.elements[1].color=(.08,.11,.032,1);l.new(noise.outputs['Fac'],ramp.inputs[0])
        mix=n.new('ShaderNodeMixRGB');l.new(factor.outputs['Fac'],mix.inputs[0])
        l.new(original,mix.inputs[1]);l.new(ramp.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
    # Head remains rigid above the jaw; the transition receives continuous neck/head weights.
    for vertex in body.data.vertices:
        p=body.matrix_world @ vertex.co
        if p.z<1.48 or abs(p.x)>.20:continue
        blend=max(0,min(1,(p.z-1.48)/.14));blend=blend*blend*(3-2*blend)
        for membership in list(vertex.groups):body.vertex_groups[membership.group].remove([vertex.index])
        body.vertex_groups['head'].add([vertex.index],blend,'REPLACE')
        if blend<1:body.vertex_groups['neck'].add([vertex.index],1-blend,'REPLACE')
    rig.data.pose_position='POSE';scene.frame_set(1)
    out=ROOT/'neck';out.mkdir(exist_ok=True)
    report={'scene':SCENE,'vertices':len(body.data.vertices),'polished_vertices':count,
        'status':'Candidate union; inspect material continuity, topology and animated neck before accepting'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    bpy.data.libraries.write(str(out/'neck_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    render_review(SCENE,'neck_v3',['neck_back','head','front','attack','corpse'])
    print(json.dumps(report))

if __name__=='__main__':build()
