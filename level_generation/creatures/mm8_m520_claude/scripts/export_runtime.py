"""Portable master with a separate, animated temporary boulder joint."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_texturing_weighted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
keep=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
with bpy.data.libraries.load(str(p/'work/motion_weighted.blend'),link=False) as (src,dst):
 assert set(keep).issubset(src.actions);dst.actions=keep
for a in bpy.data.actions:a.use_fake_user=True
for pb in rig.pose.bones:pb.matrix_basis.identity();pb.scale=(1,1,1)
bpy.context.view_layer.update();me=body.data;head=[v.value for v in me.attributes['head'].data]
for face in me.polygons:
 face.material_index=head[face.index]
 if head[face.index]:
  for li in face.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV']);me.uv_layers.active=me.uv_layers['UVMap']
def material(name,base,normal,mr):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bsdf=nt.nodes.get('Principled BSDF')
 def tex(path,cs):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(path));node.image.colorspace_settings.name=cs;return node
 colour=tex(base,'sRGB');nt.nodes.active=colour;nt.links.new(colour.outputs['Color'],bsdf.inputs['Base Color'])
 nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex(normal,'Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
 channels=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex(mr,'Non-Color').outputs['Color'],channels.inputs['Color']);nt.links.new(channels.outputs['Green'],bsdf.inputs['Roughness']);nt.links.new(channels.outputs['Blue'],bsdf.inputs['Metallic'])
 bsdf.inputs['Specular IOR Level'].default_value=.5
 return mat
me.materials.clear()
for prefix,name in [('m520','Cyclops_A'),('m520_head','CyclopsHead_A')]:
 me.materials.append(material(name,p/f'textures/{prefix}_basecolor_1k.png',p/f'textures/{prefix}_normal_gltf_1k.png',p/f'textures/{prefix}_metal_rough_1k.png'))
for face in me.polygons:face.material_index=head[face.index]
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/boulder_v1/model_urls_glb.glb'));new=set(bpy.data.objects)-before
rock=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.polygons));import boulder_mesh;boulder_mesh.prepare(rock)
for o in new:
 if o!=rock:bpy.data.objects.remove(o,do_unlink=True)
rock.name='Boulder';rock.modifiers.clear();rock.vertex_groups.clear();rock.data.uv_layers.active.name='UVMap'
rock.data.materials.clear();rock.data.materials.append(material('Boulder_A',p/'textures/boulder_basecolor_512.png',p/'textures/boulder_normal_512.png',p/'textures/boulder_metal_rough_512.png'))
for face in rock.data.polygons:face.material_index=0;face.use_smooth=True
for obj in bpy.data.objects:obj.select_set(obj==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('Boulder');bone.head=(0,0,0);bone.tail=(0,1,0);bone.use_deform=True;bpy.ops.object.mode_set(mode='OBJECT')
rock.vertex_groups.new(name='Boulder').add(list(range(len(rock.data.vertices))),1,'REPLACE')
rock.parent=rig;mod=rock.modifiers.new('Armature','ARMATURE');mod.object=rig
for obj in bpy.data.objects:obj.select_set(obj in [body,rock])
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Cyclops'
# Export at 60 Hz so the carried two-hand assembly stays in contact between frames.
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:
      k.co.x*=2;k.handle_left.x*=2;k.handle_right.x*=2
 a.frame_start*=2;a.frame_end*=2
path=json.loads((p/'work/boulder_path.json').read_text())
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];pb=rig.pose.bones['Boulder'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0)
 frames=range(int(a.frame_range[1])+1) if a.name=='Attack' else [0,int(a.frame_range[1])]
 for f in frames:
  row=path[f] if a.name=='Attack' else None;pb.location=row['centre'] if row else (0,0,0);pb.rotation_quaternion=row['rotation'] if row else (1,0,0,0);pb.scale=(1,1,1) if row and row['visible'] else (0,0,0)
  for channel in ['location','rotation_quaternion','scale']:pb.keyframe_insert(channel,frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path=='pose.bones["Boulder"].scale' else 'LINEAR'
# Validate influence sums before the GLB exporter splits UV vertices.
weights=[sum(g.weight for g in v.groups) for v in body.data.vertices];assert max(abs(w-1) for w in weights)<1e-5
for name in ['piece','head','finger','orig_co']:
 if name in body.data.attributes:body.data.attributes.remove(body.data.attributes[name])
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
for pb in rig.pose.bones:
 if pb.name!='Boulder':pb.scale=(1,1,1)
(p/'export').mkdir(exist_ok=True);scene=bpy.context.scene;scene.render.fps=60;scene.render.fps_base=1
for obj in bpy.data.objects:obj.select_set(obj in [body,rig])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(p/'export/mm8_m520_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p/'export/mm8_m520.blend'))
info={'fps':60,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'bones':len(rig.data.bones),'clips':{a.name:[int(v) for v in a.frame_range] for a in bpy.data.actions},'boulder_size':[.58,.4,.38],'boulder_release_seconds':1.0}
(p/'export/export_info.json').write_text(json.dumps(info,indent=2));print('EXPORTED',info,flush=True)
common.workbench_clay(scene,textured=True)
for name,frames in {'Standing':[0],'Attack':[9,12,18,24,27,30,34],'Death':[0,30,50,78]}.items():
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in frames:
  scene.frame_set(f*2);common.render_views(str(p/f'review/export_{name}_{f:02}'),1.35,3.2,views=('front','left','three_quarter'),resolution=(700,900))
