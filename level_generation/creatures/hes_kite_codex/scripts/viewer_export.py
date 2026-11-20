import bpy,sys,os,json,traceback,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
try:
 parts=json.loads((P/'export/attachments.json').read_text());models=[]
 for tier in 'abc':
  bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_animated_v3.blend'));r=bpy.data.objects['Ashkite_Rig'];body=bpy.data.objects['Ashkite'];r.animation_data.action=None
  for b in r.pose.bones:b.matrix_basis.identity()
  bpy.context.view_layer.update()
  for node in body.data.materials[0].node_tree.nodes:
   if node.type=='TEX_IMAGE' and 'basecolor' in node.image.name:node.image=bpy.data.images.load(str(P/('work/tier_'+tier+'.png')))
  edge=bpy.data.objects['Static_Edges']
  if tier!='c':bpy.data.objects.remove(edge,do_unlink=True)
  else:
   for v in edge.data.vertices:v.co+=v.normal*.001
  for a in parts:
   if tier.upper() not in a['tiers']:continue
   before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'work/attachments_raw'/a['model']))
   for ob in set(bpy.data.objects)-before:
    if ob.type!='MESH':continue
    group=ob.vertex_groups.new(name=a['node']);group.add(list(range(len(ob.data.vertices))),1,'REPLACE');mod=ob.modifiers.new('Carrier','ARMATURE');mod.object=r;ob.parent=r
  r.animation_data.action=bpy.data.actions['Fly'];bpy.context.scene.frame_set(1)
  bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/review_'+tier+'.blend')))
  for ob in bpy.data.objects:ob.select_set(ob.type in ['MESH','ARMATURE'])
  bpy.context.view_layer.objects.active=r;dest=P/('review/viewer/hes_ashkite_'+tier+'.glb')
  bpy.ops.export_scene.gltf(filepath=str(dest),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
  sha=hashlib.sha256(dest.read_bytes()).hexdigest();models.append({'id':'kite_'+tier,'label':{'a':'A: Ashkite (10310)','b':'B: Spire Kite (10311)','c':'C: Storm Kite (10312)'}[tier],'revision':'ashkite_v5_flight_legs','url':dest.name+'?v='+sha[:12],'sha256':sha})
 clips=json.loads((P/'review/runtime_gates.json').read_text())
 manifest={'revision':'ashkite_v5_flight_legs','model':'hes_ashkite_b.glb','default_model':'kite_b','default_clip':'Fly','feedback':'feedback/user_feedback.json','model_sha256':models[1]['sha256'],'models':models,'clips':{n:{'label':n,'duration':d['seconds'],'mode':'loop' if n in ['Fly','Run','Dead'] else 'once','provenance':'locally authored four-wing rig','anchors':[{'time':0,'label':n,'phase':'HD appearance reference','source_images':['../../references_hd/00_three_quarter.png']}]} for n,d in clips.items()}}
 manifest['clips']['Attack']['anchors']=[{'time':frame/24,'label':label,'phase':label,'source_images':['../../references_hd/00_three_quarter.png']} for frame,label in [(0,'Ready'),(6,'Wind-up'),(8,'Coiled'),(11,'Bite'),(13,'Follow-through'),(18,'Recover')]]
 feedback=P/'review/viewer'/manifest['feedback']
 feedback.parent.mkdir(parents=True,exist_ok=True)
 if not feedback.exists():feedback.write_text('{"findings": []}\n')
 assert isinstance(json.loads(feedback.read_text())['findings'],list)
 (P/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Viewer: 3 tiers x 8 clips',flush=True)
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
