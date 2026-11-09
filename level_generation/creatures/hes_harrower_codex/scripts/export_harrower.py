"""Shared-body Harrower assemblies, before runtime variants, LODs and rigid attachment split."""
from pathlib import Path
import sys,json,bpy
P=Path(__file__).resolve().parents[1]
source=Path(sys.argv[sys.argv.index('--')+1]).resolve()
def material(name,glow=False):
 old=bpy.data.materials.get(name)
 if old:old.name=name+'_old'
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
 if glow:
  bs.inputs['Base Color'].default_value=(1,.42,.08,1);bs.inputs['Emission Color'].default_value=(1,.42,.08,1);bs.inputs['Emission Strength'].default_value=1
  bs.inputs['Roughness'].default_value=.4
 else:
  def tex(suffix,cs):
   n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/'textures'/('hkr_armour_'+suffix+'.png')),check_existing=True);n.image.reload();n.image.colorspace_settings.name=cs;return n
  base=tex('basecolor','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color'])
  if name in ('HHW_Cloth','HHW_Mantle'):nt.links.new(base.outputs['Alpha'],bs.inputs['Alpha'])
  nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
  sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color'])
  nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
  m['openyamm_specular_mask']=True
 return m
report={}
for kind in ('family','vreth'):
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;sc.render.fps=120;sc.render.fps_base=1
 rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()
 mats=[material('HHW_Plate'),material('HHW_Glow',True)];bossm=[material('HHW_Mantle'),material('HHW_MantleGlow',True)];clothm=[material('HHW_Cloth'),material('HHW_ClothGlow',True)]
 parts=[body]
 for o in list(bpy.data.objects):
  if o.type!='MESH' or o==body:continue
  if (kind=='family' and o.name.startswith('Vreth_') and o.name!='Vreth_Scars') or (kind=='vreth' and o.name.startswith('Family_')):
   bpy.data.objects.remove(o,do_unlink=True);continue
  slots=[f.material_index for f in o.data.polygons];o.data.materials.clear()
  for m in (bossm if o.name.startswith('Mantle_') or o.name=='Vreth_Scars' else clothm if o.name.startswith(('Cloth_','Wrap_')) else mats):o.data.materials.append(m)
  o.data.polygons.foreach_set('material_index',slots);o.modifiers.clear();parts.append(o)
 body.modifiers.clear()
 for o in bpy.data.objects:o.select_set(o in parts)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body=bpy.context.view_layer.objects.active;body.name=body.data.name='HHW'
 for n in ('piece','garment','finger','head','orig_co','thin_co','shell_hidden'):
  if n in body.data.attributes:body.data.attributes.remove(body.data.attributes[n])
 body.parent=rig;md=body.modifiers.new('Armature','ARMATURE');md.object=rig
 for a in list(bpy.data.actions):
  if not a.name.startswith(('Carbine_','Demon_','Harrower_')):bpy.data.actions.remove(a)
 # Keep the quarter-frame cloth corrections in the runtime animation, with unchanged durations.
 for a in bpy.data.actions:
  start,end=a.frame_range[:]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:
       key.co.x*=4;key.handle_left.x*=4;key.handle_right.x*=4
  if a.use_frame_range:a.frame_start=start*4;a.frame_end=end*4
 # Export the new motions first so review tools choose Harrower_Standing rather than a compatibility clip.
 act=bpy.data.actions['Harrower_Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for o in bpy.data.objects:o.select_set(o in (rig,body))
 bpy.context.view_layer.objects.active=rig
 out=P/'work'/('assembly_'+kind+'_lod0.glb')
 bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_extras=True,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 report[kind]={'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'bones':len(rig.data.bones),'clips':[a.name for a in bpy.data.actions]}
 assert report[kind]['triangles']<=15000,report[kind]
 assert len([a for a in bpy.data.actions if a.name.startswith(('Carbine_','Demon_'))])==18
 print('ASSEMBLY',kind,report[kind],flush=True)
(P/'review/export.json').write_text(json.dumps(report,indent=2)+'\n')
