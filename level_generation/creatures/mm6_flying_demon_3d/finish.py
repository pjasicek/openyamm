"""Portable source-derived disintegration, UV freeze and body-only texture upload."""
import math, json, hashlib
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector

P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animations.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
body=next(o for o in scene.objects if o.get('material_role')=='body')
visibility=rig.parent
clips={'Flight':36,'Attack':36,'Hit':36,'Death':42,'Ash_Remains':6}
for o in list(scene.objects):
 if o.name=='Demon_Death_Plume': bpy.data.objects.remove(o,do_unlink=True)
ash=scene.objects['Demon_Ash_Remains'];ash.name='Flying_Demon_Ash';ash.hide_render=False;ash.hide_set(False)
body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))

def material(name,rgb,emission=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*[v**2.2 for v in rgb],1)
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.95
 if emission: bs.inputs['Emission Color'].default_value=m.diffuse_color;bs.inputs['Emission Strength'].default_value=1.5
 return m
def push(owner,action,clip):
 owner.animation_data.action=None;t=owner.animation_data.nla_tracks.new();t.name=clip
 strip=t.strips.new(clip,0,action);strip.action_slot=action.slots[0];t.mute=True
def visibility_tracks(obj,kind):
 obj.animation_data_clear()
 for clip,end in clips.items():
  obj.animation_data_create();action=bpy.data.actions.new(obj.name+'_'+clip);obj.animation_data.action=action
  if kind=='body': rows=[(0,0),(end,0)] if clip=='Ash_Remains' else ([(0,1),(24,0),(end,0)] if clip=='Death' else [(0,1),(end,1)])
  else: rows=[(0,int(clip==('Death' if kind=='effect' else 'Ash_Remains'))),(end,int(clip==('Death' if kind=='effect' else 'Ash_Remains')))]
  for frame,value in rows: obj.scale=(value,)*3;obj.keyframe_insert('scale',frame=frame)
  for c in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
   for key in c.keyframe_points: key.interpolation='CONSTANT'
  push(obj,action,clip)
 obj.scale=(1,1,1) if kind=='body' else (0,0,0)
visibility_tracks(visibility,'body');visibility_tracks(ash,'ash')

pixels=np.load(P/'work/effect_pixels.npz');rng=np.random.default_rng(61007)
counts=[760,300,100];count=sum(counts);tetra=np.array([[0,0,1],[-.65,-.48,-.45],[.65,-.48,-.45],[0,.7,-.45]])
verts=np.tile(tetra*.000001,(count,1));faces=[[4*i+a,4*i+b,4*i+c] for i in range(count) for a,b,c in [(0,1,2),(0,2,3),(0,3,1),(1,3,2)]]
mesh=bpy.data.meshes.new('Flying_Disintegration_Morphs');mesh.from_pydata(verts,[],faces);mesh.update()
effect=bpy.data.objects.new('Flying_Demon_Disintegration',mesh);scene.collection.objects.link(effect);effect['material_role']='death_effect'
colors=[(.10,.55,.97),(.22,.70,1),(.42,.78,1),(.75,.89,1),(1,1,1),(.10,.07,.09)]
for i,c in enumerate(colors): mesh.materials.append(material('Fly_A_Effect_'+str(i),c,i<5))
for face in mesh.polygons:
 particle=face.index//4;face.material_index=particle%4 if particle<760 else 4 if particle<1060 else 5
effect.shape_key_add(name='Basis');references=[]
depth=rng.uniform(-.30,.24,count);rotation=rng.uniform(-math.pi,math.pi,count)
for index,letter in enumerate('abcdefg'):
 coords=[];manifest={'source':'wdmdth'+letter+'0','classes':{}}
 particle=0
 for category,amount in zip(('blue','white','dark'),counts):
  mask=pixels[letter+'_'+category];yy,xx=np.where(mask);manifest['classes'][category]=int(len(xx))
  if len(xx):
   order=np.lexsort((xx,yy));select=np.linspace(0,len(order)-1,amount).astype(int)
   points=np.column_stack((xx[order[select]],yy[order[select]]))
   size=min(.031,max(.004,.0066*math.sqrt(len(xx)/amount)*.92))
  else: points=np.tile([225,150],(amount,1));size=.000001
  for point in points:
   x=(point[0]-225)*.0066;z=(355-point[1])*.0066+.16
   angle=rotation[particle]+index*.37;rot=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
   shape=(tetra*size*rng.uniform(.7,1.3))@rot.T+np.array([x,depth[particle]*(.5 if index<2 else 1),z])
   coords.extend(shape);particle+=1
 key=effect.shape_key_add(name='Native_'+letter.upper());key.data.foreach_set('co',np.asarray(coords,dtype=np.float32).ravel());references.append(manifest)
key=effect.shape_key_add(name='End_Empty');key.data.foreach_set('co',verts.astype(np.float32).ravel())
keys=mesh.shape_keys
for clip,end in clips.items():
 keys.animation_data_create();action=bpy.data.actions.new('Flying_Plume_'+clip);keys.animation_data.action=action
 for frame in range(end+1):
  phase=min(frame/6,7);index=min(int(phase),6);u=phase-index
  if phase==7: index=7;u=0
  for i,key in enumerate(list(keys.key_blocks)[1:]):
   key.value=(float(i==index)*(1-u)+float(i==index+1)*u) if clip=='Death' else 0
   key.keyframe_insert('value',frame=frame)
 for c in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
  for point in c.keyframe_points: point.interpolation='LINEAR'
 push(keys,action,clip)
visibility_tracks(effect,'effect')
effect['source']='Native blue/white/charred pixel envelopes; depth and small tetrahedral fragments are authored 3D extrapolation.'
effect['palette_variants']='A blue-white / B gold-peach / C red-yellow'
(P/'work/effects_manifest.json').write_text(json.dumps({'triangles':len(faces),'fragments':count,'morphs':8,
 'body_and_wings_disappear_s':.5,'plume_empty_s':.875,'representation':'glTF morph weights and STEP presentation-parent scale; no Blender particle dependency',
 'source_anchors':references,'limitation':'Native-derived volumetric faceted interpretation of a sprite effect, not recovered simulation.'},indent=2)+'\n')

def activate(clip,frame):
 for o in scene.objects:
  for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
   if owner and owner.animation_data:
    owner.animation_data.action=None
    for t in owner.animation_data.nla_tracks: t.mute=t.name!=clip
 scene.frame_set(frame);bpy.context.view_layer.update()

for o in scene.objects:
 if o.type=='MESH' and o.get('material_role') not in ('death_effect',) and o!=ash:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
activate('Flight',6)
clones=[];depsgraph=bpy.context.evaluated_depsgraph_get()
for o in list(scene.objects):
 if o.type!='MESH' or o==ash or o==effect: continue
 evaluated=o.evaluated_get(depsgraph);data=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=depsgraph)
 clone=bpy.data.objects.new('Upload_'+o.name,data);scene.collection.objects.link(clone);clone.matrix_world=o.matrix_world.copy();clones.append(clone)
for o in scene.objects: o.select_set(o in clones)
bpy.context.view_layer.objects.active=clones[0];bpy.ops.object.join();upload=bpy.context.object
neutral=material('Neutral_Texture_Upload',(.55,.55,.55));upload.data.materials.clear();upload.data.materials.append(neutral)
for f in upload.data.polygons: f.material_index=0
path=P/'work/texturing_upload.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_skins=False,export_normals=True,export_texcoords=True,export_yup=True)
upload_record={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pose':'Flight B / 0.125s, evaluated static surface',
 'vertices':len(upload.data.vertices),'triangles':len(upload.data.polygons),'rig':False,'actions':False,'effects':False,
 'uv':'Unique body/chest/horns and membrane sides; six dark struts intentionally share one chart per wing.'}
(P/'work/upload_manifest.json').write_text(json.dumps(upload_record,indent=2)+'\n')
bpy.data.objects.remove(upload,do_unlink=True)
activate('Flight',0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/texturing_master.blend'),compress=True)
for variant in 'abc':
 request={'model_url':'@file:work/texturing_upload.glb','ai_model':'meshy-7','enable_original_uv':True,'enable_pbr':True,'texture_resolution':'4k','target_formats':['glb'],
 'multiview_image_urls':['@file:references/'+variant+'/'+view+'.png' for view in ('front','left','back')]}
 (P/'requests'/('texture_'+variant+'.json')).write_text(json.dumps(request,indent=2)+'\n')
state=json.loads((P/'creature_3d_progress.json').read_text());state['current_stage']=3;state['current_substep']='three PBR texture jobs and exported-animation review'
state['stages']['model_and_rig']='complete';state['stages']['animation_and_finish']='in_progress'
state['next_action']={'owner':'codex','action':'Generate A/B/C PBR maps on the frozen static upload; retain animated master and verify maps against unchanged UV/surface.'}
(P/'creature_3d_progress.json').write_text(json.dumps(state,indent=2)+'\n')
print('Portable seven-phase disintegration and static upload prepared',upload_record,flush=True)
