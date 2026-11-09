"""Lossless 2x Death retiming; all baked poses and non-Death asset bytes are preserved."""
import bpy, copy, hashlib, json, struct, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
BEFORE=P/'review/round3/before'
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes
records=[]
for source in sorted(list((BEFORE/'export').glob('*.glb'))+list((BEFORE/'review/viewer').glob('*.glb'))):
 doc,original=read_glb(source)
 death=next((a for a in doc.get('animations',[]) if a['name']=='Death'),None)
 if death is None:
  assert (P/source.relative_to(BEFORE)).read_bytes()==source.read_bytes()
  continue
 before_doc=copy.deepcopy(doc);binary=bytearray(original)
 inputs={s['input'] for s in death['samplers']}
 other={s[k] for a in doc['animations'] for s in a['samplers'] for k in ['input','output'] if a is not death or k=='output'}
 assert not inputs&other, 'Retiming must not mutate shared/non-time accessors'
 counts=[];old_end=0.
 for index in inputs:
  a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
  assert a['type']=='SCALAR' and a['componentType']==5126 and 'sparse' not in a
  assert view.get('byteStride',4)==4
  offset=view.get('byteOffset',0)+a.get('byteOffset',0)
  times=struct.unpack('<'+'f'*a['count'],accessor_bytes(doc,original,index))
  assert times[0]==0 and all(x<y for x,y in zip(times,times[1:]))
  new=[t*.5 for t in times];struct.pack_into('<'+'f'*len(new),binary,offset,*new)
  for k in ['min','max']:
   if k in a:a[k]=[x*.5 for x in a[k]]
  counts.append(len(times));old_end=max(old_end,times[-1])
 assert all(s.get('interpolation','LINEAR') in ['LINEAR','STEP'] for s in death['samplers'])
 target=P/source.relative_to(BEFORE);write_glb(target,doc,bytes(binary));target.chmod(0o644)
 # Reverse just the time transform: the complete original document and binary must be restored.
 check,buf=read_glb(target);restored=bytearray(buf)
 for index in inputs:
  a=check['accessors'][index];view=check['bufferViews'][a['bufferView']];offset=view.get('byteOffset',0)+a.get('byteOffset',0)
  vals=struct.unpack('<'+'f'*a['count'],accessor_bytes(check,buf,index));struct.pack_into('<'+'f'*len(vals),restored,offset,*[t*2 for t in vals])
  for k in ['min','max']:
   if k in a:a[k]=[x*2 for x in a[k]]
 assert check==before_doc and bytes(restored)==original, target
 records.append({'path':str(target.relative_to(P)),'old_duration':old_end,'new_duration':old_end*.5,'time_accessor_counts':counts,'all_pose_data_unchanged':True,'non_death_document_and_binary_unchanged':True,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
for rel in [*[f'work/final_lod{i}.blend' for i in range(4)],'export/mm6_mep.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(BEFORE/rel));action=bpy.data.actions['Death'];start,end=map(float,action.frame_range)
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:
      for co in [key.co,key.handle_left,key.handle_right]:co.x=start+(co.x-start)*.5
     curve.update()
 action.frame_start=start;action.frame_end=start+(end-start)*.5
 assert abs((action.frame_range[1]-action.frame_range[0])-(end-start)*.5)<1e-5
 bpy.ops.wm.save_as_mainfile(filepath=str(P/rel));(P/rel).chmod(0o644)
info=json.loads((BEFORE/'export/export_info.json').read_text());info['clips']['Death']['duration']*=.5;info['clips']['Death']['staff_release']=.075;info['review_revision']='mm6_mep_codex_review_round3';info['measurement_source']='review/round3/gates/gates.json';(P/'export/export_info.json').write_text(json.dumps(info,indent=2)+'\n')
config=json.loads((BEFORE/'gates.json').read_text())
for prop in config['props']:
 for hand in prop.get('hands',[]):
  if 'Death' in hand.get('intervals',{}):hand['intervals']['Death']=[[t*.5 for t in interval] for interval in hand['intervals']['Death']]
(P/'gates.json').write_text(json.dumps(config,indent=2)+'\n')
(P/'review/round3/timing_identity.json').write_text(json.dumps({'method':'Halve Death timestamps, retaining all 873 uniform baked poses at effective 480 Hz; constant channels keep endpoints. No additional interpolation or decimation. Reverse-transform equality checks complete document/binary identity.','old_duration_s':109/30,'new_duration_s':109/60,'old_release_s':.15,'new_release_s':.075,'dead_unchanged':True,'files':records},indent=2)+'\n')
print('ROUND3_RETIMED',len(records),109/30,109/60,flush=True)
