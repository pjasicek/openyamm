"""Build the editable material master and export dense, exact-endpoint animation samples."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animations.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
manifest=json.loads((P/'work/animation_manifest.json').read_text());keep=set(manifest['clips'])
# Remove detached reduction slivers and close any remaining small seams with nearby stone UVs.
for name in ['Body','Head']:
 obj=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(obj.data);uv=bm.loops.layers.uv.active
 boundary=[e for e in bm.edges if e.is_boundary];discard=set();seen=set()
 for edge in boundary:
  for seed in edge.link_faces:
   if seed in seen:continue
   connected={seed};todo=[seed]
   while todo:
    face=todo.pop()
    for edge2 in face.edges:
     for other in edge2.link_faces:
      if other not in connected:connected.add(other);todo.append(other)
   seen|=connected
   if len(connected)<8:discard|=connected
 assert len(discard)<=8
 if discard:bmesh.ops.delete(bm,geom=list(discard),context='FACES')
 print('REMOVED_DETACHED_SLIVERS',name,len(discard))
 boundary=[e for e in bm.edges if e.is_boundary];old_faces=set(bm.faces)
 if boundary:
  remaining=set(boundary);new_faces=[]
  while remaining:
   edge=remaining.pop();order=[edge.verts[0],edge.verts[1]]
   while order[-1]!=order[0]:
    choices=[e for e in remaining if order[-1] in e.verts];assert len(choices)==1
    edge=choices[0];remaining.remove(edge);order.append(edge.other_vert(order[-1]))
   assert len(order)<=9
   new_faces.append(bm.faces.new(order[:-1]))
  result={'faces':new_faces}
  for face in result['faces']:
   neighbours=[f for e in face.edges for f in e.link_faces if f in old_faces]
   assert neighbours
   source=neighbours[0]
   for loop in face.loops:loop[uv].uv=min(source.loops,key=lambda other:(other.vert.co-loop.vert.co).length)[uv].uv
   face.smooth=True
  bmesh.ops.triangulate(bm,faces=result['faces']);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
 assert not any(e.is_boundary for e in bm.edges),name
 bm.to_mesh(obj.data);bm.free()

def curves(a):return [fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a);continue
 # A 120 Hz export represents every clip endpoint exactly, including the trimmed attack.
 for fc in curves(a):
  for k in fc.keyframe_points:
   k.co.x*=4;k.handle_left.x*=4;k.handle_right.x*=4;k.interpolation='LINEAR'
   if a.name=='Death' and abs(k.co.x-11.88)<.001:k.co.x=11
  fc.update()
 a.frame_start=0;a.frame_end=manifest['clips'][a.name]['duration']*120
scene.render.fps=120
for part in ['body','head']:
 mat=bpy.data.objects[part.title()].data.materials[0];mat.name='Gargoyle'+part.title();nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled');nt.links.new(bs.outputs[0],out.inputs['Surface']);bs.inputs['Specular IOR Level'].default_value=.5;mat.use_backface_culling=False
 def texture(suffix,space):
  img=bpy.data.images.load(str((P/f'textures/{part}_{suffix}.png').resolve()),check_existing=True);img.colorspace_settings.name=space;n=nt.nodes.new('ShaderNodeTexImage');n.image=img;return n
 bc=texture('basecolor','sRGB');nt.links.new(bc.outputs['Color'],bs.inputs['Base Color']);nm=texture('normal','Non-Color');normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nm.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);mr=texture('metal_rough','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=bc
 mat['openyamm_specular']=1.0;mat['openyamm_specular_mask']=True
# Numeric checks cover the final interpolation of every mesh, including rigid fragments.
report={};meshes=[bpy.data.objects[n] for n in ['Body','Head','Rubble']]
rest={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in meshes};edge={o.name:np.array([e.vertices[:] for e in o.data.edges]) for o in meshes}
for name in keep:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for f in sorted(set(list(np.arange(0,a.frame_end+.001,1))+[float(a.frame_end)])):
  scene.frame_set(math.floor(f),subframe=f%1);row={'time':f/120,'meshes':{}}
  for o in meshes:
   ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all();e=edge[o.name];length=np.linalg.norm(rest[o.name][e[:,1]]-rest[o.name][e[:,0]],axis=1);ratio=np.linalg.norm(co[e[:,1]]-co[e[:,0]],axis=1)/np.maximum(length,1e-6);valid=length>.003
   row['meshes'][o.name]={'edge_max':float(ratio[valid].max()),'p99':float(np.quantile(ratio[valid],.99)),'bounds':[co.min(0).tolist(),co.max(0).tolist()]}
  assert all(max(pb.scale)-min(pb.scale)<1e-5 for pb in rig.pose.bones),'nonuniform bone scale'
  rows.append(row)
 report[name]={'samples':len(rows),'duration':a.frame_end/120,'max_body_edge':max(r['meshes']['Body']['edge_max'] for r in rows),'max_body_p99':max(r['meshes']['Body']['p99'] for r in rows),'head_edge':max(r['meshes']['Head']['edge_max'] for r in rows),'samples_detail':rows}
 print('AUDIT',name,{k:v for k,v in report[name].items() if k!='samples_detail'},flush=True)
(P/'work/final_pose_audit.json').write_text(json.dumps(report,indent=2))
for name in ['Flight','Attack','Hit']:
 assert 1 < report[name]['max_body_edge']<3.1,(name,report[name]['max_body_edge'])
 assert min(r['meshes']['Body']['bounds'][1][2]-r['meshes']['Body']['bounds'][0][2] for r in report[name]['samples_detail'])>1.5
# Body and head share one runtime atlas after the standard material merge.
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
for n in ['Body','Head']:bpy.data.objects[n].select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['Body'];bpy.ops.object.join();body=bpy.context.object;body.name='Gargoyle'
sockets=[]
for sd in ['L','R']:
 bone=rig.data.bones[f'B_{sd}_Hand'];e=bpy.data.objects.new('Socket_Palm_'+('Left' if sd=='L' else 'Right'),None);scene.collection.objects.link(e);e.matrix_world=Matrix.Translation(bone.head_local.lerp(bone.tail_local,.5));mw=e.matrix_world.copy();e.parent=rig;e.parent_type='BONE';e.parent_bone=bone.name;e.matrix_world=mw;sockets.append(e)
rig.animation_data.action=bpy.data.actions['Flight'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
for o in bpy.data.objects:o.select_set(o in [body,bpy.data.objects['Rubble'],rig]+sockets)
bpy.context.view_layer.objects.active=rig;(P/'export').mkdir(exist_ok=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_gar.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_gar_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
common.workbench_clay(scene,textured=True)
for variant in ['gar_a','gar_b','gar_c']:
 for part in ['body','head']:
  mat=bpy.data.materials['Gargoyle'+part.title()];n=mat.node_tree.nodes.active;n.image=bpy.data.images.load(str((P/f'textures/{part}_{variant}.png').resolve()),check_existing=True)
 common.render_views(str(P/f'review/{variant}'),1.5,3.3,views=('front','left','back','three_quarter'),resolution=(750,1000))
 common.render_views(str(P/f'review/{variant}_head'),1.68,.60,views=('front','left','three_quarter'),resolution=(750,750),target=(0,-.03))
print('EXPORTED_GARGOYLE',len(rig.data.bones))
