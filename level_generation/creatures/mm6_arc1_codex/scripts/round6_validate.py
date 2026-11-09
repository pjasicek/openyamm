"""Verify the timing-only export, all retained pose/map data, staged bindings and viewer."""
import sys,json,hashlib,subprocess,collections,shutil
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P/'review/round6';B=R/'baseline';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'scope':'Review round 6: animation timing and loop audit; all other artwork accepted as-is','files':{},'preservation':{}}
def channels(d,b):
 out={}
 for a in d.get('animations',[]):
  for c in a['channels']:
   t=c['target'];s=a['samplers'][c['sampler']]
   out[a['name'],d['nodes'][t['node']]['name'],t['path']]=(accessor_array(d,b,s['input']),accessor_array(d,b,s['output']))
 return out
memory=0;images=0
for name in ['mm6_arc1.glb','mm6_arc1_bow.glb','mm6_arc1_arrow.glb']:
 file=P/'export'/name;d,b=read_glb(file);old,ob=read_glb(B/'export'/name);triangles={}
 assert d['nodes']==old['nodes'] and d['materials']==old['materials']
 for m,om in zip(d['meshes'],old['meshes']):
  triangles[m['name']]=0
  for prim,op in zip(m['primitives'],om['primitives']):
   assert prim['attributes'].keys()==op['attributes'].keys()
   for k,ai in prim['attributes'].items():assert np.array_equal(accessor_array(d,b,ai),accessor_array(old,ob,op['attributes'][k])),(name,k)
   assert np.array_equal(accessor_array(d,b,prim['indices']),accessor_array(old,ob,op['indices']))
   triangles[m['name']]+=len(accessor_array(d,b,prim['indices']))//3
 assert len(d['images'])==len(old['images'])
 for im,oim in zip(d['images'],old['images']):
  v=d['bufferViews'][im['bufferView']];ov=old['bufferViews'][oim['bufferView']]
  assert b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]==ob[ov.get('byteOffset',0):ov.get('byteOffset',0)+ov['byteLength']]
 for i in range(len(d['images'])):
  im=image_of(d,b,i)[0];memory+=im.width*im.height*4;images+=1
 report['files']['export/'+name]={'sha256':sha(file),'bytes':file.stat().st_size,'triangles':triangles,'changed':sha(file)!=sha(B/'export'/name)}
 report['preservation'][name]='All decoded geometry, UV, skin weights, nodes, materials and embedded PNG bytes equal R5'
 if name!='mm6_arc1.glb':assert sha(file)==sha(B/'export'/name);continue
 actual=channels(d,b);source=channels(old,ob);assert actual.keys()==source.keys()
 max_time_error=0
 for k,(t,v)in actual.items():
  ot,ov=source[k];assert np.array_equal(v,ov),k
  expected=(ot/1.5).astype(np.float32)if k[0]in ('Attack','Cast')else ot
  assert np.array_equal(t,expected),k
  if k[0]in ('Attack','Cast'):max_time_error=max(max_time_error,float(abs(t.astype(float)*1.5-ot).max()))
 attack={k[1:]:v for k,v in actual.items()if k[0]=='Attack'};cast={k[1:]:v for k,v in actual.items()if k[0]=='Cast'}
 assert attack.keys()==cast.keys()and all(all(np.array_equal(x,y)for x,y in zip(attack[k],cast[k]))for k in attack)
 report['cast_exact_attack_copy']={'channels':len(attack),'equal':True};report['all_pose_outputs_equal_R5']=True;report['time_scaling_max_float32_error_s']=max_time_error
 assert len(d['skins'][0]['joints'])==63 and len(d['animations'])==8
report['texture_sets']={'images':images,'decoded_rgba8_base_mib':memory/1048576,'unchanged_from_R5':True,'dilated_margin_px':16};assert images==10 and memory/1048576==53.125
native=json.loads((P/'source/native_inputs.json').read_text());assert all(sha(P.parents[2]/f)==h for f,h in native.items());report['native_files_unchanged']=len(native)
r=subprocess.run([sys.executable,str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],capture_output=True,text=True);(R/'check_bindings.log').write_text(r.stdout+r.stderr);r.check_returncode();assert 'BAD'not in r.stdout+r.stderr
report['bindings']='PASS, no BAD line';report['integration_actors_yml_changed']=True
assert (P/'integration/actors.yml').read_text()==(B/'integration/actors.yml').read_text().replace('impact: 1.2','impact: 0.8')
report['integration_events']={'all_three_tiers':['attack_melee: 0.8','attack_ranged: 0.8','cast: 0.8'],'launch_socket':'Socket_Arrow_Release'}
checker=json.loads((P/'review/check_viewer.log').read_text());assert checker['ready']=='true'and checker['switched']==24 and not checker['failed']and not checker['consoleErrors'];report['viewer']=checker
for name in ['check_viewer.log','browser_capture.log']:shutil.copy2(P/'review'/name,R/name)
shared=json.loads((R/'shared_final/gates.json').read_text());baseline=json.loads((B/'review/round5/shared_final/gates.json').read_text());key=lambda row:tuple(str(row[k])for k in ['asset','clip','lod','gate','region']);old={key(r):r for r in baseline['gates']};new={key(r):r for r in shared['gates']}
compare={'baseline_counts':baseline['counts'],'final_counts':shared['counts'],'new_failures':[r for k,r in new.items()if r['status']=='FAIL'and old.get(k,{}).get('status')!='FAIL'],'resolved_failures':[r for k,r in old.items()if r['status']=='FAIL'and new.get(k,{}).get('status')=='PASS'],'failure_categories':dict(collections.Counter(r['gate']for r in shared['gates']if r['status']=='FAIL'))}
(R/'shared_comparison.json').write_text(json.dumps(compare,indent=2));report['shared_runner']={'status':shared['status'],'counts':shared['counts'],'report':'review/round6/shared_final/gates.md'}
feet=[r for r in shared['gates']if r['clip']in ('Attack','Cast')and r['gate']in ('rest_sole_height_mm','rest_sole_tilt_deg','floor_penetration_mm')and any(x in r['lod']for x in ['colour0','colour1','colour2'])];assert all(r['status']=='PASS'for r in feet)
report['shooting_feet_visible_lods']={k:max(r['worst']for r in feet if r['gate']==k)for k in set(r['gate']for r in feet)}
report['loop_endpoints']=json.loads((R/'loop_endpoints.json').read_text());report['retiming']=json.loads((R/'retiming.json').read_text());report['status']=shared['status'];report['scoped_review_status']='PASS';report['technical_completion']='pending_shared_gate_findings'
for rel in ['integration/actors.yml','work/rig_equipped.blend','work/rig_textured.blend','work/runtime_authoring.blend']+[f'work/round2/lod{i}.blend'for i in range(4)]:report['files'][rel]={'sha256':sha(P/rel),'bytes':(P/rel).stat().st_size}
(P/'review/delivery_validation.json').write_text(json.dumps(report,indent=2));(R/'validation.json').write_text(json.dumps(report,indent=2))
print('PASS: 1.5x clocks; every pose output unchanged; Cast identical; PNG/mesh/weights unchanged; native sources unchanged; bindings no BAD; 24 viewer switches. Shared:',shared['counts'])
