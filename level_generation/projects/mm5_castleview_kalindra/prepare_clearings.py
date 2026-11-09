"""Author native scenery and retained contact ownership for the two creature clearings."""
from author_props import ground_at
from native_scenery import native_records

PLACEMENTS = {
    'falista': [
        ('tree11', -560, 704, 'Tall western canopy frames the clear resting ground.'),
        ('tree13', 448, 608, 'Shorter eastern crown keeps the grove uneven.'),
        ('tree12', 0, 1184, 'Open-branched rear tree provides shelter behind the resting area.'),
        ('plant43', 160, 320, 'Flowered stump is the reachable sanctuary placeholder.'),
        ('plant17', -160, 384, 'Small flower pocket beside the resting space.'),
        ('plant17', 96, 608, 'Second flower clump near the rear canopy edge.'),
        ('rock05', -320, 192, 'Single low resting-ground edge rock.'),
        ('plant26', -384, 640, 'White flowering understory at the western tree.')],
    'nibbler': [
        ('tree12', -520, 576, 'Branched western shelter tree.'),
        ('tree13', 520, 640, 'Low eastern crown leaves an uneven open edge.'),
        ('tree11', 80, 1040, 'Taller rear canopy shelters the clearing.'),
        ('plant46', -160, 320, 'Ivy stump is the reachable clearing placeholder.'),
        ('plant27', 144, 608, 'Small understory pocket away from the reserved growing ground.'),
        ('rock01', 400, 320, 'Eastern natural edge beside the short tree.'),
        ('rock05', -352, 0, 'Low entrance-side rock identifies the clearing without blocking it.'),
        ('plant17', -224, 256, 'Sparse ground detail beside the ivy stump.')]
}


def configure(site, height):
    site['padHeight'] = round(ground_at(height, site['frontOrigin']))
    for component in site['components']:
        component['roof'] = 'natural_clearing'
    site['environmentKind'] = 'native scenery clearing'
    site['clearApproach'] = [-288, -320, -64, 192] if site['id'] == 'nibbler' else [-112, -320, 112, 192]
    site['futureGrowingGround'] = [-32, -128, 288, 160] if site['id'] == 'nibbler' else None
    site['nativeScenery'] = native_records(site, height, PLACEMENTS[site['id']], site['id']+'_clearing')
    stump, = [r for r in site['nativeScenery'] if r['name'] in ['plant43', 'plant46']]
    label = "Falista's sanctuary" if site['id'] == 'falista' else "Nibbler's clearing"
    x, y = stump['localPoint']
    site['venues'] = [{'id': site['semanticId']+'/entrance', 'displayLabel': label,
                       'facing': site['facing'], 'localOffset': x, 'localDepth': y,
                       'door': stump['position'][:2], 'interactionPosition': stump['position'],
                       'nativeDecorationId': stump['id'], 'interactionSurface': 'native landmark sprite',
                       'occupants': [person['id'] for person in site['people']],
                       'behavior': 'named status-only placeholder; occupancy and rewards deferred'}]
    site['implementationNotes'] = [
        'Three unevenly placed native trees frame an open resting/shelter site; individual native-triangle grounding.',
        'Flowered or ivy-covered stump provides the explicit local contact; no house geometry or runtime occupant.',
        'Native scene entities own this setting. Preserve the original 698 baseline decoration identities separately.',
        'The approach stays clear; Nibbler growing-ground reservation remains empty until its future quest state.']
