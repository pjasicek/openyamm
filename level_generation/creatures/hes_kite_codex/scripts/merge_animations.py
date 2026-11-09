"""Refresh all authored clips without changing the visually accepted LOD geometry."""
import copy,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
source=Glb(P/'export/hes_ashkite_lod0.glb');target=Glb(P/'work/hes_ashkite/r25_12.glb')
names={n.get('name'):i for i,n in enumerate(target.json['nodes'])}
for original in source.json['animations']:
 animation=copy.deepcopy(original)
 for sampler in animation['samplers']:
  for field in ['input','output']:
   old=sampler[field];sampler[field]=target.append_accessor(source.accessor(old),source.json['accessors'][old]['type'])
 for channel in animation['channels']:
  channel['target']['node']=names[source.json['nodes'][channel['target']['node']]['name']]
 index=next(i for i,a in enumerate(target.json['animations']) if a['name']==animation['name'])
 target.json['animations'][index]=animation
sm=Model(source);tm=Model(target);worst=0
for clip in sm.clips:
 for time in sm.clip_times(clip):
  sw=sm.world(sm.sample(clip,time));tw=tm.world(tm.sample(clip,time))
  for index in source.json['skins'][0]['joints']:
   delta=float(np.max(np.abs(sw[index]-tw[names[source.json['nodes'][index]['name']]])))
   worst=max(worst,delta)
assert worst<1e-5,worst
assert target.json['meshes']==Glb(P/'work/hes_ashkite/r25_12.glb').json['meshes']
target.write(P/'work/hes_ashkite/r25_12_animated.glb')
(P/'review/animation_merge.json').write_text(json.dumps({'clips':list(sm.clips),'max_joint_matrix_delta':worst,'lod_geometry_unchanged':True},indent=2)+'\n')
print('All clips transferred; joint matrix max delta',worst)
