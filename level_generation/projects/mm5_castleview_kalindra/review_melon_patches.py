"""Check the four native source crop groups, including rigid fruit support and clear approaches."""
import hashlib
import json
import math
import sys
from pathlib import Path

from author_props import ground_at
from prepare_melon_patches import PALETTE
from review_environment import edge_samples
from review_waymarks import fit

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read = lambda f: json.loads((PROJECT/f).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    props = [p for p in semantic['props'] if p.get('kind')=='melon patch']
    expected = {'source_4_3_1','source_4_8_4','source_4_14_3','source_8_1_4'}
    assert len(props)==4 and {p['id'] for p in props}==expected
    clearances = fit(props,read('implementation/architecture.json'),semantic,read('implementation/scenery.json')['records'])
    path = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    native = parse_odm_file(path)['payload']
    height = bytes(native['height_map'])
    ids = read('implementation/feature_event_ids.json')
    records = []
    for prop in props:
        assert prop['originalObject']['sprite']==31
        assert prop['frontOrigin']==prop['sourceFeature']['point'] and prop['placementChange']==0
        event, = [e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
        assert event['id']==prop['eventId']==ids[prop['semanticId']]
        model = native['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        assert {f['texture_name'].lower() for f in model['faces']}==set(PALETTE.values())
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        per_face = []
        for face in model['faces']:
            points = [vertices[i] for i in face['vertex_indices']]
            gaps = []
            for a,b in zip(points,points[1:]+points[:1]):
                length = math.dist(a[:2],b[:2])
                if length==0:
                    gaps.append(min(a[2],b[2])-ground_at(height,a))
                    continue
                for sample in edge_samples(a,b):
                    t = math.dist(a[:2],sample)/length
                    gaps.append(a[2]+t*(b[2]-a[2])-ground_at(height,sample))
            per_face.append(min(gaps))
        assert min(per_face)>=-1e-6,(prop['id'],min(per_face))
        assert len(prop['fruitFaceRanges'])==len(prop['fruit'])==6
        fruit_gaps = [min(per_face[first:last]) for first,last in prop['fruitFaceRanges']]
        assert all(0<=gap<=1 for gap in fruit_gaps),(prop['id'],fruit_gaps)
        x,y = prop['frontOrigin'];x0,y0,x1,y1 = prop['bounds']
        assert all(x+x0<=v[0]<=x+x1 and y+y0<=v[1]<=y+y1 for v in vertices)
        records.append({'id':prop['id'],'eventId':event['id'],'nativeFaces':len(model['faces']),
                        'sourcePoint':prop['frontOrigin'],'fruitCount':6,'leafCount':len(prop['leaves']),
                        'minimumEdgeGroundClearance':min(per_face),'fruitGroundClearances':fruit_gaps})
    (PROJECT/'review/native/melon_patches.json').write_text(json.dumps({
        'nativeSha256':digest,'features':records,'clearances':clearances,
        'limits':'Written source identities, footprints, fruit/foliage support and bindings only. Actual native '
                 'appearance, regional vegetation and representative click remain separate game review.'},indent=2)+'\n')
    print({'melonPatches':len(records),'nativeFaces':sum(r['nativeFaces'] for r in records)})


if __name__=='__main__':
    review()
