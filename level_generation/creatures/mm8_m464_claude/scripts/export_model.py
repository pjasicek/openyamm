"""Export the packed editable master, exact-duration clips and 50% colour/shadow LODs."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'));import build_actor_lods as L
bpy.ops.wm.open_mainfile(filepath=str(P/'work/repaired_master.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in list(bpy.data.objects):
 if o not in [body,r]:bpy.data.objects.remove(o,do_unlink=True)
for label,slot in [('body',0),('head',1)]:
 mat=body.data.materials[slot];nt=mat.node_tree;nt.nodes.clear();bs=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
 def tex(kind):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(P/f'textures/m464_{label}_{kind}.png'),check_existing=False);node.image.colorspace_settings.name='sRGB'if kind=='basecolor'else'Non-Color';return node
 base=tex('basecolor');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);normal=tex('normal');nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(normal.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);orm=tex('metal_rough');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(orm.outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 # Preserve red-channel specular data through Blender's packed metallic/roughness export.
 group=bpy.data.node_groups.get('glTF Material Output')or bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
 if not group.interface.items_tree:group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
 node=nt.nodes.new('ShaderNodeGroup');node.node_tree=group;nt.links.new(sep.outputs['Red'],node.inputs['Occlusion'])
 # The game consumes this channel as its material specular mask, not occlusion.
 mat.diffuse_color=(1,1,1,1)
sockets={}
for side,label in [('L','Left'),('R','Right')]:
 hn='B_'+side+'_Hand';h=r.data.bones[hn].head_local;kn=sum((r.data.bones[f'B_{side}_Finger{i}'].head_local for i in range(1,5)),Vector())/4;sockets['Socket_Palm_'+label]=(hn,(h+kn)*.5)
sockets['Socket_Gaze']=('B_Head',Vector((-.01,-.12,1.56)))
for name,(bone,pos) in sockets.items():
 o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.parent=r;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();parent=r.matrix_world@r.pose.bones[bone].matrix@Matrix.Translation((0,r.data.bones[bone].length,0));o.matrix_parent_inverse=parent.inverted();o.matrix_basis=Matrix.Translation(pos)
roles={'Standing','Walking','Running','Hit','Death','Dead','Fidget'}
for a in list(bpy.data.actions):
 if a.name not in roles:bpy.data.actions.remove(a)
 else:a.use_fake_user=True
assert {a.name for a in bpy.data.actions}==roles
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:]for v in mesh.vertices]);ev.to_mesh_clear();info={'standing_bounds_m':[co.min(0).tolist(),co.max(0).tolist()],'standing_height_m':float(np.ptp(co[:,2])),'durations':{a.name:float(a.frame_range[1])/30 for a in bpy.data.actions},'joints':len(r.data.bones)}
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=r;bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m464.blend'))
for a in bpy.data.actions:
 end=float(a.frame_range[1]);integer=round(end*8);factor=integer/end
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:
      for point in [kp.co,kp.handle_left,kp.handle_right]:point.x*=factor
 a.frame_start=0;a.frame_end=integer
sc.render.fps=240
bpy.ops.export_scene.gltf(filepath=str(P/'export/lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_tangents=True,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
d,b=L.read_glb(P/'export/lod0.glb');b=bytearray(b)
for a in d['animations']:
 end=max(float(d['accessors'][s['input']]['max'][0])for s in a['samplers']);duration=info['durations'][a['name']];cache={}
 for s in a['samplers']:
  old=s['input']
  if old not in cache:
   values=np.frombuffer(L.accessor_bytes(d,b,old),dtype='<f4').copy()*duration/end;index=L.append_accessor(d,b,d['accessors'][old],values.astype('<f4').tobytes());d['accessors'][index]['min']=[float(values.min())];d['accessors'][index]['max']=[float(values.max())];cache[old]=index
  s['input']=cache[old]
L.write_glb(P/'export/lod0.glb',d,b);(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True);L.generate(P/'export/lod0.glb',P/'export/lods.glb','Body',ratios=(.5,.25,.125),max_influences=4)
