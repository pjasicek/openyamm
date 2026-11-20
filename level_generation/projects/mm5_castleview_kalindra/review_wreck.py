"""Read back the bank-side wreck, submerged keel and reachable status-only binding."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

from author_props import ground_at
from prepare_wreck import FIT, PALETTE
from review_waymarks import fit

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read=lambda path:json.loads((PROJECT/path).read_text())
    semantic=read('implementation/source/mm5_sw.semantic.json')
    prop,=[p for p in semantic['props'] if p.get('kind')=='source wreck']
    assert prop['frontOrigin']==FIT['point'] and prop['originalObject']['sprite']==5
    assert math.dist(prop['frontOrigin'],prop['sourceFeature']['point'])==prop['placementChange']==640
    event,=[e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
    assert event['id']==prop['eventId']==read('implementation/feature_event_ids.json')[prop['semanticId']]
    path=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    native=parse_odm_file(path)['payload']
    model=native['bmodels'][event['bmodel_index']]
    assert len(model['faces'])==len(event['faces'])==474
    assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
    assert {f['texture_name'].lower() for f in model['faces']}==set(PALETTE.values())
    vertices=[[v[a] for a in 'xyz'] for v in model['vertices']]
    x,y=FIT['point']
    assert all(x-224<=v[0]<=x+224 and y-640<=v[1]<=y+640 for v in vertices)
    assert min(v[2] for v in vertices)==199 and max(v[2] for v in vertices)==1020
    height=bytes(native['height_map'])
    # The original source point stays beneath the bow; the stern intersects the dry bank by eight units.
    stern=[v for v in vertices if v[1]==FIT['contact'][1]]
    assert min(v[2] for v in stern)==248 and ground_at(height,FIT['contact'])==256
    rows=list(csv.DictReader((PROJECT/'implementation/terrain_rows.tsv').open(),delimiter='\t'))
    names={90+i:r['texture_name'] for i,r in enumerate(rows)}
    standing=FIT['standing']
    textures=[]
    for i in range(16):
        point=[standing[0]+96*math.cos(i*math.tau/16),standing[1]+96*math.sin(i*math.tau/16)]
        c,r=math.floor(point[0]/512+64),math.floor(64-point[1]/512)
        name=names[native['tile_map'][r*128+c]]
        assert name=='grastyl',(point,name)
        textures.append(name)
    clearances=fit([prop],read('implementation/architecture.json'),semantic,read('implementation/scenery.json')['records'])
    report={'nativeSha256':digest,'eventId':event['id'],'nativeFaces':len(model['faces']),
            'originalPoint':prop['sourceFeature']['point'],'fittedPoint':FIT['point'],
            'standingPoint':standing,'standingRingTextures':sorted(set(textures)),
            'sternBurial':8,'keelBelowWater':56,'lowestRibBelowWater':57,'clearances':clearances,
            'limits':'Written geometry, source identity and dry contact only. Actual water context and real click require game review; no walkable boat interior claimed.'}
    (PROJECT/'review/native/wreck.json').write_text(json.dumps(report,indent=2)+'\n')
    print({'wreck':prop['id'],'nativeFaces':len(model['faces']),'event':event['id']})


if __name__=='__main__':
    review()
