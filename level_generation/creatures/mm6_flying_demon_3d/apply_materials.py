"""Apply verified PBR maps to the retained animated master and export A/B/C."""
from pathlib import Path
import bpy, json, math, importlib.util, hashlib, numpy as np
from mathutils import Vector

P=Path(__file__).resolve().parent
check=json.loads((P/'work/texture_correspondence.json').read_text())
assert set(check)=={'a','b','c','wings'}
assert all(v['surface_correspondence']['maps_compatible_with_retained_master'] for v in check.values())
for v,c in check.items():
 upload=P/'work'/('wings_upload.glb' if v=='wings' else 'texturing_upload_v2.glb')
 returned=P/'meshy'/('flying_'+v+'_texture_v'+('1' if v=='wings' else '2'))/'model_urls_glb.glb'
 assert hashlib.sha256(upload.read_bytes()).hexdigest()==c['upload_sha256']
 assert hashlib.sha256(returned.read_bytes()).hexdigest()==c['returned_glb_sha256']
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'))
scene=bpy.context.scene;body=next(o for o in scene.objects if o.get('material_role')=='body');rig=next(o for o in scene.objects if o.type=='ARMATURE')
spec=importlib.util.spec_from_file_location('flying_export',P/'export.py');exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)

def linear(rgb): return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
def constant(name,rgb,glow=False):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_fake_user=True;rgba=(*linear(rgb),1);mat.diffuse_color=rgba
 shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=rgba;shader.inputs['Roughness'].default_value=.60
 if glow: shader.inputs['Emission Color'].default_value=rgba;shader.inputs['Emission Strength'].default_value=.35
 return mat
def pbr(name,directory):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_fake_user=True
 nodes,links=mat.node_tree.nodes,mat.node_tree.links;shader=nodes.get('Principled BSDF')
 for field,suffix,space in [('Base Color','base_color','sRGB'),('Roughness','roughness','Non-Color')]:
  node=nodes.new('ShaderNodeTexImage');image=bpy.data.images.load(str(directory/f'texture_urls_0_{suffix}.png'),check_existing=True)
  image.colorspace_settings.name=space;image.pack();node.image=image;links.new(node.outputs['Color'],shader.inputs[field])
 node=nodes.new('ShaderNodeTexImage');image=bpy.data.images.load(str(directory/'texture_urls_0_normal.png'),check_existing=True)
 image.colorspace_settings.name='Non-Color';image.pack();node.image=image
 normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.75;links.new(node.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],shader.inputs['Normal'])
 # Flesh, bone and wing membranes have no metallic response. Keep the original
 # returned metallic maps as provenance; do not turn anatomical highlights into metal.
 shader.inputs['Metallic'].default_value=0
 return mat
eyes={'a':(.1,.8,1),'b':(1,.61,.12),'c':(1,.50,.20)}
bones={'a':(.87,.84,.71),'b':(.66,.56,.33),'c':(.63,.47,.38)}
effect_colors={
 'a':[(.18,.30,.85),(.32,.46,.96),(.47,.62,1),(.70,.78,1),(.95,.96,1),(.10,.07,.09)],
 'b':[(1,.48,.12),(1,.60,.25),(1,.73,.42),(1,.86,.67),(1,.96,.90),(.12,.09,.03)],
 'c':[(.72,.12,.025),(.95,.22,.025),(1,.42,.025),(1,.67,.16),(1,.92,.62),(.14,.055,.025)]}
def flame_material(name,rgb):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_fake_user=True
 mat.surface_render_method='BLENDED';nodes=mat.node_tree.nodes;links=mat.node_tree.links
 shader=nodes.get('Principled BSDF');shader.inputs['Metallic'].default_value=0
 shader.inputs['Roughness'].default_value=1;shader.inputs['Specular IOR Level'].default_value=.5
 image=bpy.data.images.new(name+'_Soft_Alpha',width=128,height=256,alpha=True)
 yy,xx=np.mgrid[0:256,0:128];t=(yy+.5)/256;x=(xx+.5)/128-.5
 centre=.035*np.sin(t*17)+.025*np.sin(t*31)
 width=.36*np.maximum(1-t,0)**.68+.008
 alpha=np.exp(-((x-centre)/width)**4)*np.minimum(1,t*14)*np.minimum(1,(1-t)*24)
 # Bright interior with soft edges, no shaded solid-droplet silhouette.
 heat=.70+.30*np.exp(-((x-centre)/(width*.55))**2)
 color=np.array(linear(rgb));rgba=np.empty((256,128,4),np.float32)
 rgba[:,:,:3]=heat[:,:,None]*color;rgba[:,:,3]=alpha
 image.pixels.foreach_set(rgba.ravel());image.pack();node=nodes.new('ShaderNodeTexImage');node.image=image
 links.new(node.outputs['Color'],shader.inputs['Base Color']);links.new(node.outputs['Color'],shader.inputs['Emission Color'])
 links.new(node.outputs['Alpha'],shader.inputs['Alpha']);shader.inputs['Emission Strength'].default_value=1
 return mat

materials={};wing=pbr('Flying_Wings_PBR',P/'meshy/flying_wings_texture_v1')
for variant in 'abc':
 materials[variant]={'skin':pbr('Flying_'+variant.upper()+'_Skin',P/'meshy'/f'flying_{variant}_texture_v2'),
  'iris':constant('Flying_'+variant.upper()+'_Iris',eyes[variant],True),
  'bone':constant('Flying_'+variant.upper()+'_Bone',bones[variant]),
  'effect':[]}
 for i,rgb in enumerate(effect_colors[variant]):
  mat=flame_material('Flying_'+variant.upper()+'_Effect_'+str(i),rgb)
  shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.95
  if i==5: shader.inputs['Emission Strength'].default_value=0
  materials[variant]['effect'].append(mat)

def select_variant(variant):
 m=materials[variant];body.data.materials[0]=m['skin'];body.data.materials[1]=m['iris'];body.data.materials[3]=m['bone']
 for o in scene.objects:
  if o.get('material_role') in ('wing','wing_strut'): o.data.materials[0]=wing
  if o.get('material_role')=='horn': o.data.materials[0]=m['bone']
  if o.get('material_role')=='death_effect':
   for i,mat in enumerate(m['effect']): o.data.materials[i]=mat
 scene['selected_palette']=variant

for variant in 'abc':
 select_variant(variant);exporter.export(scene,P/'delivery'/f'mm6_flying_demon_{variant}.glb')
select_variant('a');exporter.activate(scene,'Flight',0)
for other in list(bpy.data.scenes):
 if other!=scene: bpy.data.scenes.remove(other,do_unlink=True)
for mat in list(bpy.data.materials):
 if (mat.users==0 or (mat.use_fake_user and mat.users==1)) and not mat.name.startswith('Flying_'): bpy.data.materials.remove(mat)
for action in list(bpy.data.actions):
 if action.users==0 or (action.use_fake_user and action.users==1): bpy.data.actions.remove(action)
bpy.data.orphans_purge(do_recursive=True)
scene.frame_start=0;scene.frame_end=36
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=3.1
camera.location=(0,-6,1.2);camera.rotation_euler=(Vector((0,.12,1.10))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=900;scene.render.resolution_y=900;scene.eevee.taa_render_samples=48
scene.view_settings.view_transform='Standard'
for name,pos,power in [('Flying_Key',(-3,-4,5),500),('Flying_Fill',(3,1,3),250)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=4
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
text=bpy.data.texts.new('SELECT_ANIMATION_AND_PALETTE.py')
text.write('''# Run in Blender's Text Editor. Space plays the selected clip.
CLIP = 'Flight'  # Flight, Attack, Hit, Death, Ash_Remains
PALETTE = 'a'   # a purple/blue, b ochre/amber, c dark red/orange
import bpy
scene=bpy.context.scene
ends={'Flight':36,'Attack':36,'Hit':36,'Death':42,'Ash_Remains':6}
assert CLIP in ends and PALETTE in 'abc'
for o in scene.objects:
 role=o.get('material_role')
 if role=='body':
  o.data.materials[0]=bpy.data.materials['Flying_'+PALETTE.upper()+'_Skin']
  o.data.materials[1]=bpy.data.materials['Flying_'+PALETTE.upper()+'_Iris']
  o.data.materials[3]=bpy.data.materials['Flying_'+PALETTE.upper()+'_Bone']
 if role=='horn': o.data.materials[0]=bpy.data.materials['Flying_'+PALETTE.upper()+'_Bone']
 if role=='death_effect':
  for i in range(6): o.data.materials[i]=bpy.data.materials['Flying_'+PALETTE.upper()+'_Effect_'+str(i)]
 for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
  if owner and owner.animation_data:
   owner.animation_data.action=None
   for t in owner.animation_data.nla_tracks: t.mute=t.name!=CLIP
scene.render.fps=48;scene.frame_start=0;scene.frame_end=ends[CLIP];scene.frame_set(0)
''')
for image in bpy.data.images:
 if image.users and image.has_data and not image.packed_file:
  image.pack()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'delivery/mm6_flying_demon.blend'),compress=True)
print('Saved packed editable master and three synchronized PBR animated exports.',flush=True)
