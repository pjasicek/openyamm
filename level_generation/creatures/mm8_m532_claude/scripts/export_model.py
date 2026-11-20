"""Final materials and protected region reduction on the retained animated rig."""
from pathlib import Path
import bpy,json
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];T=P/'textures';(P/'export').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
b=bpy.data.objects['Body'];eq=bpy.data.objects['Equipment'];rig=bpy.data.objects['Rig'];me=b.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
me.materials.clear()
for name,prefix in [('Centaur','centaur'),('CentaurHead','centaur_head')]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False;mat['openyamm_specular']=1.;mat['openyamm_specular_mask']=True
    nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
    def tex(suffix,cs):
        n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/(prefix+suffix)));n.image.colorspace_settings.name=cs;return n
    bc=tex('_basecolor_1k.png','sRGB');nt.links.new(bc.outputs['Color'],bs.inputs['Base Color'])
    nm=tex('_normal_1k.png','Non-Color');normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nm.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    mr=tex('_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    # glTF leaves red unused; the runtime reads it as the declared specular mask.
    group=bpy.data.node_groups.new(name+' glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat');node=nt.nodes.new('ShaderNodeGroup');node.node_tree=group;nt.links.new(sep.outputs['Red'],node.inputs['Occlusion'])
    me.materials.append(mat)
uv=me.uv_layers.new(name='ExportUV')
for p in me.polygons:
    ishead=me.attributes['head'].data[p.index].value;p.material_index=ishead
    layer=me.uv_layers['HeadUV'if ishead else'UVMap']
    for li in p.loop_indices:
        uv.data[li].uv=layer.data[li].uv
        if not ishead:uv.data[li].uv.x*=1024/1152
for layer in list(me.uv_layers):
    if layer.name!='ExportUV':me.uv_layers.remove(layer)
me.uv_layers.active=uv;uv.active_render=True
# Face, fingers and the head/neck material seam retain their fitted density.
prot=b.vertex_groups.new(name='_protect');keys={g.index for g in b.vertex_groups if g.name in ('Head','Neck')or'Hand'in g.name or any(n in g.name for n in ('Thumb','Index','Middle','Ring','Pinky'))}
for v in me.vertices:
    if sum(g.weight for g in v.groups if g.group in keys)>.25:prot.add([v.index],1,'REPLACE')
for o in bpy.context.scene.objects:o.select_set(o==b)
bpy.context.view_layer.objects.active=b
before=len(me.polygons);mod=b.modifiers.new('RegionReduction','DECIMATE');mod.ratio=.78;mod.vertex_group=prot.name;mod.invert_vertex_group=True;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);b.vertex_groups.remove(b.vertex_groups['_protect'])
after=len(b.data.polygons)
eq.data.uv_layers.active.name='ExportUV'
x,y,w,h=json.loads((T/'texture_report.json').read_text())['props_rect_pixels']
for loop in eq.data.uv_layers.active.data:loop.uv=((x+loop.uv.x*w)/1152,1-(y+h)/1024+loop.uv.y*h/1024)
eq.data.materials.clear();eq.data.materials.append(me.materials[0])
for joint in ('Bow','Quiver'):
    mat=me.materials[0].copy();mat.name='Centaur'+joint;eq.data.materials.append(mat)
    gi=eq.vertex_groups[joint].index
    for face in eq.data.polygons:
        if all(any(g.group==gi and g.weight>.999 for g in eq.data.vertices[v].groups)for v in face.vertices):face.material_index=len(eq.data.materials)-1
for mat in eq.data.materials:mat.use_backface_culling=False
for o in bpy.context.scene.objects:o.select_set(o in (b,eq))
bpy.context.view_layer.objects.active=b;bpy.ops.object.join()
b.data.validate(verbose=True);b.data.update();
bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
# Bone-parented empties use Blender's tail offset; cancel it to put the launch socket at the nock head.
for name,bone,offset in [('Socket_BowRelease','StringNock',(0,0,0)),('Socket_CastPalm','RHand',(0,.13,0))]:
    o=bpy.data.objects.get(name)
    if o is None:o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o)
    o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;o.matrix_parent_inverse=Matrix.Identity(4)
    o.matrix_basis=Matrix.Translation(Vector(offset)-Vector((0,rig.data.bones[bone].length,0)))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
for o in bpy.context.scene.objects:o.select_set(o==b or o==rig or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active=rig
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/centaur_master.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_centaur_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
report={'body_before':before,'body_after':after,'equipment':696,'total':len(b.data.polygons),'max_influences':max(len(v.groups)for v in b.data.vertices),'bones':len(rig.data.bones)}
assert report['total']<15000 and report['max_influences']<=4
(P/'export/reduction.json').write_text(json.dumps(report,indent=2)+'\n');print('EXPORTED',report)
