"""Use the standard NLA exporter; supply explicit portable effect/reset channels."""
from pathlib import Path
import sys, struct
import bpy

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb, write_glb, append_accessor
CLIPS={'Flight':36,'Attack':36,'Hit':36,'Death':42,'Ash_Remains':6}

def activate(scene,clip,frame):
 bpy.context.window.scene=scene
 for o in scene.objects:
  for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
   if owner and owner.animation_data:
    owner.animation_data.action=None
    for track in owner.animation_data.nla_tracks: track.mute=track.name!=clip
 scene.frame_set(frame);bpy.context.view_layer.update()

def export(scene,path):
 rig=next(o for o in scene.objects if o.type=='ARMATURE')
 effect=scene.objects['Flying_Demon_Disintegration'];ash=scene.objects['Flying_Demon_Ash'];visibility=rig.parent
 morph=[]
 for frame in range(43):
  activate(scene,'Death',frame);morph.append([k.value for k in effect.data.shape_keys.key_blocks][1:])
 activate(scene,'Flight',0)
 saved={};matrices={o:o.matrix_basis.copy() for o in scene.objects}
 # Do not let zero-scale presentation parents corrupt the exporter's bind/evaluation.
 # Their animation is restored below and written as explicit STEP glTF channels.
 for o in scene.objects:
  for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
   if owner and owner!=rig and owner.animation_data:
    saved[owner]=[(t.name,t.strips[0].action,t.strips[0].action_slot,t.mute) for t in owner.animation_data.nla_tracks]
    owner.animation_data_clear()
  if o in (visibility,effect,ash): o.scale=(1,1,1)
  o.hide_set(False);o.select_set(o.type not in ('CAMERA','LIGHT'))
 for t in rig.animation_data.nla_tracks: t.mute=True
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,
  export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,export_force_sampling=True,
  export_frame_step=1,export_all_influences=True,export_def_bones=False,export_optimize_animation_size=False,
  export_morph=True,export_morph_animation=False,export_normals=True,export_cameras=False,export_lights=False,export_extras=True)
 for owner,tracks in saved.items():
  owner.animation_data_create()
  for name,action,slot,mute in tracks:
   t=owner.animation_data.nla_tracks.new();t.name=name;s=t.strips.new(name,0,action);s.action_slot=slot;t.mute=mute
 for o,m in matrices.items(): o.matrix_basis=m
 activate(scene,'Flight',0)
 doc,payload=read_glb(path);binary=bytearray(payload);nodes={n['name']:i for i,n in enumerate(doc['nodes'])}
 assert set(a['name'] for a in doc['animations'])==set(CLIPS)
 def accessor(rows,kind):
  flat=[float(v) for row in rows for v in (row if isinstance(row,(tuple,list)) else [row])]
  item={'componentType':5126,'count':len(flat)//{'SCALAR':1,'VEC3':3}[kind],'type':kind}
  if kind=='SCALAR': item.update(min=[min(flat)],max=[max(flat)])
  return append_accessor(doc,binary,item,struct.pack('<'+'f'*len(flat),*flat))
 def channel(animation,node,path,times,rows,kind,interpolation):
  sampler=len(animation['samplers']);animation['samplers'].append({'input':accessor(times,'SCALAR'),'output':accessor(rows,kind),'interpolation':interpolation})
  animation['channels'].append({'sampler':sampler,'target':{'node':nodes[node],'path':path}})
 doc['nodes'][nodes[effect.name]]['scale']=[0,0,0];doc['nodes'][nodes[ash.name]]['scale']=[0,0,0];doc['nodes'][nodes[visibility.name]]['scale']=[1,1,1]
 for animation in doc['animations']:
  clip=animation['name'];end=CLIPS[clip]/48
  for o,kind in [(visibility,'body'),(ash,'ash'),(effect,'effect')]:
   times=[0,end];value=int(clip==('Ash_Remains' if kind=='ash' else 'Death')) if kind!='body' else int(clip!='Ash_Remains')
   rows=[[value]*3,[value]*3]
   if kind=='body' and clip=='Death': times=[0,.5,end];rows=[[1]*3,[0]*3,[0]*3]
   channel(animation,o.name,'scale',times,rows,'VEC3','STEP')
  times=[f/48 for f in range(43)] if clip=='Death' else [0,end]
  rows=morph if clip=='Death' else [[0]*8,[0]*8]
  channel(animation,effect.name,'weights',times,rows,'SCALAR','LINEAR')
 doc['buffers'][0]['byteLength']=len(binary);write_glb(path,doc,binary)
 print('Exported',path.name,'five clips, explicit visibility and eight morphs',flush=True)

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/texturing_master.blend'))
 export(bpy.context.scene,P/'work/clay_animated.glb')
