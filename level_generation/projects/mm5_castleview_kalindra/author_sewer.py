"""Original low masonry culvert, grating and bank landing in native units."""
import math

from author_props import ground_at
from prepare_natural_entrances import world


def support_box(author, panels, bounds, material, site, model):
    first = len(panels)
    author.box(panels, bounds, material)
    site.setdefault('sewerChecks', []).append({'model': model, 'faces': [first+4], 'kind': 'buried support'})


def vault(author, panels, component, palette, site):
    g = site['sewerGeometry']; depth = g['vaultDepth']; spring = g['springHeight']
    name = site['id']+'_'+component['id']
    for x0, x1 in [(-224, -128), (128, 224)]:
        support_box(author, panels, [x0, 0, -96, x1, depth, spring], palette['wall'], site, name)
    for x0, x1 in [(-352, -224), (224, 352)]:
        support_box(author, panels, [x0, 32, -96, x1, depth-32, 128], palette['stone'], site, name)
    def arc(radius, y):
        return [(radius*math.cos(i*math.pi/8), y, spring+radius*math.sin(i*math.pi/8)) for i in range(9)]
    outer0, outer1 = arc(g['outerRadius'], 0), arc(g['outerRadius'], depth)
    inner0, inner1 = arc(g['innerRadius'], 0), arc(g['innerRadius'], depth)
    for i in range(8):
        j = i+1
        author.panel(panels, [outer0[i], outer0[j], inner0[j], inner0[i]], palette['arch'])
        author.panel(panels, [outer1[j], outer1[i], inner1[i], inner1[j]], palette['arch'])
        author.panel(panels, [outer0[j], outer0[i], outer1[i], outer1[j]], palette['arch'])
        author.panel(panels, [inner0[i], inner0[j], inner1[j], inner1[i]], palette['stone'])
    # Solid rear closure behind the recessed dark face, with no hidden walkable room or original-map transfer.
    end = [(128, depth, -96)] + inner1 + [(-128, depth, -96)]
    for i in range(1, len(end)-1):
        points = [end[0], end[i+1], end[i]]
        author.panel(panels, points, palette['wall'], [(x/128, z/256) for x, y, z in points])


def landing(author, panels, component, palette, site, height):
    name = site['id']+'_'+component['id']
    for section in site['sewerGeometry']['walkingSections']:
        first = len(panels)
        for triangle in section['triangles']:
            author.panel(panels, triangle, palette['floor'], [(p[0]/128, p[1]/128) for p in triangle])
        site.setdefault('sewerChecks', []).append(
            {'model': name, 'faces': [first, first+1], 'kind': 'supported walking floor', 'section': section['id']})
        corners = section['corners']
        bottom = [[x, y, ground_at(height, world(site, [x, y, z]))-site['padHeight']-32] for x, y, z in corners]
        for i in range(4):
            j = (i+1)%4
            author.panel(panels, [bottom[i], bottom[j], corners[j]], palette['stone'])
            author.panel(panels, [bottom[i], corners[j], corners[i]], palette['stone'])
        first = len(panels)
        for indices in [(2, 1, 0), (3, 2, 0)]:
            author.panel(panels, [bottom[i] for i in indices], palette['stone'])
        site['sewerChecks'].append({'model': name, 'faces': [first, first+1], 'kind': 'buried landing base'})


def interaction(author, panels, site, palette, venue):
    y = 320; spring = site['sewerGeometry']['springHeight']; radius = 128
    points = [(-128, y, 0), (128, y, 0)]
    points += [(radius*math.cos(i*math.pi/8), y, spring+radius*math.sin(i*math.pi/8)) for i in range(9)]
    for i in range(1, len(points)-1):
        author.panel(panels, [points[0], points[i], points[i+1]], palette['dark'])
    # The physical grating stops the party before the unimplemented passage; bars and recess share one handler.
    y = venue['localDepth']
    for x in [-96, -48, 0, 48, 96]:
        top = spring+math.sqrt(radius*radius-x*x)
        author.box(panels, [x-4, y-4, 0, x+4, y+4, top], palette['metal'])
    for z in [64, 160]:
        author.box(panels, [-128, y-8, z-4, 128, y, z+4], palette['metal'])
