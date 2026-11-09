"""Source-owned Xeen cliff contour, spill surfaces and impassable-space geometry."""
import hashlib
import math

from author_props import ground_at
from review_environment import edge_samples


def plan_rim(project):
    import numpy as np
    from PIL import Image

    classes = np.array(Image.open(project/'landscape/surface_classes.png'))[:127, :127]
    height = (project/'landscape/heightmap.raw').read_bytes()
    edges, normals = [], {}
    directions = [(-1, 0, (0, 0), (0, 1)), (0, 1, (0, 1), (1, 1)),
                  (1, 0, (1, 1), (1, 0)), (0, -1, (1, 0), (0, 0))]
    for r in range(127):
        for c in range(127):
            if classes[r, c] == 0:
                continue
            for dr, dc, a, b in directions:
                rr, cc = r+dr, c+dc
                if not (0 <= rr < 127 and 0 <= cc < 127) or classes[rr, cc] != 0:
                    continue
                points = [(r+a[0], c+a[1]), (r+b[0], c+b[1])]
                edges.append({'landCell': [r, c], 'voidCell': [rr, cc], 'nodes': points,
                              'landClass': int(classes[r, c]), 'outward': [dc, -dr]})
                for node in points:
                    normal = normals.setdefault(node, [0, 0])
                    normal[0] += dc
                    normal[1] -= dr
    nodes = []
    fluid_nodes = {tuple(node) for e in edges if e['landClass'] in [3, 4] for node in e['nodes']}
    for (r, c), normal in sorted(normals.items()):
        length = math.hypot(*normal)
        assert length > 0, ('Ambiguous contour vertex', r, c)
        x, y, z = (c-64)*512, (64-r)*512, height[r*128+c]*32
        outward = [v/length for v in normal]
        variation = math.sin(x/971+y/1249)*24 + math.sin(x/397-y/641)*12
        crest = 0 if (r, c) in fluid_nodes else round(48+variation)
        inner = [round(x-outward[0]*(176+variation)), round(y-outward[1]*(176+variation))]
        inner.append(round(ground_at(height, inner))-16)
        # A small exposed ledge beyond the impassable source edge stays in view when the party reaches it.
        # Water nodes retain their exact surface endpoint for a separately authored spill treatment.
        ledge = 0 if (r, c) in fluid_nodes else 464+variation*2
        rings = [[round(x+outward[0]*ledge), round(y+outward[1]*ledge), z+crest]]
        for depth, projection in [(128, ledge+80+variation), (768, ledge+128+variation*3),
                                  (2816, 32-variation*5), (8192, -48+variation*3)]:
            rings.append([round(x+outward[0]*projection), round(y+outward[1]*projection), z-depth])
        nodes.append({'grid': [r, c], 'boundary': [x, y, z], 'outward': outward, 'rings': rings,
                      'inner': inner, 'crestHeight': crest})
    by_grid = {tuple(n['grid']): n for n in nodes}
    for edge in edges:
        a, b = [by_grid[tuple(n)] for n in edge['nodes']]
        samples = edge_samples(a['inner'], b['inner']) if edge['landClass'] not in [3, 4] else []
        length = math.dist(a['inner'][:2], b['inner'][:2])
        edge['capSamples'] = [{'t': math.dist(a['inner'][:2], point)/length,
                               'point': point+[ground_at(height, point)-16]} for point in samples]
    report = {'status': 'Source-derived rim specification; native contextual acceptance recorded separately',
              'sourceSha256': {name: hashlib.sha256((project/name).read_bytes()).hexdigest()
                               for name in ['landscape/surface_classes.png', 'landscape/heightmap.raw']},
              'edges': edges, 'nodes': nodes, 'boundaryBottom': -64, 'boundaryTop': 32700,
              'fluidEdgeCount': sum(e['landClass'] in [3, 4] for e in edges),
              'limits': ['Visible descending rock and explicit impassable-space faces require native review.',
                         'Water termination needs its own appearance treatment; dry rock is not a waterfall.',
                         'No terrain heights, source destinations, travel bounds or canonical geometry are changed.']}
    return report


def author_rim(author, plan):
    nodes = {tuple(n['grid']): n['rings'] for n in plan['nodes']}
    boundary = {tuple(n['grid']): n['boundary'] for n in plan['nodes']}
    outward = {tuple(n['grid']): n['outward'] for n in plan['nodes']}
    overrides = []
    for start in range(0, len(plan['edges']), 32):
        group = plan['edges'][start:start+32]
        identity = 'rim_'+str(start//32)
        prop = {'id': identity, 'semanticId': 'mm5:sw/rim/'+identity, 'title': 'Xeen world rim',
                'frontOrigin': [0, 0], 'frontOutward': [0, -1], 'frontTangent': [1, 0], 'padHeight': 0}
        panels, restrictions, spills = [], [], []
        for edge in group:
            a, b = [nodes[tuple(n)] for n in edge['nodes']]
            if edge['landClass'] not in [3, 4]:
                samples = edge['capSamples']
                for left, right in zip(samples, samples[1:]):
                    outer = [[a[0][i]+s['t']*(b[0][i]-a[0][i]) for i in range(3)] for s in [left, right]]
                    cap = [left['point'], right['point'], outer[1], outer[0]]
                    uv = [(p[0]/512, p[1]/512) for p in cap]
                    for corners in [(0, 1, 2), (0, 2, 3)]:
                        author.panel(panels, [cap[i] for i in corners], 'rctyl', [uv[i] for i in corners])
            for level in range(4):
                points = [a[level], b[level], b[level+1], a[level+1]]
                # Project at the terrain rock's 512-unit repeat, independently of triangle edges.
                tangent = [(b[0][i]-a[0][i])/512 for i in range(2)]
                uv = [(sum((p[i]-a[0][i])*tangent[i] for i in range(2))/512, p[2]/512) for p in points]
                for corners in [(0, 1, 2), (0, 2, 3)]:
                    author.panel(panels, [points[i] for i in corners], 'rctyl', [uv[i] for i in corners])
            if edge['landClass'] in [3, 4]:
                water_rings = []
                for grid, ring in zip(edge['nodes'], [a, b]):
                    normal = outward[tuple(grid)]
                    water_rings.append([[p[0]+normal[0]*(32 if level else 0),
                                         p[1]+normal[1]*(32 if level else 0), p[2]+1]
                                        for level, p in enumerate(ring)])
                for level in range(4):
                    points = [water_rings[0][level], water_rings[1][level],
                              water_rings[1][level+1], water_rings[0][level+1]]
                    tangent = [(b[0][i]-a[0][i])/512 for i in range(2)]
                    uv = [(sum((p[i]-a[0][i])*tangent[i] for i in range(2))/512, p[2]/512) for p in points]
                    for corners in [(0, 1, 2), (0, 2, 3)]:
                        author.panel(spills, [points[i] for i in corners], 'wtrtyl', [uv[i] for i in corners])
            # Normal points into valid land: prevent entering source space, with no visible wall or event face.
            boundary_a, boundary_b = [boundary[tuple(n)] for n in edge['nodes']]
            points = [[boundary_a[0], boundary_a[1], plan['boundaryBottom']],
                      [boundary_b[0], boundary_b[1], plan['boundaryBottom']],
                      [boundary_b[0], boundary_b[1], plan['boundaryTop']],
                      [boundary_a[0], boundary_a[1], plan['boundaryTop']]]
            author.panel(restrictions, points, 'rctyl')
        author.model(identity+'_cliff', panels, prop)
        author.model(identity+'_space_boundary', restrictions, prop)
        index = len(author.metadata['bmodels'])-1
        overrides.extend({'bmodel_index': index, 'face_index': i, 'legacy_attributes': 0x2000,
                          'cog_number': 0, 'cog_triggered_number': 0, 'cog_trigger': 0}
                         for i in range(len(restrictions)))
        for obj in author.scene.objects:
            if obj.get('assembly_id') == identity and 'space_boundary' in obj.name:
                obj.hide_render = True
                obj['space_boundary_only'] = True
        if spills:
            author.model(identity+'_water_spill', spills, prop)
            index = len(author.metadata['bmodels'])-1
            overrides.extend({'bmodel_index': index, 'face_index': i, 'legacy_attributes': 0x20000004,
                              'cog_number': 0, 'cog_triggered_number': 0, 'cog_trigger': 0}
                             for i in range(len(spills)))
        author.semantic.setdefault('landscape', []).append(prop)
    return overrides
