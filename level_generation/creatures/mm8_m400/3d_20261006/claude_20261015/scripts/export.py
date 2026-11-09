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
# Protect the face, fingers and feet while reducing the torso and flat garment surfaces.
protected=body.vertex_groups.new(name='_protect');names=[g.name for g in body.vertex_groups]
for v in body.data.vertices:
    w=sum(g.weight for g in v.groups if any(k in names[g.group] for k in ['Head','Hand','Thumb','Digit','Foot','Toe']))
    if w>.3 or (.60<v.co.z<1.08 and abs(v.co.x)<.17 and v.co.y<0):protected.add([v.index],1,'REPLACE')
bpy.context.view_layer.objects.active=body
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
before=len(body.data.polygons)
m=body.modifiers.new('BodyBudget','DECIMATE');m.ratio=.72;m.vertex_group=protected.name;m.invert_vertex_group=True
bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
body.vertex_groups.remove(body.vertex_groups['_protect'])
bpy.ops.object.vertex_group_limit_total(limit=8)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
body.data.validate(verbose=True)
body.data.update()
print('REDUCED',before,'to',len(body.data.polygons),flush=True)
for attr in ['head']:
    if attr in body.data.attributes:body.data.attributes.remove(body.data.attributes[attr])
for obj in list(bpy.data.objects):
    if obj.type not in ['MESH','ARMATURE','LIGHT','CAMERA']:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.file.pack_all();(P/'delivery').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'delivery/mm8_lizardman_peasant.blend'))
# Bake at 192 Hz so the exported linear interpolation preserves the curved source gait between frames.
# NLA export needs integer endpoints; build_runtime.py restores the walk's exact seconds.
for name in ['Standing','Walk','Hit','Fidget','Death','Corpse']:
    action=bpy.data.actions[name];factor=4*(50/49.6 if name=='Walk' else 1)
    end=float(action.frame_range[1])*factor
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:
                        key.co.x*=factor;key.handle_left.x*=factor;key.handle_right.x*=factor
                    fc.update()
    strip=next(t for t in rig.animation_data.nla_tracks if t.name==name).strips[0]
    strip.action_frame_end=end;strip.frame_end=end
sc.render.fps=192

bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'delivery/export_raw.glb'),export_format='GLB',use_selection=True,
    export_animation_mode='NLA_TRACKS',export_frame_range=False,export_force_sampling=False,export_yup=True,
    export_all_influences=True,export_extras=True,export_attributes=False)
