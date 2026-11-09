"""Original faceted rock hoods, supported entrance floors and restrained mine equipment."""
from author_props import ground_at
from prepare_natural_entrances import world


def align_rock_uvs(author, panels, palette):
    # Adjacent triangles share a local projection instead of restarting/rotating the bitmap at every first edge.
    key = palette['rock']
    width, height = author.sizes[key]
    for index, (points, material, uv) in enumerate(panels):
        if material != key:
            continue
        a = [points[1][i]-points[0][i] for i in range(3)]
        b = [points[-1][i]-points[0][i] for i in range(3)]
        normal = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
        drop = max(range(3), key=lambda i: abs(normal[i]))
        u, v = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[drop]
        panels[index] = (points, material, [(p[u]/width, p[v]/height) for p in points])


def rock_recess(author, panels, component, palette, site, height):
    geometry = site['entranceGeometry']
    front, rear = geometry['frontDepth'], geometry['rearDepth']
    low, end = geometry['frontFloor'], geometry['rearFloor']
    name = site['id']+'_'+component['id']

    def ground(x, y):
        return ground_at(height, world(site, [x, y, 0]))-site['padHeight']-32

    # Matching open-bottom profiles form a real recessed hood, not an opaque rock with a black decal.
    inside = [(-160, front, low), (-160, front, low+224), (-96, front, low+288),
              (32, front, low+304), (128, front, low+272), (160, front, low+192), (160, front, low)]
    outside = [(x, front-64, low+z) for x, z in geometry['outerProfile']]
    outside = [(-384, 0, ground(-384, 0))] + outside + [(384, 0, ground(384, 0))]
    # Eight outer points versus seven inner points: split the left shoulder into a separate front triangle.
    author.panel(panels, [outside[0], inside[0], outside[1]], palette['rock'])
    outer = outside[1:]
    for i in range(6):
        a, b, c, d = outer[i], inside[i], inside[i+1], outer[i+1]
        author.panel(panels, [a, b, c], palette['rock'])
        author.panel(panels, [a, c, d], palette['rock'])
    # Close both front shoulders beneath the raised lip; an open edge reads as a floating rock sheet.
    author.panel(panels, [outside[0], inside[0], (-160, front, ground(-160, front))], palette['rock'])
    author.panel(panels, [inside[-1], outside[-1], (160, front, ground(160, front))], palette['rock'])
    back = [(x*.65, rear, z-low+end) for x, y, z in inside]
    for i in range(6):
        # Inward-facing tunnel walls/ceiling; four triangles handle the changing width and descent.
        author.panel(panels, [inside[i], back[i], back[i+1]], palette['rock'])
        author.panel(panels, [inside[i], back[i+1], inside[i+1]], palette['rock'])
    # Outer rear tapers into the ground. Its crown continues beyond the dark recess for a closed silhouette.
    rear_profile = [(x*.8, 544, low+z*.72) for x, z in geometry['outerProfile']]
    rear_profile = [(-384, 576, ground(-384, 576))] + rear_profile + [(384, 576, ground(384, 576))]
    for i in range(len(outside)-1):
        author.panel(panels, [outside[i], outside[i+1], rear_profile[i+1]], palette['rock'])
        author.panel(panels, [outside[i], rear_profile[i+1], rear_profile[i]], palette['rock'])
    bottom = [(x, 576, ground(x, 576)) for x, y, z in rear_profile]
    for i in range(len(bottom)-1):
        if rear_profile[i+1] != bottom[i+1]:
            author.panel(panels, [rear_profile[i], rear_profile[i+1], bottom[i+1]], palette['rock'])
        if bottom[i] != bottom[i+1] and rear_profile[i] != bottom[i]:
            author.panel(panels, [rear_profile[i], bottom[i+1], bottom[i]], palette['rock'])
    # The bottom footprint is buried. Endpoints share the native-ground skirt at all four corners.
    floor = [(-384, 0, ground(-384, 0)), (384, 0, ground(384, 0)),
             (384, 576, ground(384, 576)), (-384, 576, ground(-384, 576))]
    first = len(panels)
    for tri in [[floor[2], floor[1], floor[0]], [floor[3], floor[2], floor[0]]]:
        author.panel(panels, tri, palette['rock'])
    site.setdefault('entranceChecks', []).append({'model': name, 'faces': [first, first+1], 'kind': 'buried skirt'})
    align_rock_uvs(author, panels, palette)


def details(author, panels, site, palette, height):
    geometry = site['entranceGeometry']
    name = site['id']+'_service_details'
    faces = []
    for tri in geometry['walkingTriangles']:
        faces.append(len(panels))
        author.panel(panels, tri, palette['rock'])
    site.setdefault('entranceChecks', []).append({'model': name, 'faces': faces, 'kind': 'supported walking floor'})
    # Close the floor edges down into terrain. No grass can show through the vestibule.
    triangles = geometry['walkingTriangles']
    edges = {}
    for triangle in triangles:
        for a, b in zip(triangle, triangle[1:]+triangle[:1]):
            key = tuple(sorted((tuple(a), tuple(b))))
            edges.setdefault(key, []).append((a, b))
    for occurrences in edges.values():
        if len(occurrences) != 1:
            continue
        a, b = occurrences[0]
        lower = [[p[0], p[1], ground_at(height, world(site, p))-site['padHeight']-32] for p in [a, b]]
        author.panel(panels, [lower[0], lower[1], b], palette['rock'])
        author.panel(panels, [lower[0], b, a], palette['rock'])
    align_rock_uvs(author, panels, palette)
    if site['id'] != 'mine':
        return
    z = geometry['frontFloor']; y = geometry['frontDepth']+24
    # A pair of posts and a lintel identify worked geology. The central passage retains 256-unit headroom.
    for x in [-152, 128]:
        bottom = ground_at(height, world(site, [x, y, 0]))-site['padHeight']-32
        first = len(panels)
        author.box(panels, [x, y-12, bottom, x+24, y+12, z+256], palette['wood'])
        site['entranceChecks'].append({'model': name, 'faces': [first+4], 'kind': 'buried mine support'})
    author.box(panels, [-160, y-16, z+256, 160, y+16, z+280], palette['crosswood'])
    # One closed supply crate outside the left approach. It is inert equipment, not a loot container.
    x, y = -288, 0
    z = max(ground_at(height, world(site, [x+dx, y+dy, 0])) for dx in [0, 96] for dy in [0, 96])
    z -= site['padHeight']
    author.box(panels, [x, y, z-32, x+96, y+96, z+96], palette['crate'])


def interaction(author, panels, site, palette, venue):
    g = site['entranceGeometry']; y = g['rearDepth']; z = g['rearFloor']
    # Convex dark cap at the back of a physical vestibule. All clicks remain in this map.
    points = [(-104, y, z), (104, y, z), (104, y, z+192), (83.2, y, z+272),
              (20.8, y, z+304), (-62.4, y, z+288), (-104, y, z+224)]
    for i in range(1, len(points)-1):
        author.panel(panels, [points[0], points[i], points[i+1]], palette['dark'])
