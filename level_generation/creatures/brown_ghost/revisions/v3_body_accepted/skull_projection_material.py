"""Project restored frontal color onto a carved skull; fade to neutral bone on side/rear surfaces."""
import bpy
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')

def projected_skull_material(base):
    mat=base.copy();mat.name='Restored skull projected color'
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    principled=nodes.get('Principled BSDF')
    base_color=principled.inputs['Base Color'].links[0].from_socket
    image=bpy.data.images.load(str(ROOT/'reference_restoration/skull_detail_v1.png'),check_existing=True)
    image.pack()
    def math_node(operation,a,b=None):
        n=nodes.new('ShaderNodeMath');n.operation=operation
        for index,value in enumerate([a,b]):
            if value is None:continue
            if isinstance(value,(int,float)):n.inputs[index].default_value=value
            else:links.new(value,n.inputs[index])
        return n.outputs[0]
    def mix(a,b,factor):
        n=nodes.new('ShaderNodeMixRGB');links.new(factor,n.inputs[0]);links.new(a,n.inputs[1]);links.new(b,n.inputs[2])
        return n.outputs[0]
    def reference(uv_name):
        uv=nodes.new('ShaderNodeUVMap');uv.uv_map=uv_name
        tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND';links.new(uv.outputs['UV'],tex.inputs['Vector'])
        channels=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],channels.inputs['Color'])
        red,green,blue=channels.outputs['Red'],channels.outputs['Green'],channels.outputs['Blue']
        # Reject cyan background and purple cloth; retain bone and cavity shadow pixels.
        warm=math_node('MULTIPLY',math_node('GREATER_THAN',green,math_node('MULTIPLY',red,.52)),
                       math_node('LESS_THAN',green,math_node('MULTIPLY',red,1.08)))
        warm=math_node('MULTIPLY',warm,math_node('GREATER_THAN',red,.04))
        dark=math_node('LESS_THAN',math_node('MAXIMUM',math_node('MAXIMUM',red,green),blue),.07)
        color=mix(base_color,tex.outputs['Color'],math_node('MAXIMUM',warm,dark))
        separate=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],separate.inputs[0])
        return color,separate.outputs['X']
    front,u=reference('Procedural surface UV')
    side_uv=nodes.new('ShaderNodeUVMap');side_uv.uv_map='Skull profile projection'
    separate=nodes.new('ShaderNodeSeparateXYZ');links.new(side_uv.outputs['UV'],separate.inputs[0])
    # A second painted socket would conflict with the real cavity in side views.
    # Use the profile guide for geometry, and fade frontal color to bone on the sides.
    back=nodes.new('ShaderNodeMapRange');back.clamp=True;back.interpolation_type='SMOOTHERSTEP'
    links.new(separate.outputs['X'],back.inputs['Value'])
    back.inputs['From Min'].default_value=(1170-850*.02)/1402
    back.inputs['From Max'].default_value=(1170+850*.07)/1402
    back.inputs['To Min'].default_value=1;back.inputs['To Max'].default_value=0
    color=mix(front,base_color,back.outputs[0])
    links.new(color,principled.inputs['Base Color'])
    mat['source']='AI restored m242 skull_detail_v1.png; native sprite cross-checks remain authoritative'
    return mat
