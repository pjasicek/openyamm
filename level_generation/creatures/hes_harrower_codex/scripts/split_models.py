"""Split caste gear using the Trooper's multi-material attachment exporter."""
from pathlib import Path
import json,subprocess,sys,shutil
P=Path(__file__).resolve().parents[1]
common=[{'name':'hes_harrower_cap_'+s.lower(),'joint':'B_'+s+'_Pauldron','materials':['HHW_']} for s in 'LR']
for kind in ('family','vreth'):
 prefix='hes_harrower' if kind=='family' else 'hes_vreth'
 items=[{'name':prefix+'_blade_'+s.lower(),'joint':'Blade_'+s,'materials':['HHW_']} for s in 'LR']
 items += [{'name':prefix+'_crest','joint':'Harrower_Crest','materials':['HHW_']},{'name':prefix+'_trophies','joint':'Harrower_Trophies','materials':['HHW_']}]
 items += common
 path=P/'work'/('items_'+kind+'.json');path.write_text(json.dumps(items,indent=2)+'\n')
 body=P/'export/hes_harrower.glb' if kind=='family' else P/'work/vreth_body_check.glb'
 subprocess.run([sys.executable,str(P/'scripts/split_attachments.py'),str(P/'work'/('assembly_'+kind+'_lods.glb')),'--body',str(body),'--items',str(path),'--outdir',str(P/'export')],check=True)
 shutil.copy(P/'export/attachments.json',P/'review'/('attachments_'+kind+'.json'))

# Head protection in the assembled reducer otherwise leaves rigid crests unchanged at LOD1.
for stem in ('hes_harrower_crest','hes_vreth_crest'):
 source=P/'export'/f'{stem}.glb';out=P/'work'/f'{stem}_initial_lods.glb'
 with (P/'review'/f'{stem}_lod1.log').open('w') as log:
  subprocess.run(['/tmp/lancer_lod_venv/bin/python',str(P.with_name('lod_repair_claude')/'scripts/build_lods.py'),str(source),'Harrower_Crest',str(out),'1:0.5,2:0.25,3:0.125'],stdout=log,stderr=subprocess.STDOUT,check=True)
 shutil.copy(out,source)
originals=P/'work/lod_originals';originals.mkdir(exist_ok=True)
for source in (P/'export').glob('*.glb'):shutil.copy(source,originals/source.name)
