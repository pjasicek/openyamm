"""Mount explicit test-region travel, preserving original destinations and service presentations.

Only the isolated installation is changed. Two native map-edge roads lead to existing MM8 cities.
Their stable instances receive private copies of their original route profiles plus a daily return;
original profile rows and legacy event scripts remain intact.
"""
import csv
import hashlib
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]


def configure(assets):
    original=ROOT/'assets_dev/engine/data_tables'
    target=assets/'engine/data_tables'
    ids=json.loads((PROJECT/'source/ids.json').read_text())['travel']
    source_hashes={}
    def read(name,staged=False):
        path=(target if staged else original)/name
        if not staged:source_hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding='cp1252',newline='') as f:return list(csv.reader(f,delimiter='\t'))
    def write(name,rows):
        with (target/name).open('w',encoding='cp1252',newline='') as f:
            csv.writer(f,delimiter='\t',lineterminator='\n').writerows(rows)
    navigation=read('map_navigation.txt')
    assert not any(r and r[0].lower()=='lg01.odm' for r in navigation)
    row=['lg01.odm','-24576','24576','-24576','24576']+['0']*12+['']*12
    # Native navigation headings are degrees. Arrival coordinates are outside the original stable doors.
    row[5:8]=['out03.odm','2','90'];row[17:20]=['4040','13184','288']
    # Heading zero is the navigation table's "unspecified" sentinel; 360 explicitly faces east.
    row[14:17]=['out02.odm','1','360'];row[26:29]=['16960','-12512','0']
    navigation.append(row);write('map_navigation.txt',navigation)

    locations=read('transport_locations.txt');location=str(ids['return_location'])
    assert not any(r and r[0]==location for r in locations)
    anchor=next(a for a in json.loads((PROJECT/'source/lg01.semantic.json').read_text())['arrivals'] if a['id']=='stable')
    locations.append([location,'lg01.odm']+['x']*7+['1']+list(map(str,anchor['position']))+['512','0'])
    write('transport_locations.txt',locations)

    rules=read('house_rules.txt');section=None;profiles={}
    for r in rules:
        if not r:continue
        if not r[0].isdigit():section=r[0]
        elif section=='Stables':profiles[r[0]]=r
    clones=[]
    for house,old in [(452,'1'),(453,'2')]:
        new=str(ids['return_profiles'][str(house)])
        assert new not in profiles
        clones.append([new]+profiles[old][1:]+[location])
    end=next(i for i,r in enumerate(rules) if r and r[0]=='Boats')
    rules[end:end]=clones;write('house_rules.txt',rules)
    # stage_runtime has just rebuilt this from base + scoped Brackenford registrations.
    houses=read('house_data.txt',staged=True)
    for r in houses:
        if r and r[0] in ids['return_profiles']:
            assert r[2]=='Stables'
            r[1]=str(ids['return_profiles'][r[0]])
    write('house_data.txt',houses)
    report=dict(status='configured; functional evidence in review/shared_travel_followup.json',source_tables=source_hashes,
        native_edges=[dict(edge='west',destination='out02.odm',days=1),dict(edge='north',destination='out03.odm',days=2)],
        return_location=location,return_arrival=anchor,return_profiles=ids['return_profiles'],
        policy='Isolated test-world links; original stable routes retained, daily Brackenford return appended. Existing stable opening hours/quest behavior apply.')
    (PROJECT/'source/travel_registry.json').write_text(json.dumps(report,indent=2)+'\n')
