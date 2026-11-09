"""Audit baseline identity coverage and terrain support against the current native checkpoint.

These structural checks complement, and do not replace, actual scene and movement review.
"""
import collections
import hashlib
import json
import math
import re
import sys
from pathlib import Path

from author_props import ground_at
from review_fortifications import rectangle

PROJECT=Path(__file__).resolve().parent


def edge_samples(a,b):
    """Exact breakpoints of a line over the native piecewise-linear terrain triangles."""
    ts={0.,1.}
    for start,end in [(a[0],b[0]),(a[1],b[1]),(a[0]-a[1],b[0]-b[1])]:
        if abs(end-start)<1e-9:continue
        for grid in range(math.ceil(min(start,end)/512),math.floor(max(start,end)/512)+1):
            t=(grid*512-start)/(end-start)
            if 0<t<1:ts.add(t)
    return [[a[i]+t*(b[i]-a[i]) for i in range(2)] for t in sorted(ts)]


def review():
    read=lambda name:json.loads((PROJECT/name).read_text())
    build=read('review/native/build.json')
    semantic=read('implementation/source/mm5_sw.semantic.json')
    scenery=read('implementation/scenery.json')
    spec=read('implementation/architecture.json')
    planned=read('landscape/decorations.json')['records']+read('landscape/buffer_scenery.json')['records']
    native=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    assert hashlib.sha256(native.read_bytes()).hexdigest()==build['nativeSha256']
    assert len(semantic['bmodels'])==build['bmodels']
    assert len(semantic['props'])==build['props']
    for name,digest in build['sourceObjSha256'].items():
        assert hashlib.sha256((PROJECT/'implementation/source/models'/name).read_bytes()).hexdigest()==digest,name
    assert build['terrainArraysExact']
    counts=collections.Counter(r['id'] for r in scenery['records'])
    counts.update(r['semanticId'] for r in semantic['props'])
    counts.update(r['semanticId'] for r in semantic['landscape'])
    expected={r['id'] for r in planned}
    assert len(expected)==len(planned),'Duplicate source decoration identities'
    missing=sorted(expected-counts.keys())
    duplicates={key:count for key,count in counts.items() if count!=1}
    additional=sorted(counts.keys()-expected)
    modeled_additions=sorted(p['semanticId'] for p in spec['props'] if p['semanticId'] not in expected)
    rim_additions=['mm5:sw/rim/rim_'+str(start//32) for start in range(0,len(spec['worldRim']['edges']),32)]
    native_additions=sorted(r['id'] for site in spec['buildings']+spec['props']+spec['sceneryGroups']
                            for r in site.get('nativeScenery',[]))
    court_additions=sorted(p['semanticId'] for p in read('implementation/chapter_court.json')['props'])
    assert court_additions==['mm5:castleview/chapter_court_bench','mm5:castleview/chapter_court_edging']
    assert additional==sorted(modeled_additions+native_additions+rim_additions+court_additions)
    assert not missing and not duplicates,(missing,duplicates)
    paths=['implementation/source/mm5_sw.semantic.json','implementation/scenery.json','implementation/architecture.json',
           'landscape/decorations.json','landscape/buffer_scenery.json','implementation/chapter_court.json']
    report={'nativeSha256':build['nativeSha256'],'planned':len(planned),
            'represented':sum(counts[key] for key in expected),'spriteInstances':len(scenery['records']),
            'modeledBaselineProps':sum(r['semanticId'] in expected for r in semantic['props']),
            'additionalModeledProps':modeled_additions,'additionalNativeScenery':native_additions,
            'additionalRimGroups':rim_additions,
            'additionalCourtProps':court_additions,
            'missing':missing,'duplicates':duplicates,
            'sourceSha256':{p:hashlib.sha256((PROJECT/p).read_bytes()).hexdigest() for p in paths},
            'limits':'Baseline identities exactly once; separately lists planned site-specific additions. '
                     'Does not certify visual composition or completion of all GOAL.md props/chests.'}
    (PROJECT/'review/native/decoration_coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    sys.path.insert(0,str(PROJECT.parents[2]/'util'))
    from map_export import parse_odm_file
    payload=parse_odm_file(native)['payload']
    height=bytes(payload['height_map'])
    assert height==(PROJECT/'landscape/heightmap.raw').read_bytes()
    foundations=[]
    unchecked=[]
    for building in semantic['buildings']:
        for component in building['components']:
            if component['roof'] in ['lean_to','entry_hood']:continue
            if component.get('baseHeight',0) or component['roof'] not in [
                    'hip','gable','parapet','arcane_tower','apse','watch_tower','royal_tower']:
                unchecked.append(building['id']+'/'+component['id'])
                continue
            poly=rectangle(building,component['bounds'])
            if 'polygon' in component:
                poly=[[building['frontOrigin'][i]+building['frontTangent'][i]*x-building['frontOutward'][i]*y
                       for i in range(2)] for x,y in component['polygon']]
            support=[ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
            bottom=building['padHeight']-64
            foundations.append({'id':building['id']+'/'+component['id'],
                                'groundRange':[min(support),max(support)],'foundationBottom':bottom,
                                'minimumBurial':min(support)-bottom})
    doors=[{'id':v['id'],'thresholdZ':b['padHeight']+v.get('heightAbovePad',0),
            'riseFrom128Outside':b['padHeight']-ground_at(height,
                [v['door'][i]+b['frontOutward'][i]*128 for i in range(2)])}
           for b in semantic['buildings'] for v in b['venues']
           if not v.get('heightAbovePad',0) and 'nativeDecorationId' not in v]
    assert all(f['minimumBurial']>=0 for f in foundations),foundations
    support={'nativeSha256':build['nativeSha256'],'foundations':foundations,'doors':doors,
             'uncheckedComponents':unchecked,
             'method':'All footprint edges split at native grid and triangle-diagonal crossings; '
                      'extrema checked against the actual serialized heightfield.',
             'limits':'Main shell skirts only. Open shelters, props, roofs, bridges, full approach corridors '
                      'and actual movement require separate checks.'}
    (PROJECT/'review/native/foundation_support.json').write_text(json.dumps(support,indent=2)+'\n')
    # Keep the implemented interaction graph reviewable alongside pending original venues.
    events=semantic['events']+scenery['events']
    lua=(PROJECT/'implementation/runtime/worlds/mm5/events/maps/mm5_sw.lua').read_text()
    registered=[int(value) for value in re.findall(r'RegisterEvent\((\d+),',lua)]
    assert sorted(registered)==sorted(e['id'] for e in events)
    bindings=[]
    for event in events:
        binding=dict(event)
        if 'bmodel_index' in event:
            model=payload['bmodels'][event['bmodel_index']]
            assert all(model['faces'][face]['cog_triggered_number']==event['id'] for face in event['faces'])
            binding['targetKind']='bmodel faces'
        else:
            binding['targetKind']='decoration secondary event'
            binding['entityIndices']=[i for i,e in enumerate(payload['entities']) if e['event_id_secondary']==event['id']]
            assert binding['entityIndices'],event
        bindings.append(binding)
    by_semantic={e['semantic_id']:e for e in bindings}
    premises=[]
    native_indices={r['id']:i+1 for i,r in enumerate(scenery['records'])}
    for building in spec['buildings']:
        models=[m['index'] for m in semantic['bmodels'] if m['assembly']==building['id']]
        decorations=[native_indices[r['id']] for r in building.get('nativeScenery',[]) if r['id'] in native_indices]
        venues=[{'semanticId':v['id'],'label':v['displayLabel'],'occupants':v['occupants'],
                 'interactionSurface':v.get('interactionSurface','entrance door'),
                 'additionalInteractionSurfaces':v.get('additionalInteractionSurfaces',[]),
                 'binding':by_semantic.get(v['id'])} for v in building['venues']]
        premises.append({'id':building['id'],'semanticId':building['semanticId'],'title':building['title'],
                         'form':building['form'],'purpose':building['purpose'],'nativeBmodels':models,
                         'geometryAuthored':bool(models),'nativeDecorationIndices':decorations,
                         'environmentAuthored':bool(models or decorations),'venues':venues,
                         'plannedProps':building['plannedProps'],
                         'interiorContacts':building.get('interiorContacts',[]),
                         'acceptance':'Native source/binding presence only; contextual visual completion remains pending.'})
    inventory={'nativeSha256':build['nativeSha256'],'premises':premises,'bindings':bindings,
               'nativeBoundHandlerCount':len(bindings),'luaHandlerCount':len(registered),
               'population':{'actors':build['actors'],'spawns':build['spawns']},
               'limits':'Residents are future semantic assignments, not runtime NPCs. This proves current native '
                        'bindings and registered handlers, not every click, natural-site interpretation or final visuals.'}
    (PROJECT/'review/native/interaction_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print({'baselineCovered':report['represented'],'additionalProps':additional,
           'supportedShells':len(foundations),'uncheckedComponents':unchecked})


if __name__=='__main__':
    review()
