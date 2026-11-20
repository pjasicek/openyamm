"""Use the established variant, attachment and head-atlas tools on independently rebaked levels."""
import sys,json,subprocess,copy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];OUT=P/'export';sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'tools'))
from build_actor_lods import read_glb,write_glb
def run(*args):subprocess.run([sys.executable,'-B',*map(str,args)],check=True)
cfg0=json.loads((P/'textures/natm_ramps.json').read_text())
for level in range(4):
 raw=OUT/f'mm6_natm_raw_lod{level}.glb';doc,buf=read_glb(raw)
 assert len(doc.get('skins',[]))==1
 mesh=next(n['mesh']for n in doc['nodes']if n.get('name')=='Natm');doc['meshes'][mesh].setdefault('extras',{})['openyamm_lods']=[]
 assert not(set(doc.get('extensionsUsed',[])) - {'KHR_materials_variants'}),doc.get('extensionsUsed')
 write_glb(raw,doc,buf);cfg=copy.deepcopy(cfg0)
 for item,kind,index in zip(cfg['materials'],['body','body','spear','buckler'],[0,1,0,0]):item['mask']=str(OUT/f'textures_lod{level}/{kind}/{index}_region_mask.png')
 path=OUT/f'ramps_lod{level}.json';path.write_text(json.dumps(cfg,indent=2));variant=OUT/f'mm6_natm_variants_lod{level}.glb'
 run(P.parent/'claude_shared/region_variants.py',raw,variant,path,'--extra','Natm','openyamm_specular=1','--extra','Natm','openyamm_specular_mask=true','--extra','Natm','pbr.metallicFactor=0')
 run(ROOT/'tools/split_attachment.py',variant,'--joint','Spear','--body',OUT/f'natm_without_spear_lod{level}.glb','--attachment',OUT/f'mm6_natm_spear_lod{level}.glb')
 run(ROOT/'tools/split_attachment.py',OUT/f'natm_without_spear_lod{level}.glb','--joint','Buckler','--body',OUT/f'natm_body_separate_lod{level}.glb','--attachment',OUT/f'mm6_natm_buckler_lod{level}.glb')
 run(ROOT/'tools/merge_head_material.py',OUT/f'natm_body_separate_lod{level}.glb',OUT/f'mm6_natm_body_lod{level}.glb')
snapshot=P/'work/atlas_input';snapshot.mkdir(exist_ok=True)
for kind in ['body','spear','buckler']:
 for level in range(4):shutil.copy2(OUT/f'mm6_natm_{kind}_lod{level}.glb',snapshot/f'mm6_natm_{kind}_lod{level}.glb')
if '--prepare-only'in sys.argv:sys.exit(0)
run(P/('scripts/review1_reuse_atlas.py'if '--reuse-atlas'in sys.argv else'scripts/review4_atlas.py'))
if '--reuse-atlas'not in sys.argv:
 for kind in ['body','spear','buckler']:
  for level in range(4):
   name=f'mm6_natm_{kind}_lod{level}.glb';shutil.copy2(OUT/name,P/'work/shared_atlas_cache'/name)
run(P/'scripts/pack_lods.py')
run(P/'scripts/shrink_shadow_lods.py',OUT/'mm6_natm_body_packed.glb',OUT/'mm6_natm.glb')
print('RUNTIME_PACK_COMPLETE')
