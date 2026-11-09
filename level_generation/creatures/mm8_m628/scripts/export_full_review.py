"""Export the complete reduced rig with its authored fractional animation keys."""
import bpy,json,hashlib,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'))
from build_actor_lods import read_glb,accessor_bytes
import numpy as np
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for o in bpy.data.objects:o.select_set(o in [rig,body])
bpy.context.view_layer.objects.active=rig
out=P/'review/viewer/m628_full.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,
    export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=False,
    export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
    export_reset_pose_bones=True,export_anim_slide_to_zero=True)
d,b=read_glb(out);a=next(a for a in d['animations']if a['name']=='Attack')
channels={}
for c in a['channels']:
    n=d['nodes'][c['target']['node']]['name'];s=a['samplers'][c['sampler']]
    t=np.frombuffer(accessor_bytes(d,b,s['input']),dtype='<f4')
    if n in ['Arrow','StringTop','StringBottom']:
        channels[n+'/'+c['target']['path']]={'keys':len(t),'near_release':[float(x)for x in t if .90<x<.93]}
(P/'work/review_export_keys.json').write_text(json.dumps(channels,indent=2));print('EXPORTED PROP KEYS',channels)
assert channels and min(x['keys']for x in channels.values())>200,'Export discarded fractional prop keys'
manifest=json.loads((P/'review/viewer/manifest.json').read_text());sha=hashlib.sha256(out.read_bytes()).hexdigest()
manifest.update(revision='m628-full-clay-v1',default_model='m628_full',model=out.name,
    models=[{'id':'m628_full','label':'Complete clay motion','revision':'m628-full-clay-v1','url':out.name+'?v='+sha[:12],'sha256':sha}])
native={'Standing':'sa','Walking':'wa','Attack':'aa','Hit':'na','Death':'da','Dead':'de','Fidget':'fa'}
manifest['clips']={a.name:{'label':a.name,'duration':float(a.frame_range[1])/30,
    'mode':'loop'if a.name in ['Standing','Walking','Dead']else'once',
    'provenance':'Fitted local humanoid bow sources; authored grip, draw, bow flex, native upright carry and corpse endpoint.',
    'anchors':[{'time':0,'label':'Native','phase':'Native reference','source_images':['../../native/m628'+native[a.name]+'0.png']}]}
    for a in bpy.data.actions}
(P/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2))
