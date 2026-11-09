from pathlib import Path
import importlib.util,json,hashlib,numpy as np
p=Path(__file__).resolve().parent
# Load only existing accessors helper definitions, avoiding the checker side effects.
s=(p/'check_assets.py').read_text().split('exports=')[0];n={'__file__':str(p/'check_assets.py')};exec(s,n)
old,ob=n['read_glb'](p/'work/before_death_correction.glb');new,nb=n['read_glb'](p/'delivery/mm6_flying_demon_a.glb')
assert old['nodes']==new['nodes'] and old['skins']==new['skins']
def animation_bytes(doc,buf,a):
 payload=b''.join(n['values'](doc,buf,s[field]).tobytes() for s in a['samplers'] for field in ('input','output'))
 return hashlib.sha256(payload).hexdigest()
report={'status':'pass','old_a_sha256':hashlib.sha256((p/'work/before_death_correction.glb').read_bytes()).hexdigest(),'new_a_sha256':hashlib.sha256((p/'delivery/mm6_flying_demon_a.glb').read_bytes()).hexdigest(),'unchanged_clips':{}}
for clip in ('Flight','Attack','Hit','Ash_Remains'):
 a=next(a for a in old['animations'] if a['name']==clip);b=next(a for a in new['animations'] if a['name']==clip)
 assert a==b and animation_bytes(old,ob,a)==animation_bytes(new,nb,b),clip
 report['unchanged_clips'][clip]={'all_channels_and_samples_byte_identical':True,'sha256':animation_bytes(new,nb,b)}
for i,(a,b) in enumerate(zip(old['meshes'],new['meshes'])):
 if i==next(node['mesh'] for node in new['nodes'] if node.get('name')=='Flying_Demon_Disintegration'):continue
 assert a==b
 for pr in a['primitives']:
  for accessor in [pr['indices'],*pr['attributes'].values()]:assert np.array_equal(n['values'](old,ob,accessor),n['values'](new,nb,accessor))
report['living_geometry_uvs_normals_weights_bind_and_ash_byte_identical']=True
(p/'work/death_change_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Four unaffected clips and all living/ash geometry preserved exactly.')
