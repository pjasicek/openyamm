import bpy, json, sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'master_motion.blend'))
rig=bpy.data.objects['Lizardman_Rig'];body=bpy.data.objects['Lizardman_Body'];sc=bpy.context.scene
rig.animation_data.action=None
for track in rig.animation_data.nla_tracks:track.mute=True
for bone in rig.pose.bones:bone.matrix_basis.identity()
bpy.context.view_layer.update()

def material(name,label):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=False
    m['openyamm_specular']=1.0;m['openyamm_specular_mask']=True
    nt=m.node_tree;bsdf=nt.nodes.get('Principled BSDF')
    def tex(file,space):
        n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/file));n.image.colorspace_settings.name=space;return n
    nt.links.new(tex(label+'_basecolor.png','sRGB').outputs['Color'],bsdf.inputs['Base Color'])
    n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.7
    nt.links.new(tex(label+'_normal.png','Non-Color').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bsdf.inputs['Normal'])
    sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex(label+'_mr.png','Non-Color').outputs['Color'],sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
    return m
body.data.materials.clear()
for m in [material('Lizardman_A','Body'),material('LizardmanHead_A','Head')]:body.data.materials.append(m)
flags=np.zeros(len(body.data.polygons),np.int32);body.data.attributes['head'].data.foreach_get('value',flags)
body.data.polygons.foreach_set('material_index',flags)

from mathutils import Vector
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=720;sc.render.resolution_y=720
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];sc.frame_set(0)
sc.camera.location=(0,-5,.85);sc.camera.rotation_euler=(Vector((0,0,.85))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=2.5
sc.render.filepath=str(P/'review/full_detail_before_reduction.png');bpy.ops.render.render(write_still=True)
