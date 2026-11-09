"""Fit the source Dark Grove Skyroad contact to a tree-supported climbing rig."""
from author_props import ground_at
from author_skyrope import PALETTE
from native_scenery import native_records
from prepare_natural_entrances import world


def configure(site, height):
    assert site['id'] == 'skyrope' and site['frontOrigin'] == [-2304, 11232]
    site['padHeight'] = round(ground_at(height, site['frontOrigin']))
    site['palette'] = 'skyrope_timber'
    site['environmentKind'] = 'tree-supported climbing rig'
    site['clearApproach'] = [32, -320, 224, 128]
    site['futureGrowingGround'] = None
    site['components'] = [{'id': 'brace', 'bounds': [-48, 192, 176, 336],
                           'roof': 'skyrope_brace', 'eave': 400, 'top': 744}]
    site['details'] = []
    site['nativeScenery'] = native_records(site, height, [
        ('tree12', 0, 288, 'Live trunk and canopy visibly support the lashed climbing rig.')], 'skyroad_anchor')
    site['venues'] = [{'id': site['semanticId']+'/entrance', 'displayLabel': 'Dark Grove Skyroad rope',
                       'facing': 'S', 'localOffset': 128, 'localDepth': 224,
                       'door': world(site, [128, 224, 0])[:2], 'doorSize': [128, 704],
                       'interactionSurface': 'climbing rope and coil', 'occupants': [],
                       'behavior': 'status-only placeholder; Skyroad travel unavailable'}]
    point = world(site, [128, -128, 0])
    point[2] = round(ground_at(height, point))
    site['arrivals'] = [{'id': site['semanticId']+'/ground_return', 'position': point, 'active': False,
                         'purpose': 'Future Skyroad return on clear ground south of the climbing rig.'}]
    # The authored coil lies inside one flat native triangle patch. Reject later terrain changes that invalidate it.
    support = [world(site, [x, y, 0]) for x in [24, 80, 144] for y in [168, 224, 280]]
    assert all(ground_at(height, point) == site['padHeight'] for point in support), support
    site['ropeGeometry'] = {'coilSupportSamples': support, 'treeLocalAnchor': [0, 288, 0],
                            'upperKnotLocalCenter': [120, 288, 672],
                            'sourceDestination': {'map': 91, 'cell': [13, 8]},
                            'sourceReturn': {'map': 3, 'cell': [14, 7]}}
    site['implementationNotes'] = [
        'Original stranded rope, loose ground coil and inclined timber brace lashed to the native tree12 trunk.',
        'Preserve the original Dark Grove location and ordinary ground approach; no house pad or added road.',
        'The visible rope and coil own event 151. Native supporting tree is inert.',
        'Full upper Skyroad geometry, climbing and travel remain deferred; local feedback leaves the party here.']
