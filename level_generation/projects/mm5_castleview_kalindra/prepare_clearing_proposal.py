"""Measure a purposeful native-sprite proposal for the two remaining creature clearings.

This writes review data only. It does not add map entities or claim native visual acceptance.
"""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from author_props import ground_at
from prepare_natural_entrances import world
from prepare_scenery import polygon_distance
from review_fortifications import distance, rectangle

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]

from prepare_clearings import PLACEMENTS



def prepare():
    text = (ROOT/'level_generation/catalogues/outdoor_decorations/data.js').read_text()
    survey = json.loads(text[text.index('{'):].strip().rstrip(';'))
    types = {t['name']: t for t in survey['types']}
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    existing = [r for r in json.loads((PROJECT/'implementation/scenery.json').read_text())['records']
                if 'nativeSite' not in r]
    roads = json.loads((PROJECT/'implementation/roads.json').read_text())
    height = (PROJECT/'landscape/heightmap.raw').read_bytes()
    surface = list(Image.open(PROJECT/'landscape/surface_classes.png').getdata())
    xy = lambda c: [(c[1]-64)*512+256, (64-c[0])*512-256]
    segments = [(xy(a), xy(b)) for path in roads['paths'] for a, b in zip(path['cells'], path['cells'][1:])]
    sites = []
    for name, proposal in PLACEMENTS.items():
        site = next(b for b in spec['buildings'] if b['id'] == name)
        # Natural plantings have a broader canopy envelope than the old compact interaction reservation.
        obstacles = [rectangle(b, c['bounds']) for b in spec['buildings'] if b['id'] != name
                     for c in b['components']]
        records = []
        for index, (asset, x, y, purpose) in enumerate(proposal):
            point = world({**site, 'padHeight': 0}, [x, y, 0])[:2]
            kind = types[asset]
            art = kind['previews']['mm8']
            source = ROOT/art['source']
            col, row = int((point[0]+32768)/512), int((32768-point[1])/512)
            collision = kind['radius']
            support = [ground_at(height, [point[0]+dx, point[1]+dy])
                       for dx, dy in [(-collision, 0), (collision, 0), (0, -collision), (0, collision), (0, 0)]]
            records.append({'id': site['semanticId']+'/native/'+str(index), 'name': asset,
                            'localPoint': [x, y], 'position': point+[round(ground_at(height, point))],
                            'purpose': purpose, 'descriptorNumber': kind['id']+1, 'descriptorId': kind['id'],
                            'collisionRadius': collision, 'collisionHeight': kind['height'],
                            'visualRadius': art['pixel_size'][0]*art['frame_scale']/2,
                            'visualHeight': art['pixel_size'][1]*art['frame_scale'],
                            'source': art, 'assetSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                            'originalUse': kind['maps'], 'sourceSurfaceClass': surface[row*128+col],
                            'groundSupportRange': [min(support), max(support)],
                            'nearestRoad': min(distance(point, a, b) for a, b in segments),
                            'nearestOtherAssembly': min(polygon_distance(point, poly) for poly in obstacles),
                            'nearestExistingSprite': min(math.dist(point, e['position'][:2]) for e in existing),
                            'travelBoundClearance': 24576-max(abs(v) for v in point),
                            'proposedInteraction': asset in ['plant43', 'plant46']})
        sites.append({'id': name, 'sourceIdentities': site['sourceIdentities'], 'people': site['people'],
                      'originalReservation': site['reservedEnvelope'], 'records': records,
                      'futureGrowingGround': [-32, -128, 288, 160] if name == 'nibbler' else None,
                      'clearApproach': [-288, -320, -64, 192] if name == 'nibbler' else [-112, -320, 112, 192],
                      'limits': 'Measured proposal only. Needs explicit native-site ownership, venue binding, '
                                'collision/visual envelope review and actual player-height views. '
                                'Existing 698 baseline decoration identities must remain accounted for.'})
    result = {'status': 'proposal; no native entities added', 'sites': sites,
              'rules': ['Preserve an open center and different front/side/rear canopy placement.',
                        'Retain empty future occupancy and defer every crop, reward and actor.',
                        'Use local groups; do not repeat a ring or apply this density across the entire region.']}
    (PROJECT/'review/clearing_proposal.json').write_text(json.dumps(result, indent=2)+'\n')
    print([{'site': s['id'], 'records': len(s['records']),
            'minimumOtherAssemblyDistance': min(r['nearestOtherAssembly'] for r in s['records']),
            'minimumRoadDistance': min(r['nearestRoad'] for r in s['records']),
            'surfaceClasses': sorted({r['sourceSurfaceClass'] for r in s['records']})} for s in sites])


if __name__ == '__main__':
    prepare()
