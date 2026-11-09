"""Apply the shared repair.py image thresholds to each exact bound actor assembly."""
from pathlib import Path
import json,subprocess,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from prepare_repair import scores,passes
report={'gate':{'LOD2_outline_pct':6,'LOD2_colour':16,'LOD2_colour_allowance':'max(16, installed LOD1 colour + 3)','LOD3_outline_pct':13,'LOD3_colour':19.5},'scope':'exact four runtime assemblies at 450/180/72 pixel actor switch sizes; hidden family mantle omitted','tiers':{}}
for tier in ('a','b','c','boss'):
 audit=P/'work/lod_repair'/('assembly_'+tier)/'audit'
 with (audit/'scores.tsv').open('w') as out:subprocess.run([sys.executable,str(P.with_name('lod_repair_claude')/'scripts/lod_score.py'),str(audit)],stdout=out,check=True)
 table=scores(audit);lod1=table['installed',1]
 entry={'installed':{k:table['installed',k] for k in (1,2,3)},'repaired':{k:table['repaired',k] for k in (1,2,3)},'pass':{k:passes(table['repaired',k],k,lod1) for k in (2,3)}}
 report['tiers'][tier]=entry;print(tier,entry['repaired'],entry['pass'])
report['passed']=all(all(t['pass'].values()) for t in report['tiers'].values())
report['plan']=json.loads((P/'review/lod_plan.json').read_text())
(P/'review/lod_audit.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['passed'],'Full-actor LOD image gate failed'
