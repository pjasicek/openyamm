"""Check written message-bottle grounding, local shore access and status bindings."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image
from author_props import ground_at
from prepare_message_bottles import FITS, PALETTE
from review_environment import edge_samples
from review_waymarks import fit

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read = lambda f: json.loads((PROJECT/f).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    props = [p for p in semantic['props'] if p.get('kind')=='message bottle']
    assert len(props)==4 and {p['id'] for p in props}==set(FITS)
    clearances = fit(props,read('implementation/architecture.json'),semantic,read('implementation/scenery.json')['records'])
    path = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(path)['payload']
    height = bytes(payload['height_map'])
    rows = list(csv.DictReader((PROJECT/'implementation/terrain_rows.tsv').open(),delimiter='\t'))
    names = {90+i:r['texture_name'] for i,r in enumerate(rows)}
    ids = read('implementation/feature_event_ids.json')
    records = []
    for prop in props:
        event, = [e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
        assert event['id']==prop['eventId']==ids[prop['semanticId']]
        assert prop['originalObject']['sprite']==7
        assert prop['frontOrigin']==FITS[prop['id']]['point']
        assert math.dist(prop['frontOrigin'],prop['sourceFeature']['point'])==prop['placementChange']<=768
        model = payload['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        assert {f['texture_name'].lower() for f in model['faces']}==set(PALETTE.values())
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        gaps = []
        for face in model['faces']:
            points = [vertices[i] for i in face['vertex_indices']]
            for a,b in zip(points,points[1:]+points[:1]):
                delta = math.dist(a[:2],b[:2])
                if delta==0:
                    gaps.append(min(a[2],b[2])-ground_at(height,a))
                    continue
                for sample in edge_samples(a,b):
                    t = math.dist(a[:2],sample)/delta
                    gaps.append(a[2]+t*(b[2]-a[2])-ground_at(height,sample))
        assert min(gaps)>=-1e-6 and min(gaps)<=1,(prop['id'],min(gaps))
        assert max(v[2] for v in vertices)-min(v[2] for v in vertices)==44
        standing = FITS[prop['id']]['standing']
        samples = [standing]+[[standing[0]+96*math.cos(i*math.tau/16),
                              standing[1]+96*math.sin(i*math.tau/16)] for i in range(16)]
        textures = []
        for point in samples:
            c,r = math.floor(point[0]/512+64),math.floor(64-point[1]/512)
            name = names[payload['tile_map'][r*128+c]]
            assert name in ['dirttyl','grastyl'] or name.startswith('grdrt'),(prop['id'],name)
            textures.append(name)
        records.append({'id':prop['id'],'eventId':event['id'],'nativeFaces':len(model['faces']),
                        'minimumEdgeGroundClearance':min(gaps),'verticalExtent':44,
                        'originalPoint':prop['sourceFeature']['point'],'fittedPoint':prop['frontOrigin'],
                        'standingPoint':standing,'standingRingTextures':sorted(set(textures))})
    for key,size in [('mm5glass',(64,64)),('mm5paper',(32,64))]:
        with Image.open(PROJECT/'implementation/runtime/worlds/mm5/textures'/(key+'.png')) as image:
            assert image.size==size
    (PROJECT/'review/native/message_bottles.json').write_text(json.dumps({
        'nativeSha256':digest,'features':records,'clearances':clearances,
        'limits':'Written source identity, grounding, dry standing rings and face bindings. Actual water context, '
                 'player-height visibility and representative clicks remain separate game review.'},indent=2)+'\n')
    print({'messageBottles':len(records),'nativeFaces':sum(r['nativeFaces'] for r in records)})


if __name__=='__main__':
    review()
