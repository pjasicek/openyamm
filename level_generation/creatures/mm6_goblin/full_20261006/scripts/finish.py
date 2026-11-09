"""Pack the reviewed master and export exact native clips with dense collapse keys retained."""
import bpy,json,hashlib,math
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/native_textured_v2.blend'))
arm=bpy.data.objects['Goblin_Rig'];body=bpy.data.objects['Goblin_Body'];sword=bpy.data.objects['Goblin_Sword'];scene=bpy.context.scene;scene.view_layers[0].material_override=None
clips={'Standing':125,'Walk':750,'Attack':750,'Hit':750,'Death':625,'Corpse':125,'Fidget':750}
for o in list(scene.objects):
 if o not in [arm,body,sword]:bpy.data.objects.remove(o,do_unlink=True)
for a in list(bpy.data.actions):
 if a.name not in clips:bpy.data.actions.remove(a)
 else:
  a.use_fake_user=True;a['native_duration_ms']=clips[a.name]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     # Quaternion signs must be continuous at all fractional collapse keys.
     paths={fc.data_path for fc in bag.fcurves if fc.data_path.endswith('rotation_quaternion')}
     for path in paths:
      curves=sorted([fc for fc in bag.fcurves if fc.data_path==path],key=lambda fc:fc.array_index);previous=None
      for keys in zip(*(fc.keyframe_points for fc in curves)):
       values=[k.co.y for k in keys]
       if previous is not None and sum(x*y for x,y in zip(previous,values))<0:
        for k in keys:k.co.y=-k.co.y
        values=[-v for v in values]
       previous=values
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:
       kp.co.x=1+(kp.co.x-1)*4;kp.interpolation='LINEAR'
      fc.update()
scene.render.fps=192;scene.frame_start=1;scene.frame_end=145
if arm.animation_data:
 for track in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(track)
for mat in body.data.materials:
 if any(n in mat.name.lower() for n in ['skin','leather','teeth','eyes']):
  socket=mat.node_tree.nodes.get('Principled BSDF').inputs['Metallic']
  for link in list(socket.links):mat.node_tree.links.remove(link)
  socket.default_value=0
for mat in sword.data.materials:
 bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat.use_nodes else None
 if bsdf:
  color=bsdf.inputs['Base Color'].default_value
  if color[0]>.15 and color[0]>color[1]*2 and color[0]>color[2]*2:
   bsdf.inputs['Base Color'].default_value=(.50,.29,.065,1);bsdf.inputs['Metallic'].default_value=.8;bsdf.inputs['Roughness'].default_value=.4;mat['correction']='Native golden pommel; removed reused sword ruby color.'
base=next(n.image for n in body.data.materials[0].node_tree.nodes if n.name=='base_color')
variants={745:base}
for pid in [746,747]:
 image=bpy.data.images.load(str(OUT/f'delivery/textures/goblin_basecolor_{pid}.png'),check_existing=False);image.name=f'Goblin palette {pid} 4K';image.colorspace_settings.name='sRGB';image.pack();image.use_fake_user=True;variants[pid]=image
for o in [arm,body,sword]:o.select_set(True)
bpy.context.view_layer.objects.active=arm;act=bpy.data.actions['Standing'];arm.animation_data.action=act;arm.animation_data.action_slot=act.slots[0];scene.frame_set(1)
arm['native_forward']='Blender -Y, glTF +Z';arm['native_walk_speed_m_s']=1.6;arm['native_scale_factors']='745=1;746=0.699997/0.649994;747=0.75/0.649994; caller applies scale once.'
for image in bpy.data.images:
 if image.source!='VIEWER' and image.size[0]>0 and not image.packed_file:image.pack()
for pid in [745,746,747]:
 for mat in body.data.materials:mat.node_tree.nodes['base_color'].image=variants[pid]
 bpy.ops.export_scene.gltf(filepath=str(OUT/f'delivery/mm6_goblin_{pid}.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_rest_position_armature=True,export_frame_range=False,export_force_sampling=True,export_frame_step=1,export_anim_single_armature=True,export_influence_nb=4,export_all_influences=False,export_animations=True,export_yup=True,export_apply=True,export_tangents=True,export_texcoords=True,export_normals=True,export_extras=True,export_image_format='AUTO')
for mat in body.data.materials:mat.node_tree.nodes['base_color'].image=base
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'delivery/mm6_goblin.blend'))
manifest={'clips':[{'name':name,'native_duration_ms':duration,'mode':'held' if name in ['Standing','Corpse'] else 'loop' if name in ['Walk','Fidget'] else 'one_shot','native_anchor_times_ms':list(range(0,duration,125)),'export_sampling_fps':192} for name,duration in clips.items()],'aliases':json.loads((OUT.parent/'stage1_20261006/source_inventory.json').read_text())['descriptor_aliases'],'death_end_state':'Corpse','standing_and_corpse':'Truly held; metadata 125 ms native descriptor, consumer may hold indefinitely.','outgoing_endpoints':'Attack/Hit/Fidget return to Standing at native end; incoming crossfade remains caller policy.','walk':'In-place; recommended calibrated actor travel 1.6 m/s; no native Run action.','coordinate_system':'glTF Y up, +Z forward, metres; Blender Z up, -Y forward. Ground at zero. Native front fit includes a +0.082 m lateral ready-pose offset.','effects_required':[],'native_scale_factors':{745:1,746:.699997/.649994,747:.75/.649994},'height_contract':'All palette files use the same 1.65 m reference body; caller applies the native variant scale factor once.'}
(OUT/'delivery/clip_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Packed master and three palette GLBs; all seven native clips retained.',flush=True)
