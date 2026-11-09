"""Export selected measured geometry and unchanged clips; package resources in a separate local step."""
import bpy,sys,json,struct,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
selection=json.loads((P/'review/reduction/selection.json').read_text());E=P/'export';E.mkdir(exist_ok=True);manifest=[]
def curves(a):return [fc for l in a.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
for level in range(4):
 bodyinfo=selection['body'][level];clubinfo=selection['club'][level]
 bpy.ops.wm.open_mainfile(filepath=str(P/bodyinfo['blend']));C.cleanup();C.reset();
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and Path(bpy.path.abspath(im.filepath)).is_file():
   if im.packed_file:im.unpack(method='REMOVE')
   im.reload()
 rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];bpy.data.objects.remove(bpy.data.objects['ClubMesh'],do_unlink=True)
 with bpy.data.libraries.load(str(P/clubinfo['blend']),link=False)as(src,dst):dst.objects=['ClubMesh']
 club=dst.objects[0];bpy.context.scene.collection.objects.link(club);club.name='ClubMesh';club.parent=rig
 for m in club.modifiers:
  if m.type=='ARMATURE':m.object=rig
 for o in list(bpy.data.objects):
  if o.type=='ARMATURE'and o!=rig:bpy.data.objects.remove(o,do_unlink=True)
 for o in [body,club]:
  group=o.vertex_groups.get('_reduction_protect')
  if group:o.vertex_groups.remove(group)
  for v in o.data.vertices:
   ws=sorted([(g.group,g.weight)for g in v.groups if o.vertex_groups[g.group].name in rig.data.bones and g.weight>1e-8],key=lambda t:-t[1])[:4];total=sum(w for _,w in ws);assert total>0
   for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
   for gi,w in ws:o.vertex_groups[gi].add([v.index],w/total,'REPLACE')
 body.data.materials[0].name=f'MerchantL{level}_A';body.data.materials[1].name=f'MerchantHeadL{level}_A';club.data.materials[0].name=f'MerchantClubL{level}'
 if level==3:
  node=body.data.materials[1].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node
  node.image=bpy.data.images.load(str(P/bodyinfo['textures']/'1_basecolor.png'),check_existing=False)
 for name in ['Body','ClubMesh']:bpy.data.objects[name].hide_render=False
 C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/reduction/selected_lod{level}.blend'))
 if level==0:
  # Keep the authoring rig editable at its native 30 fps, with actual tier-A colour visible.
  mat=body.data.materials[0];node=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node;original=node.image
  node.image=bpy.data.images.load(str(P/bodyinfo['textures']/'mer1_a_preview.png'));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(E/'mm6_mer1.blend'));node.image=original
 for o in bpy.data.objects:o.select_set(o in [body,club])
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Merchant'
 for name in ['piece','finger','head','orig_co']:
  if name in body.data.attributes:body.data.attributes.remove(body.data.attributes[name])
 keep={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
 for a in list(bpy.data.actions):
  if a.name not in keep:bpy.data.actions.remove(a)
 scene=bpy.context.scene
 if level==0:
  for a in bpy.data.actions:
   for fc in curves(a):
    for k in fc.keyframe_points:k.co.x*=4;k.handle_left.x*=4;k.handle_right.x*=4
    fc.update()
   if a.use_frame_range:
    first,last=a.frame_start,a.frame_end;a.frame_end=last*4;a.frame_start=first*4
  scene.render.fps=120
  a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
 else:scene.render.fps=30
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 path=P/f'work/reduction/selected_lod{level}.glb'
 bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_extras=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 raw=path.read_bytes();doc=json.loads(raw[20:20+struct.unpack('<I',raw[12:16])[0]]);bodyinfo=copy.deepcopy(bodyinfo)
 count=sum(doc['accessors'][prim['indices']]['count']//3 for mesh in doc['meshes'] for prim in mesh['primitives'] if 'Club' not in doc['materials'][prim['material']]['name'])
 if count!=bodyinfo['triangles']:bodyinfo['authoring_triangles']=bodyinfo['triangles'];bodyinfo['triangles']=count
 manifest.append({'level':level,'glb':str(path.relative_to(P)),'body':bodyinfo,'club':clubinfo})
(P/'work/reduction/exports_manifest.json').write_text(json.dumps(manifest,indent=2))
print('EXPORTED FOUR SELECTED LEVELS',flush=True)
