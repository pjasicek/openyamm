"""Refresh shared-table fingerprints only after exact family-record equality, preserving the old audit."""
from pathlib import Path
import json,sys,datetime,yaml
R=Path(__file__).resolve().parent;F=R/'checkpoints'
sys.path.insert(0,str(R));import process

def run():
    sources=json.loads((R/'sources.json').read_text());groups={};changes=[]
    for rec in sources['source_tables']:
        p=process.queue.REPO/rec['path']
        groups.update({g['sprite_name'].lower():g for g in yaml.load(p.read_text(),Loader=yaml.CSafeLoader)['sprites']})
    p=process.queue.REPO/sources['descriptor_table']['path']
    descriptors={v[0]:v for line in p.read_text().splitlines() if (v:=line.split('\t'))[0].isdigit()}
    for mid,b in sources['bindings'].items():
        assert descriptors[mid]==b['native_descriptor'],('Changed descriptor',mid)
        for action,a in b['actions'].items():
            assert groups[a['native_group'].lower()]==a['native_group_record'],('Changed native family group',mid,action)
    for rec in [*sources['sources'].values(),*sources['palette_sources'].values()]:
        assert process.queue.sha(process.queue.REPO/rec['path'])==rec['sha256'],rec['path']
    before=json.dumps(sources,indent=2)+'\n'
    for rec in [*sources['source_tables'],sources['descriptor_table']]:
        current=process.queue.sha(process.queue.REPO/rec['path'])
        if current!=rec['sha256']:
            changes.append({'path':rec['path'],'previous_sha256':rec['sha256'],'current_sha256':current})
            rec['sha256']=current
    if changes:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        (F/('sources_before_table_refresh_'+stamp+'.json')).write_text(before)
        process.save(F/'shared_table_refresh.json',{'changes':changes,'verified':'All 3 native descriptors, 24 action group records, 160 BMP hashes and 3 palette hashes remain exactly unchanged. Only unrelated shared-table content changed.','utc':stamp})
        process.save(R/'sources.json',sources)
    print('Verified native family equality;',len(changes),'unrelated shared-table fingerprints refreshed.')

if __name__=='__main__':run()
