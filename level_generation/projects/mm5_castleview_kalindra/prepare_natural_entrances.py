"""Fit original mine and shallow troll descents without modifying the native heightfield."""
import math

from author_props import ground_at
from prepare_bridges import triangle_clearance

IDS = {'mine', 'troll_a', 'troll_b', 'troll_c'}
PALETTE = {'rock': 't68a02a', 'dark': 'solid01', 'wood': 't06a10',
           'crosswood': 't06c11', 'metal': 'gn_mtl03', 'crate': 'crate_w64'}


def world(site, point):
    x, y, z = point
    return [site['frontOrigin'][i] + site['frontTangent'][i]*x - site['frontOutward'][i]*y
            for i in range(2)] + [site['padHeight']+z]


def configure(site, height):
    mine = site['id'] == 'mine'
    # A local origin is not a terrain pad: every exposed skirt and the approach are fitted independently.
    site['padHeight'] = math.ceil(ground_at(height, site['frontOrigin']))
    base = max(ground_at(height, world(site, [x, y, 0]))-site['padHeight']
               for x in range(-192, 193, 32) for y in range(192, 513, 32))
    lower = math.ceil(base)+8
    upper = lower+(0 if mine else 48)
    front = 192 if mine else 256
    rear = 480
    variations = {
        'mine': [(-384, 64), (-352, 288), (-224, 448), (32, 496), (256, 400), (384, 176)],
        'troll_a': [(-384, 72), (-336, 272), (-192, 384), (64, 416), (288, 320), (384, 96)],
        'troll_b': [(-384, 112), (-304, 320), (-128, 432), (128, 384), (320, 288), (384, 64)],
        'troll_c': [(-384, 64), (-352, 256), (-256, 400), (-32, 448), (256, 352), (384, 128)],
    }
    site['palette'] = 'natural_entrances'
    site['components'] = [{'id': 'rock_recess', 'bounds': [-384, 0, 384, 576],
                           'roof': 'natural_recess', 'eave': upper+288, 'top': upper+496}]
    site['entranceGeometry'] = {'frontDepth': front, 'rearDepth': rear,
                               'frontFloor': upper, 'rearFloor': lower,
                               'outerProfile': variations[site['id']], 'openingHalfWidth': 160,
                               'openingHeight': 288, 'minimumHeadroom': 256}
    venue = {'id': site['semanticId']+'/entrance', 'displayLabel': site['title'],
             'facing': site['facing'], 'localOffset': 0, 'localDepth': rear,
             'heightAbovePad': lower, 'doorSize': [320, 288],
             'occupants': [p['id'] for p in site['people']],
             'interactionSurface': 'recessed rock descent', 'behavior': 'named status-only placeholder'}
    venue['door'] = world(site, [0, rear, lower])[:2]
    site['venues'] = [venue]
    site['arrivals'] = [{'id': site['semanticId']+'/ground_return',
                         'position': world(site, [0, 64, 0]), 'active': False,
                         'purpose': 'Future source BLV return on the supported approach; no map transfer yet.'}]
    # Triangulated approach starts only six units above the unmodified terrain. Interior slopes down at troll sites.
    rows = []
    for y in [0, front, rear]:
        row = []
        for x in [-160, 160]:
            z = ground_at(height, world(site, [x, y, 0]))-site['padHeight']+6 if y == 0 else \
                upper if y == front else lower
            row.append([x, y, z])
        rows.append(row)
    triangles = []
    for a, b in zip(rows, rows[1:]):
        for tri in [[a[0], a[1], b[1]], [a[0], b[1], b[0]]]:
            check = triangle_clearance(height, [world(site, p) for p in tri])
            assert check['minimum'] >= 2, (site['id'], check['minimum'])
            triangles.append(tri)
    site['entranceGeometry']['walkingTriangles'] = triangles
    # The retained arrival stands on the modeled ramp, not an assumed flat pad.
    start = sum(p[2] for p in rows[0])/2
    arrival_z = start+(upper-start)*64/front
    site['arrivals'][0]['position'][2] = site['padHeight']+arrival_z
    site['implementationNotes'] = [
        'Original faceted rock recess, using inspected native cave material roles; no donor vertices.',
        'The safe shallow descent remains above unchanged native terrain, with a supported entrance apron.',
        'The dark recessed end is a clickable placeholder. Deeper BLV, falling and travel behavior are deferred.',
        'Preserve the existing reservation and off-road approach. No automatic lane or flattened house pad.']
