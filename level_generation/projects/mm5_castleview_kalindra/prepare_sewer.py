"""Fit the existing riverside outfall to a dry landing connected to the southern bank."""
from author_props import ground_at
from prepare_bridges import triangle_clearance
from prepare_natural_entrances import world

PALETTE = {'wall': 't18a01a', 'arch': 't18a02a', 'stone': 't18b01',
           'floor': 't32a05b', 'metal': 'gn_mtl03', 'dark': 'solid01'}


def configure(site, height):
    assert site['id'] == 'sewer_out'
    assert site['frontOrigin'] == [-768, -10528]
    site['padHeight'] = 288
    site['palette'] = 'sewer_masonry'
    site['components'] = [
        {'id': 'culvert', 'bounds': [-352, 0, 352, 384], 'roof': 'sewer_vault', 'eave': 160, 'top': 384},
        {'id': 'bank_landing', 'bounds': [-160, -736, 160, 384], 'roof': 'sewer_landing', 'eave': 0, 'top': 70}]
    venue = site['venues'][0]
    venue.update({'door': world(site, [0, 48, 0])[:2], 'localDepth': 48,
                  'doorSize': [256, 288], 'interactionSurface': 'barred sewer recess'})
    site['arrivals'] = [{'id': site['semanticId']+'/ground_return', 'position': world(site, [0, -64, 0]),
                         'active': False, 'purpose': 'Future sewer return on the dry landing outside the grating.'}]
    # Ground-connected ramp, a broader level landing, and the dry interior floor share edges.
    sections = []
    for name, width, first, last in [('bank_ramp', 256, -736, -128),
                                     ('landing', 320, -128, 0), ('threshold', 256, 0, 376)]:
        points = []
        for x, y in [(-width/2, first), (width/2, first), (width/2, last), (-width/2, last)]:
            z = ground_at(height, world(site, [x, y, 0]))-site['padHeight']+6 if y == -736 else 0
            points.append([x, y, z])
        triangles = [[points[i] for i in indices] for indices in [(0, 1, 2), (0, 2, 3)]]
        checks = [triangle_clearance(height, [world(site, p) for p in triangle]) for triangle in triangles]
        assert min(c['minimum'] for c in checks) >= 2, (name, checks)
        sections.append({'id': name, 'corners': points, 'triangles': triangles,
                         'minimumClearance': min(c['minimum'] for c in checks)})
    site['sewerGeometry'] = {'waterLevel': 256, 'walkingSections': sections,
                             'vaultDepth': 384, 'springHeight': 160, 'innerRadius': 128, 'outerRadius': 224}
    site['implementationNotes'] = [
        'Retain the original source outfall location and south-facing bank approach.',
        'New low Garrote masonry vault with recessed grating; no reused donor building mesh.',
        'The supported bank ramp ends on a dry Z288 landing, 32 above the river level.',
        'The grating and recessed end share the sewer placeholder; no BLV travel, actors or rewards.']
