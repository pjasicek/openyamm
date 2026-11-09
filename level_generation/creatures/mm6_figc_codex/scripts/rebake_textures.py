"""Selected-to-active texture and tangent-normal bake from the accepted round-2 surface."""
import bpy,bmesh,os,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';level=int(os.environ.get('FIGC_BAKE_LEVEL','0'));D=R/os.environ.get('FIGC_BAKE_ROOT','rebake')/f'export_lod{level}';T=D/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'mm6_figc_authoring.blend'));target=bpy.data.objects['FighterChain'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for m in target.modifiers:m.show_render=False;m.show_viewport=False
bpy.context.view_layer.update()
# Repack each existing material separately; the original source UVs remain untouched.
for o in bpy.data.objects:o.select_set(o is target)
bpy.context.view_layer.objects.active=target
bm=bmesh.new();bm.from_mesh(target.data);uv=bm.loops.layers.uv.active
for edge in bm.edges:
 edge.seam=len(edge.link_loops)!=2
 if not edge.seam:
  a,b=edge.link_loops;edge.seam=a.face.material_index!=b.face.material_index or any((next(l for l in a.face.loops if l.vert==v)[uv].uv-next(l for l in b.face.loops if l.vert==v)[uv].uv).length>1e-6 for v in edge.verts)
bm.to_mesh(target.data);bm.free()
for material in range(len(target.data.materials)):
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in target.data.polygons:f.select=f.material_index==material
 bpy.ops.object.mode_set(mode='EDIT')
 # The hand-modelled prop projections intentionally overlap. Closed sockets need fresh charts; body seams stay fixed.
 if 'Gear' in target.data.materials[material].name:bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=[.008,.015,.025,.04][level])
 else:bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=[.005,.015,.025,.04][level])
 bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(R/'before/export/mm6_figc_authoring.blend'),link=False) as (src,dst):dst.meshes=['FighterChain']
source=bpy.data.objects.new('AcceptedSource',dst.meshes[0]);scene.collection.objects.link(source);source.matrix_world=target.matrix_world.copy()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=False;scene.render.bake.cage_extrusion=[.015,.035,.06,.10][level];scene.render.bake.max_ray_distance=[.05,.12,.18,.24][level];scene.render.bake.margin=[12,8,4,2][level];scene.render.bake.use_clear=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
suffix=lambda m:'_head' if 'Head' in m.name else '_gear' if 'Gear' in m.name else ''
images={};target_nodes={}
for m in target.data.materials:
 m.use_nodes=True;node=m.node_tree.nodes.new('ShaderNodeTexImage');m.node_tree.nodes.active=node;target_nodes[m.name]=node
def gear_only(original,name):
 faces=[f for f in original.data.polygons if 'Gear' in original.data.materials[f.material_index].name];me=bpy.data.meshes.new(name);me.from_pydata([v.co for v in original.data.vertices],[],[tuple(f.vertices) for f in faces]);me.materials.append(original.data.materials[faces[0].material_index]);uv=me.uv_layers.new(name='UVMap');normals=[]
 for new,old in zip(me.polygons,faces):
  new.use_smooth=old.use_smooth
  for dst,src in zip(new.loop_indices,old.loop_indices):uv.data[dst].uv=original.data.uv_layers.active.data[src].uv;normals.append(original.data.corner_normals[src].vector)
 me.normals_split_custom_set(normals);ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);ob.matrix_world=original.matrix_world.copy();return ob
for kind in ['basecolor','region_mask','metal_rough','normal']:
 for m in source.data.materials:
  nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');s=suffix(m);size='2k' if s=='_gear' else '1k'
  if kind=='normal':nt.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
  else:
   filename=f'figc{s}_region_mask.png' if kind=='region_mask' else f'figc{s}_{kind}_{size}.png';img=bpy.data.images.load(str(R/'before/textures'/filename),check_existing=True);img.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color';node=nt.nodes.new('ShaderNodeTexImage');node.image=img;em=nt.nodes.new('ShaderNodeEmission');nt.links.new(node.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],output.inputs['Surface'])
 for m in target.data.materials:
  s=suffix(m);size=[2048,1024,512,256][level];img=bpy.data.images.new(f'rebake{s}_{kind}',width=size,height=size,alpha=False);img.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color';target_nodes[m.name].image=img;images[(s,kind)]=img
 for o in bpy.data.objects:o.select_set(o in [source,target])
 bpy.context.view_layer.objects.active=target;bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False);bpy.ops.object.bake(type='NORMAL' if kind=='normal' else 'EMIT',normal_space='TANGENT')
 # Bake prop surfaces separately: the hand/body otherwise contaminates the held grip and overlapping socket.
 high_gear=gear_only(source,'SourceGearOnly');low_gear=gear_only(target,'TargetGearOnly')
 for o in bpy.data.objects:o.select_set(o in [high_gear,low_gear])
 bpy.context.view_layer.objects.active=low_gear;scene.render.bake.cage_extrusion=[.008,.015,.025,.04][level];scene.render.bake.max_ray_distance=[.06,.10,.12,.16][level];bpy.ops.object.bake(type='NORMAL' if kind=='normal' else 'EMIT',normal_space='TANGENT')
 for o in [high_gear,low_gear]:mesh=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(mesh)
 scene.render.bake.cage_extrusion=[.015,.035,.06,.10][level];scene.render.bake.max_ray_distance=[.05,.12,.18,.24][level]
 for (s,k),img in list(images.items()):
  if k!=kind:continue
  size='2k' if s=='_gear' else '1k';filename=f'figc{s}_region_mask.png' if kind=='region_mask' else f'figc{s}_{kind}_{size}.png';img.filepath_raw=str(T/filename);img.file_format='PNG';img.save();img.pack()
 print('BAKE_COMPLETE',level,kind,flush=True)
for m in target.data.materials:
 nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');s=suffix(m)
 def tex(k):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=images[(s,k)];return n
 nt.links.new(tex('basecolor').outputs['Color'],bs.inputs['Base Color']);n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough').outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
bpy.data.objects.remove(source,do_unlink=True)
for m in target.modifiers:m.show_render=True;m.show_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(D/'rebaked_authoring.blend'))
for o in bpy.data.objects:o.select_set(o in [target,rig])
bpy.context.view_layer.objects.active=rig;rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.ops.export_scene.gltf(filepath=str(D/'rebaked.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(T/'figc_ramps.json').write_bytes((P/'textures/figc_ramps.json').read_bytes())
