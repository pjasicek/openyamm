import bpy,json,sys,io,hashlib,collections,subprocess
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb,accessor_bytes

original,payload=read_glb(ROOT/'body_for_texture_v1.glb')
returned,returned_payload=read_glb(ROOT.parent/'meshy/body_texture_v1/model_urls_glb.glb')
rows=[];faces=[]
for doc,data in ((original,payload),(returned,returned_payload)):
    primitive=doc['meshes'][0]['primitives'][0]
    positions=np.frombuffer(accessor_bytes(doc,data,primitive['attributes']['POSITION']),dtype='<f4').reshape(-1,3)
    uv=np.frombuffer(accessor_bytes(doc,data,primitive['attributes']['TEXCOORD_0']),dtype='<f4').reshape(-1,2)
    accessor=doc['accessors'][primitive['indices']]
    indices=np.frombuffer(accessor_bytes(doc,data,primitive['indices']),dtype={5123:'<u2',5125:'<u4'}[accessor['componentType']]).reshape(-1,3)
    rows.append((positions,uv));faces.append(collections.Counter(tuple(sorted(tuple(map(float,uv[i])) for i in t)) for t in indices))
assert faces[0]==faces[1],'Texture return changed per-triangle UV correspondence'
source,uv=rows[0];center=(source.min(0)+source.max(0))/2;half_height=(source[:,1].max()-source[:,1].min())/2
reference=collections.defaultdict(list)
for p,u in zip(source,uv):reference[tuple(u)].append(p)
error=0
for p,u in zip(*rows[1]):
    assert tuple(u) in reference,'Returned UV changed'
    error=max(error,min(float(np.linalg.norm(p*half_height+center-q)) for q in reference[tuple(u)]))
assert error*.01<1e-5,('Texture return changed original surface',error)
texture_dir=ROOT/'textures';texture_dir.mkdir(exist_ok=True)
receipt=json.loads((ROOT/'creature_3d_progress.json').read_text())['meshy']['jobs']['body_texture_v1']
for key,name in [('texture_urls_0_base_color','base_color.png'),('texture_urls_0_roughness','roughness.png'),('texture_urls_0_normal','normal.png')]:
    source_path=ROOT.parent/receipt['downloads'][key]['path'];(texture_dir/name).write_bytes(source_path.read_bytes())
material=returned['materials'][0];tex_index=returned['textures'][material['pbrMetallicRoughness']['metallicRoughnessTexture']['index']]['source']
view=returned['bufferViews'][returned['images'][tex_index]['bufferView']];offset=view.get('byteOffset',0)
packed_path=texture_dir/'packed_mr_original.jpg';packed_path.write_bytes(returned_payload[offset:offset+view['byteLength']])
subprocess.run(['/usr/bin/python3','-c',"from PIL import Image;import sys;Image.open(sys.argv[1]).convert('RGB').getchannel('B').save(sys.argv[2])",str(packed_path),str(texture_dir/'metallic.png')],check=True)
# Remove confirmed service metallic bleed outside gold, retaining the actual generated gold map.
subprocess.run(['/usr/bin/python3','-c',"""
from PIL import Image
import numpy as np,sys
from pathlib import Path
r=Path(sys.argv[1]);a=np.asarray(Image.open(r/'base_color.png').convert('RGB')).astype(float)
m=np.asarray(Image.open(r/'metallic.png')).copy();rough=np.asarray(Image.open(r/'roughness.png').convert('L')).copy()
gold=(a[:,:,0]>a[:,:,1]*1.15)&(a[:,:,1]>a[:,:,2]*1.3)&(a[:,:,0]>64)
skin=(a[:,:,2]>a[:,:,0]*1.2)&(a[:,:,1]>a[:,:,0]*1.1)
m[~gold]=0;rough[skin]=np.maximum(rough[skin],140)
assert np.all(m[skin]==0)
Image.fromarray(m).save(r/'metallic.png');Image.fromarray(rough).save(r/'roughness.png')
print('Non-gold metal bleed removed; blue-skin roughness minimum 140/255.')
""",str(texture_dir)],check=True)
print('UV triangles preserved; maximum rest-surface error metres:',error*.01,flush=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'animated_master_v7.blend'))
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;body=bpy.data.objects['Lizardman_Body'];rig=bpy.data.objects['Lizardman_Rig']
# Deliver a conventional metre-space rig; preserve the world-space surface and all clip translations.
bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
world_before=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
assert all(abs(x-.01)<1e-6 for x in rig.matrix_world.to_scale())
body.parent=None
for v in body.data.vertices:v.co*=.01
rig.data.transform(Matrix.Scale(.01,4))
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if curve.data_path.startswith('pose.bones[') and curve.data_path.endswith('.location'):
                        for key in curve.keyframe_points:
                            key.co.y*=.01;key.handle_left.y*=.01;key.handle_right.y*=.01
for bone in rig.pose.bones:bone.location*=.01
rig.matrix_world=Matrix.Identity(4);body.matrix_world=Matrix.Identity(4)
body.parent=rig;body.matrix_parent_inverse=Matrix.Identity(4);body.matrix_basis=Matrix.Identity(4)
scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
error_units=max((a-ev.matrix_world@v.co).length for a,v in zip(world_before,mesh.vertices));ev.to_mesh_clear()
assert error_units<1e-5,('Unit conversion changed surface',error_units)
print('Metre-space rig conversion world error:',error_units,flush=True)
material=bpy.data.materials.new('MM8_Lizardman_Villager_A');material.use_nodes=True
nodes=material.node_tree.nodes;nodes.clear();links=material.node_tree.links
shader=nodes.new('ShaderNodeBsdfPrincipled');output=nodes.new('ShaderNodeOutputMaterial');links.new(shader.outputs['BSDF'],output.inputs['Surface'])
for name,output_name,input_name in [('base_color.png','Color','Base Color'),('roughness.png','Color','Roughness'),('metallic.png','Color','Metallic')]:
    n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(texture_dir/name),check_existing=True);n.image.colorspace_settings.name='sRGB' if name.startswith('base') else 'Non-Color';links.new(n.outputs[output_name],shader.inputs[input_name])
normal=nodes.new('ShaderNodeTexImage');normal.image=bpy.data.images.load(str(texture_dir/'normal.png'),check_existing=True);normal.image.colorspace_settings.name='Non-Color'
normal_map=nodes.new('ShaderNodeNormalMap');normal_map.inputs['Strength'].default_value=.7;links.new(normal.outputs['Color'],normal_map.inputs['Color']);links.new(normal_map.outputs['Normal'],shader.inputs['Normal'])
body.data.materials.clear();body.data.materials.append(material)

def clip(name,frame):
    rig.animation_data.action=bpy.data.actions[name]
    rig.animation_data.action_slot=next(t.strips[0].action_slot for t in rig.animation_data.nla_tracks if t.name==name)
    for t in rig.animation_data.nla_tracks:t.mute=True
    scene.frame_set(int(frame),subframe=frame%1)

scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=720;scene.render.resolution_y=720
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.36,.36,.36,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT':bpy.data.objects.remove(obj,do_unlink=True)
for name,position,power in [('Neutral_Key',(3,-4,4),420),('Neutral_Fill',(-3,-1,2.4),220),('Neutral_Rim',(1,3,3),350)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=3
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.15
review=ROOT/'material_review_v1';review.mkdir(exist_ok=True)
views={'front':(0,-5,0),'quarter':(-3.535,-3.535,0),'profile':(-5,0,0),'rear_quarter':(-3.535,3.535,0),'back':(0,5,0)}
for name,frame in [('Standing',0),('Fidget',12),('Hit',12),('Death',24),('Corpse',0)]:
    clip(name,frame)
    for view,direction in views.items():
        if name not in ('Standing','Corpse') and view not in ('front','profile','quarter'):continue
        target=Vector((0,.23,.83));camera.location=target+Vector(direction);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(review/f'{name}_{view}.png');bpy.ops.render.render(write_still=True)
clip('Standing',0)
for focus,target,scale in [('head',(0,-.04,1.43),.65),('hands',(0,-.05,.76),1),('feet',(0,0,.18),.7)]:
    target=Vector(target);camera.data.ortho_scale=scale;camera.location=target+Vector((-2,-5,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(review/f'detail_{focus}.png');bpy.ops.render.render(write_still=True)

# A checker verifies the retained final UV set on the actual rest surface.
checker=bpy.data.materials.new('UV_Checker');checker.use_nodes=True;n=checker.node_tree.nodes.new('ShaderNodeTexChecker');coord=checker.node_tree.nodes.new('ShaderNodeTexCoord');n.inputs['Scale'].default_value=48
checker.node_tree.links.new(coord.outputs['UV'],n.inputs['Vector']);checker.node_tree.links.new(n.outputs['Color'],checker.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
body.data.materials[0]=checker
for view,direction in [('front',(0,-5,0)),('back',(0,5,0))]:
    camera.data.ortho_scale=2.1;target=Vector((0,0,.85));camera.location=target+Vector(direction);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(review/f'checker_{view}.png');bpy.ops.render.render(write_still=True)
body.data.materials[0]=material
clip('Standing',0);camera.data.ortho_scale=2.15;scene.frame_start=0;scene.frame_end=6
bpy.ops.file.pack_all()
delivery=ROOT/'delivery';delivery.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(delivery/'mm8_lizardman_villager_a.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'textured_export_v1.glb'),export_format='GLB',use_selection=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,export_force_sampling=True,export_yup=True,export_all_influences=True)
subprocess.run(['/usr/bin/python3',str(REPO/'tools/prepare_actor_glb.py'),str(ROOT/'textured_export_v1.glb'),str(delivery/'mm8_lizardman_villager_a.glb')],check=True)
(ROOT/'texture_return_check.json').write_text(json.dumps({'uv_triangles_exact':True,'original_uv_preserved':True,'triangle_count':15287,'service_normalization':{'center_source_cm':list(map(float,center)),'half_height_source_cm':float(half_height)},'max_world_surface_error_m':error*.01,'returned_geometry_applied':False,'retained_master':'animated_master_v7.blend','normal_strength':.7,'maps':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in texture_dir.glob('*.png')}},indent=2))
print('Retained animated master textured, packed and exported',flush=True)
