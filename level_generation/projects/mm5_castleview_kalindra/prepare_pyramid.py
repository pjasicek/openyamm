"""Retain the closed source pyramid with a bounded wall clearance and explicit MM6 stone provenance."""
import hashlib
import json
from pathlib import Path

from author_props import ground_at

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
PALETTE={'stone':'mm5pyrst','metal':'gn_mtl03'}
STONE=ROOT/'assets_dev/worlds/mm6/textures/egymedb.bmp'


def material():
    return {'path':str(STONE.relative_to(ROOT)),'sha256':hashlib.sha256(STONE.read_bytes()).hexdigest(),
            'sourceBitmap':str(STONE.relative_to(ROOT)),
            'purpose':'Exact MM6 outb3 pyramid masonry; independently authored closed MM5 monument.'}


def prepare(height):
    feature,=[f for f in json.loads((PROJECT/'layout.json').read_text())['features'] if f['id']=='cross_world']
    original,=[o for o in json.loads((PROJECT/'source_objects.json').read_text()) if o['source'] in feature['sources']]
    assert original['sprite']==34
    semantic='mm5:sw/feature/cross_world'
    ids=json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    point=[-8048,-4008]
    assert feature['point']==[-8304,-4008]
    ground=[ground_at(height,[point[0]+x,point[1]+y]) for x in [-256,0,256] for y in [-256,0,256]]
    assert min(ground)>=632 and max(ground)==640
    return [{'id':'cross_world','semanticId':semantic,'title':'Closed cross-world pyramid','kind':'closed pyramid',
             'sourceFeature':feature,'sourceIdentities':feature['sources'],'originalObject':original,
             'frontOrigin':point,'frontOutward':[0,-1],'frontTangent':[1,0],
             'bounds':[-256,-256,256,256],'radius':362,'padHeight':640,'palette':'closed_pyramid',
             'purpose':feature['purpose'],'approachDistance':576,'standingRadius':96,
             'clearApproach':[-112,-672,112,-288],'placementChange':256,
             'eventId':ids[semantic],'behavior':'status-only placeholder; closed monument, no MM4 travel',
             'foundation':{'bottomZ':600,'groundRange':[min(ground),max(ground)]}}]
