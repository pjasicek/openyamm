"""Original climbing rope, ground coil and timber brace lashed to a live tree; authored map geometry."""
import math

PALETTE = {'rope': 't06c11', 'branch': 't06a10'}


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def unit(vector):
    length = math.sqrt(sum(v*v for v in vector))
    assert length > 0
    return [v/length for v in vector]


def tube(author, panels, path, radii, key, sides=6):
    rings = []
    for index, point in enumerate(path):
        before, after = path[max(0, index-1)], path[min(len(path)-1, index+1)]
        tangent = unit([after[i]-before[i] for i in range(3)])
        axis = [0, 0, 1] if abs(tangent[2]) < .9 else [0, 1, 0]
        u = unit(cross(tangent, axis))
        v = cross(tangent, u)
        rings.append([[point[k]+radii[index]*(u[k]*math.cos(j*math.tau/sides)
                       +v[k]*math.sin(j*math.tau/sides)) for k in range(3)] for j in range(sides)])
    for first, last in zip(rings, rings[1:]):
        for j in range(sides):
            k = (j+1)%sides
            author.panel(panels, [first[j], first[k], last[k], last[j]], key)
    author.panel(panels, list(reversed(rings[0])), key)
    author.panel(panels, rings[-1], key)


def branch(author, panels, palette):
    # Lower end is lashed at the visible trunk; the upper brace continues into the canopy.
    tube(author, panels, [[0, 288, 400], [96, 288, 608], [144, 288, 736]],
         [18, 14, 8], palette['branch'], 8)
    path = [[36*math.cos(i*math.tau/8), 288+36*math.sin(i*math.tau/8), 384+i*32/16]
            for i in range(17)]
    tube(author, panels, path, [6]*len(path), palette['rope'], 5)


def rope(author, panels, palette):
    # Preserve the former three-strand envelope with one cord; the native rope texture supplies its fine grain.
    path = [[128-8*t, 224+64*t, 48+612*t] for t in [0, .25, .5, .75, 1]]
    tube(author, panels, path, [8.5]*len(path), palette['rope'])
    # Two turns of the loose lower coil remain part of the same readable contact.
    path = []
    for i in range(25):
        t = i/24
        radius = 48-32*t
        path.append([80+radius*math.cos(t*math.tau*2), 224+radius*math.sin(t*math.tau*2),
                     48-41*min(1, t*4)])
    tube(author, panels, path, [7]*len(path), palette['rope'], 5)
    # Wrap the rope around the inclined branch, terminating inside the knot instead of in open air.
    axis = unit([48, 0, 128])
    u, v = [0, 1, 0], unit([-128, 0, 48])
    path = []
    for i in range(17):
        t = i/16
        angle = t*math.tau*2
        path.append([[120, 288, 672][k]+axis[k]*(t-.5)*24
                     +18*(u[k]*math.cos(angle)+v[k]*math.sin(angle)) for k in range(3)])
    tube(author, panels, path, [6]*len(path), palette['rope'], 5)
