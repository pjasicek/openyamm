"""Goldur's modest woodcraft setting, kept south of the clear lodge approach."""
import math

from author_props import ground_at
from native_scenery import native_records


def prepare(height):
    origin = [-7190, -2590]
    prop = {
        'id': 'ranger_woodcraft', 'semanticId': 'mm5:castleview/ranger/woodcraft', 'owner': 'ranger',
        'title': 'Goldur woodcraft setting', 'kind': 'woodcraft setting',
        'frontOrigin': origin, 'frontTangent': [1, 0], 'frontOutward': [0, -1],
        'padHeight': math.ceil(ground_at(height, origin)/32)*32,
        'bounds': [-256, -180, 208, 136], 'radius': 282, 'palette': 'working_props',
        'purpose': 'An outdoor work surface, chopping block, embedded axe and short timber stock; '
                   'the east-facing lodge approach stays open and unpaved.',
        'behavior': 'inert architectural scenery; no actor, pickup, reward or event',
        'clearLodgeApproach': [-7420, -2180, -6200, -1850],
        'clearApproach': [-230, 410, 990, 740], 'futureGrowingGround': None,
        'allowedSurfaceClasses': [1, 2],
    }
    # A loose practice-garden pocket north of the door; keep the southern work surface separate.
    plants = [
        ('plant32', -90, 1080, 'Rear shrub anchors the small lodge garden.'),
        ('plant26', 90, 1200, 'Low white-flower pocket beside the shrub.'),
        ('plant26', 230, 1000, 'Separate low pocket near the open frontage.'),
        ('plant32', -160, 1320, 'Unequal northern shrub continues the garden edge.'),
        ('plant26', 180, 1350, 'Small northern flower accent; no continuous border.')]
    prop['nativeScenery'] = native_records(prop, height, plants, 'ranger_practice_garden')
    return prop


def author_yard(author, prop, palette, height):
    origin, pad = prop['frontOrigin'], prop['padHeight']
    panels, supports = [], []

    def ground(x, y):
        return ground_at(height, [origin[0]+x, origin[1]+y])-pad

    def box(bounds, material='wood', fitted=False):
        x0, y0, z0, x1, y1, z1 = bounds
        if fitted:
            samples = [ground(x,y) for x in [x0,x1] for y in [y0,y1]]
            z0 = min(samples)-16
            supports.append({'bounds': [x0,y0,x1,y1], 'bottom': pad+z0, 'top': pad+z1,
                             'footprint': [[origin[0]+x,origin[1]+y]
                                           for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]})
        author.box(panels, [x0,y0,z0,x1,y1,z1], palette[material])

    # A narrow plank work surface on two grounded trestles, alongside the chopping block.
    for y in [40,72,104]:
        box([-256,y,104,0,y+30,120])
    for x in [-226,-54]:
        box([x,48,0,x+28,124,104], fitted=True)
    box([-240,69,44,-16,83,64])
    # Three short squared timbers with different lengths; individually fitted at the ground.
    for bounds in [[-200,-180,0,50,-146,24],[-160,-137,0,110,-107,30],[-126,-98,0,72,-70,22]]:
        box(bounds, fitted=True)

    # Slightly tapered eight-sided chopping block. Cap grain is the retained native wood texture.
    cx, cy, radius, top = 144, 24, 56, 72
    bottom = min(ground(cx+radius*math.cos(i*math.tau/8),cy+radius*math.sin(i*math.tau/8))
                 for i in range(8))-16
    lower = [(cx+radius*math.cos(i*math.tau/8), cy+radius*math.sin(i*math.tau/8), bottom)
             for i in range(8)]
    upper = [(cx+(radius-4)*math.cos(i*math.tau/8), cy+(radius-4)*math.sin(i*math.tau/8), top)
             for i in range(8)]
    for i in range(8):
        author.panel(panels, [lower[i],lower[(i+1)%8],upper[(i+1)%8],upper[i]], palette['wood'])
    author.panel(panels, upper, palette['wood'])
    supports.append({'bounds':[cx-radius,cy-radius,cx+radius,cy+radius],
                     'bottom':pad+bottom,'top':pad+top,
                     'footprint': [[origin[0]+x,origin[1]+y] for x,y,_ in lower]})
    # A small embedded axe, authored as scenery rather than an inventory object.
    axe_start = len(panels)
    box([cx-4,cy-4,68,cx+4,cy+4,156])
    outline = [(5,68),(5,88),(-16,94),(-44,110),(-52,64),(-24,68)]
    front = [(cx+x,cy-6,z) for x,z in outline]
    back = [(x,cy+6,z) for x,_,z in front]
    # Split the mildly concave side profile explicitly into planar convex faces.
    for indices in [(0,1,2,5),(2,3,4,5)]:
        author.panel(panels,[front[i] for i in indices],palette['metal'])
        author.panel(panels,[back[i] for i in reversed(indices)],palette['metal'])
    for i in range(len(front)):
        j = (i+1)%len(front)
        author.panel(panels,[front[i],back[i],back[j],front[j]],palette['metal'])
    # A slight lean distinguishes the embedded axe from a vertical pole or hammer.
    angle = math.radians(-18)
    for i in range(axe_start,len(panels)):
        points,key,uv = panels[i]
        rotated = [(cx-42+(x-(cx-42))*math.cos(angle)+(z-72)*math.sin(angle),y,
                    72-(x-(cx-42))*math.sin(angle)+(z-72)*math.cos(angle)) for x,y,z in points]
        panels[i] = (rotated,key,uv)
    # Two flat worked pieces on the table suggest use without inventing a service interaction.
    box([-214,58,120,-134,82,128])
    box([-101,82,120,-43,110,132])
    prop['groundSupports'] = supports
    author.model(prop['id'], panels, prop)
    author.semantic['props'].append(prop)
