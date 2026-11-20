"""Apply the graded maps to the retained rig, save an editable packed master and export the actual clips."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
release=float(scene['attack_impact_seconds'])*30-.01;scene.frame_set(int(release),subframe=release%1)
am=rig.pose.bones['Arrow'].matrix.copy();tip=am.translation+am.to_3x3().col[2].normalized()*float(scene['arrow_length'])
socket_local=rig.pose.bones['Bow'].matrix.inverted()@tip
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
socket=rig.data.edit_bones['Socket_Arrow'];M=rig.data.edit_bones['Bow'].matrix@__import__('mathutils').Matrix.Translation(socket_local)
socket.head=M.translation;socket.tail=socket.head+M.to_3x3().col[1]*.1;socket.align_roll(M.to_3x3().col[2])
bpy.ops.object.mode_set(mode='OBJECT')
piece=np.array([x.value for x in me.attributes['piece'].data]);head=np.array([x.value for x in me.attributes['head'].data])
runtime=me.uv_layers.new(name='RuntimeUV');me.materials.clear()
for kind,suffix in [('body','Body'),('head','Head'),('bow','Bow')]:
    mat=bpy.data.materials.new('SkeletonArcher'+suffix+'_A');mat.use_nodes=True;me.materials.append(mat)
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;shader=nodes.get('Principled BSDF');shader.inputs['Metallic'].default_value=0
    maps={}
    for channel in ['basecolor','normal','orm']:
        img=bpy.data.images.load(str(P/f'textures/m628_{kind}_{channel}.png'),check_existing=True)
        if channel!='basecolor':img.colorspace_settings.name='Non-Color'
        tex=nodes.new('ShaderNodeTexImage');tex.image=img;uv=nodes.new('ShaderNodeUVMap');uv.uv_map='RuntimeUV';links.new(uv.outputs['UV'],tex.inputs['Vector']);maps[channel]=tex
    nodes.active=maps['basecolor'];links.new(maps['basecolor'].outputs['Color'],shader.inputs['Base Color'])
    normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.7;normal.uv_map='RuntimeUV';links.new(maps['normal'].outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    sep=nodes.new('ShaderNodeSeparateColor');links.new(maps['orm'].outputs['Color'],sep.inputs['Color'])
    links.new(sep.outputs['Green'],shader.inputs['Roughness']);links.new(sep.outputs['Blue'],shader.inputs['Metallic'])
for f in me.polygons:
    pid=piece[f.vertices[0]];slot=1 if head[f.index]else 2 if pid in[4000,4003,4004]else 0
    layer=me.uv_layers[['UVMap','HeadUV','BowUV'][slot]].data;f.material_index=slot
    for li in f.loop_indices:runtime.data[li].uv=layer[li].uv
me.uv_layers.active=runtime;runtime.active_render=True
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([tuple(v.co)for v in em.vertices]);ev.to_mesh_clear();bodyheight=float(np.ptp(co[piece<4000,2]));stride=[]
rig.animation_data.action=bpy.data.actions['Walking'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for f in np.linspace(0,24,97):
    scene.frame_set(int(f),subframe=float(f%1));stride.append([tuple(rig.pose.bones[f'B_{s}_Foot'].head)for s in 'LR'])
stride=float(np.mean(np.ptp(np.array(stride)[:,:,1],axis=0))*2)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.data.orphans_purge(do_recursive=True);bpy.ops.file.pack_all();(P/'export').mkdir(exist_ok=True)
info={'triangles':len(me.polygons),'bones':len(rig.data.bones),'maximum_influences':max(len(v.groups)for v in me.vertices),
    'standing_body_height_m':bodyheight,'stride_length_m':stride,'impact_seconds':float(scene['attack_impact_seconds']),
    'release_socket_bow_local':list(socket_local),
    'clips':{a.name:float(a.frame_range[1])/30 for a in bpy.data.actions}}
(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/m628_master.blend'))
# Export one active UV set and only the rigged character; the editable master retains all source UV layers.
for uv in list(me.uv_layers):
    if uv.name!='RuntimeUV':me.uv_layers.remove(uv)
for attr in list(me.attributes):
    if attr.name in ['piece','head','material_class']:me.attributes.remove(attr)
body.name=me.name='SkeletonArcher'
for o in bpy.data.objects:o.select_set(o in [rig,body])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m628_raw.glb'),use_selection=True,export_format='GLB',export_yup=True,
    export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=False,
    export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
    export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_image_format='AUTO')
# Neutral colour and detail review; runtime GPU captures provide the final lighting check.
common.workbench_clay(scene,textured=True)
for name,f in [('Standing',0),('Attack',25),('Death',16),('Dead',0)]:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(f)
    common.render_views(str(P/f'review/textured_{name}'),.65 if name in['Death','Dead']else 1.,4 if name in['Death','Dead']else 2.5,
        views=('front','left','back','three_quarter'),resolution=(800,500)if name in['Death','Dead']else(600,900))
print('EXPORT',info)
