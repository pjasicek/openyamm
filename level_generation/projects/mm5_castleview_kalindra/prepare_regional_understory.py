"""Three authored southern-woodland floor pockets; preserve the existing canopy and open lanes."""
import json
from pathlib import Path

from native_scenery import native_records
from author_props import ground_at

PROJECT = Path(__file__).resolve().parent

POCKETS = [
    ('wood_west_floor', [11900,-13900], [
        ('plant44',-220,0,'Broken mossy stump marks one edge of a small woodland-floor pocket.'),
        ('plant32',-100,140,'Low shrub beside the deadwood, away from the walking gap.'),
        ('rock05',-360,180,'Low rock at the slope-side edge.'),
        ('rock02',120,220,'Unequal companion rock, leaving the centre open.'),
        ('plant32',300,-80,'Separate low shrub on the downslope shoulder.'),
        ('rock01',460,0,'Small exposed stone beside the shrub.'),
        ('rock05',-80,360,'A detached stone continues the shoulder without forming a border.'),
        ('plant32',540,200,'A short final shrub accent; no enclosing ring.')]),
    ('wood_south_floor', [15600,-18400], [
        ('plant47',-240,0,'Older grey deadwood in a second, separate woodland pocket.'),
        ('rock02',-400,-160,'A weathered stone on the outer side of the deadwood.'),
        ('plant32',-100,-180,'Low cover on one side, retaining an open northern gap.'),
        ('plant44',220,260,'Second irregular stump suggests scattered old damage, not a logged row.'),
        ('rock05',380,160,'Low stone beside the second stump.'),
        ('plant32',180,480,'Small isolated shrub at the rear of the pocket.'),
        ('rock01',-20,420,'A detached stone between the uneven subgroups.')]),
    ('wood_east_floor', [21700,-11300], [
        ('rock02',-260,160,'Exposed stone on the northeastern woodland shoulder.'),
        ('rock05',-60,260,'Unequal smaller rock beside the exposed stone.'),
        ('plant32',-140,-80,'Low cover on the sheltered side.'),
        ('plant47',160,40,'One broken stump connects this shoulder to the woodland.'),
        ('plant32',340,-160,'A separate shrub leaves the central walk-through space open.'),
        ('rock01',460,80,'Small stone beside the eastern shrub.'),
        ('plant32',240,360,'Loose rear cover; preserve the gap toward the buffer.'),
        ('rock05',-340,-220,'Detached foreground stone, not a continuous perimeter.')]),
]


def prepare(height):
    groups = []
    for name,point,placements in POCKETS:
        group = {'id':name,'semanticId':'mm5:sw/landscape/'+name,'frontOrigin':point,
                 'padHeight':ground_at(height, point),
                 'frontTangent':[1,0],'frontOutward':[0,-1],
                 'allowedSurfaceClasses':[1,2],'futureGrowingGround':None,
                 'clearApproach':None,
                 'openSpaceIntent':'Retain existing canopy and gaps; this is ground scenery, not a venue approach.',
                 'purpose':'Selected native ground detail within the existing southern woodland; no new trees or rewards.'}
        group['nativeScenery'] = native_records(group,height,placements,'southern_woodland_floor')
        groups.append(group)
    return groups


if __name__ == '__main__':
    output = PROJECT/'review/region_composition_v1/planned_understory.json'
    output.write_text(json.dumps({'status':'Draft placement study; not integrated or native-reviewed.',
        'groups':prepare((PROJECT/'landscape/heightmap.raw').read_bytes())},indent=2)+'\n')
    print('Wrote isolated woodland-floor proposal:',output)
