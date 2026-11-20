"""Fit the original broken ship to its local bank, preserving the water-contact identity."""
import json
import math
from pathlib import Path

from author_props import ground_at

PROJECT = Path(__file__).resolve().parent
PALETTE = {'wood':'t06a10', 'rib':'t06c11', 'cloth':'gnecclg2'}
FIT = {'point':[-20736,-13696], 'standing':[-20736,-14656], 'contact':[-20736,-14336]}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    feature, = [f for f in layout['features'] if f['id']=='source_4_2_7']
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    original, = [o for o in objects if o['source'] in feature['sources']]
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    assert original['sprite']==5
    assert math.dist(feature['point'],FIT['point'])==640
    assert ground_at(height,FIT['point'])==ground_at(height,FIT['contact'])==256
    semantic = 'mm5:sw/feature/'+feature['id']
    return [{'id':feature['id'], 'semanticId':semantic, 'title':'Broken river ship', 'kind':'source wreck',
             'sourceFeature':feature, 'sourceIdentities':feature['sources'], 'originalObject':original,
             'frontOrigin':FIT['point'], 'frontOutward':[0,-1], 'frontTangent':[1,0],
             'bounds':[-224,-640,224,640], 'radius':678, 'padHeight':256, 'palette':'source_wreck',
             'purpose':feature['purpose'], 'approachDistance':960, 'standingRadius':96,
             'clearApproach':[-112,-1056,112,-672], 'standingPoint':FIT['standing'],
             'interactionContact':FIT['contact'], 'placementChange':640,
             'eventId':ids[semantic], 'behavior':'status-only placeholder; search, loot and sinking deferred',
             'support':{'waterZ':256, 'intent':'Keel is submerged; stern meets dry bank. No artificial platform.'}}]
