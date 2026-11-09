"""Geometry and encoding helpers shared by the offline lighting producers (outdoor bake_outdoor.py, indoor
bake_indoor.py) and their regression tests."""
import math


def fnv(data):
    """FNV-1a 64 of a byte string: the content hash every bake records for its geometry and dependencies."""
    h = 14695981039346656037
    for b in data:
        h = ((h ^ b) * 1099511628211) & 0xffffffffffffffff
    return h


def rgbm(pixels):
    """Encode linear float RGB(A) rows (height, width, 4) as BGRM texels: RGB * M * 4, M the rounded-up maximum
    channel over four (minimum 1/255). Rejects values above four or nonfinite samples."""
    import numpy as np
    rgb = np.maximum(pixels[:, :, :3], 0)
    if not np.isfinite(rgb).all() or float(rgb.max()) > 4:
        raise ValueError('Lighting exceeds RGBM4 range or contains nonfinite samples')
    m = np.maximum(np.ceil(rgb.max(axis=2) * 255 / 4), 1)
    rgba = np.empty(pixels.shape, dtype=np.uint8)
    rgba[:, :, :3] = np.rint(np.clip(rgb / (m[:, :, None] * 4 / 255), 0, 1) * 255)
    rgba[:, :, 3] = m.astype(np.uint8)
    # Blender bottom-up data is kept: runtime lighting UVs use the same coordinates.
    return rgba[:, :, [2, 1, 0, 3]].tobytes()


def rle_bgra(pixels):
    """Encode BGRA texels as PackBits-style literal and repeated-pixel spans."""
    if len(pixels) % 4:
        raise ValueError('BGRA payload is not pixel aligned')
    output = bytearray()
    pixel_count = len(pixels) // 4
    index = 0
    while index < pixel_count:
        run = 1
        pixel = pixels[index * 4:(index + 1) * 4]
        while run < 128 and index + run < pixel_count \
                and pixels[(index + run) * 4:(index + run + 1) * 4] == pixel:
            run += 1
        if run >= 2:
            output.append(0x80 | (run - 1))
            output.extend(pixel)
            index += run
            continue

        start = index
        index += 1
        while index - start < 128 and index < pixel_count:
            if index + 1 < pixel_count \
                    and pixels[index * 4:(index + 1) * 4] == pixels[(index + 1) * 4:(index + 2) * 4]:
                break
            index += 1
        output.append(index - start - 1)
        output.extend(pixels[start * 4:index * 4])
    return bytes(output)


def pack_lightmap_charts(chart_sizes, page_size, padding=4, first_fit=False):
    """Pack chart rectangles into deterministic shelves and return cropped pages.

    Placements identify the chart area; each chart retains ``padding`` texels on
    every side for the bake margin. Pages are cropped to the occupied outer
    rectangles instead of retaining the square packing limit. The default (the
    outdoor bakes' layout) opens a new shelf for a chart rather than leave height
    unused in a taller one; ``first_fit`` places each chart in the first shelf
    with room (first-fit decreasing height), which packs thousands of small
    indoor charts far more densely.
    """
    if page_size <= padding * 2:
        raise ValueError('lightmap page is too small for chart padding')

    maximum_chart_size = page_size - padding * 2
    normalized = [(min(width, maximum_chart_size), min(height, maximum_chart_size))
                  for width, height in chart_sizes]
    order = sorted(range(len(normalized)),
                   key=lambda index: (-normalized[index][1], -normalized[index][0], index))
    pages = []
    placements = [None] * len(normalized)

    for chart_index in order:
        width, height = normalized[chart_index]
        outer_width = width + padding * 2
        outer_height = height + padding * 2
        best = None
        for page_index, page in enumerate(pages):
            if first_fit and best is not None:
                break
            for shelf_index, shelf in enumerate(page['shelves']):
                if first_fit and best is not None:
                    break
                if outer_height <= shelf['height'] and shelf['x'] + outer_width <= page_size:
                    score = (shelf['height'] - outer_height,
                             page_size - shelf['x'] - outer_width, page_index, shelf_index)
                    if best is None or score < best[0]:
                        best = score, page_index, shelf_index
            if page['height'] + outer_height <= page_size and not (first_fit and best is not None):
                score = (0, page_size - outer_width, page_index, len(page['shelves']))
                if best is None or score < best[0]:
                    best = score, page_index, len(page['shelves'])

        if best is None:
            pages.append({'shelves': [], 'width': 0, 'height': 0})
            page_index = len(pages) - 1
            shelf_index = 0
        else:
            _, page_index, shelf_index = best

        page = pages[page_index]
        if shelf_index == len(page['shelves']):
            page['shelves'].append({'x': 0, 'y': page['height'], 'height': outer_height})
            page['height'] += outer_height
        shelf = page['shelves'][shelf_index]
        outer_x, outer_y = shelf['x'], shelf['y']
        shelf['x'] += outer_width
        page['width'] = max(page['width'], shelf['x'])
        placements[chart_index] = (page_index, outer_x + padding, outer_y + padding, width, height)

    dimensions = [(page['width'], page['height']) for page in pages]
    return placements, dimensions


def face_basis(points):
    """Return an orthonormal chart basis from the largest native fan triangle.

    Legacy faces may begin with duplicate or collinear vertices. Only an entirely
    zero-area fan is degenerate; its first triangle is not sufficient evidence.
    """
    if len(points) < 3:
        return None
    best = None
    best_area_squared = 0.0
    for index in range(1, len(points) - 1):
        edge = tuple(points[index][k] - points[0][k] for k in range(3))
        other = tuple(points[index + 1][k] - points[0][k] for k in range(3))
        cross = (edge[1] * other[2] - edge[2] * other[1],
                 edge[2] * other[0] - edge[0] * other[2],
                 edge[0] * other[1] - edge[1] * other[0])
        area_squared = sum(value * value for value in cross)
        if area_squared > best_area_squared:
            best_area_squared = area_squared
            best = edge, cross
    if best is None or best_area_squared < 1e-6:
        return None
    edge, cross = best
    edge_length = math.sqrt(sum(value * value for value in edge))
    normal_length = math.sqrt(best_area_squared)
    axis_u = tuple(value / edge_length for value in edge)
    normal = tuple(value / normal_length for value in cross)
    axis_v = (normal[1] * axis_u[2] - normal[2] * axis_u[1],
              normal[2] * axis_u[0] - normal[0] * axis_u[2],
              normal[0] * axis_u[1] - normal[1] * axis_u[0])
    return axis_u, axis_v


def plane_chart_basis(normal):
    """An orthonormal in-plane basis for a lightmap chart, aligned with the world where it can be: world X and the
    in-plane Y for floors and ceilings, the horizontal and the slope direction for walls. Faces of the same plane
    then share texel rows and columns, so a chart grouping several of them has no seams between them."""
    nx, ny, nz = normal
    if abs(nz) >= 0.7:
        reference = (1.0, 0.0, 0.0)
        dot = reference[0] * nx
        axis_u = (1.0 - dot * nx, -dot * ny, -dot * nz)
    else:
        # Horizontal: up x normal.
        axis_u = (-ny, nx, 0.0)
    length = math.sqrt(sum(value * value for value in axis_u))
    axis_u = tuple(value / length for value in axis_u)
    axis_v = (ny * axis_u[2] - nz * axis_u[1], nz * axis_u[0] - nx * axis_u[2], nx * axis_u[1] - ny * axis_u[0])
    return axis_u, axis_v


def newell_normal(points):
    """The unnormalized polygon normal (Newell's method): twice the area, oriented by the winding."""
    n = [0.0, 0.0, 0.0]
    for index, current in enumerate(points):
        following = points[(index + 1) % len(points)]
        n[0] += (current[1] - following[1]) * (current[2] + following[2])
        n[1] += (current[2] - following[2]) * (current[0] + following[0])
        n[2] += (current[0] - following[0]) * (current[1] + following[1])
    return tuple(n)


def point_in_polygon(polygon, x, y):
    """Even-odd test of a point against a 2D polygon's (x, y) vertices; points on an edge may go either way."""
    inside = False
    for index, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[index - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


# Native terrain cell triangles as corner indices into [(gx, gy), (gx, gy + 1), (gx + 1, gy), (gx + 1, gy + 1)].
TERRAIN_CELL_TRIANGLES = ((0, 3, 2), (0, 1, 3))
# Barycentric sample points strictly inside a triangle: its centroid and points toward each corner and edge.
TRIANGLE_SAMPLES = ((1 / 3, 1 / 3, 1 / 3), (2 / 3, 1 / 6, 1 / 6), (1 / 6, 2 / 3, 1 / 6), (1 / 6, 1 / 6, 2 / 3),
                    (1 / 2, 1 / 2 - 1 / 12, 1 / 12), (1 / 12, 1 / 2, 1 / 2 - 1 / 12), (1 / 2 - 1 / 12, 1 / 12, 1 / 2))


def terrain_triangles_on_floors(heights, floors, height_scale=32):
    """The flat native terrain triangles that lie in the plane of a horizontal building face and under it.

    ``heights`` is the 128 x 128 native height map; ``floors`` lists (z, [(x, y), ...]) horizontal faces. A terrain
    triangle whose three corners have one height z, with a sample point inside a floor at that z, is returned as
    (gx, gy, triangle) with ``triangle`` indexing TERRAIN_CELL_TRIANGLES. Such a triangle coincides with the floor:
    Cycles' shadow and bounce rays from the floor hit it at zero distance, so the floor bakes black where they
    overlap (Ravenshore's crystal plaza). The producer keeps these triangles out of the other surfaces' rays.
    """
    by_height = {}
    for z, polygon in floors:
        xs = [x for x, _ in polygon]
        ys = [y for _, y in polygon]
        # The floor's own interior points (centroid, corners pulled slightly inward) catch a floor smaller than the
        # triangle, which the triangle's sample points can miss.
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        inner = [(cx, cy)] + [(x + (cx - x) * 0.01, y + (cy - y) * 0.01) for x, y in polygon]
        by_height.setdefault(round(z), []).append((min(xs), min(ys), max(xs), max(ys), polygon, inner))
    found = []
    for gy in range(127):
        for gx in range(127):
            corners = [(gx, gy), (gx, gy + 1), (gx + 1, gy), (gx + 1, gy + 1)]
            for triangle, indices in enumerate(TERRAIN_CELL_TRIANGLES):
                levels = {heights[corners[i][1] * 128 + corners[i][0]] for i in indices}
                if len(levels) != 1:
                    continue
                candidates = by_height.get(levels.pop() * height_scale)
                if not candidates:
                    continue
                points = [((corners[i][0] - 64) * 512, (64 - corners[i][1]) * 512) for i in indices]
                samples = [(sum(w * p[0] for w, p in zip(weights, points)),
                            sum(w * p[1] for w, p in zip(weights, points))) for weights in TRIANGLE_SAMPLES]
                if any(x0 <= x <= x1 and y0 <= y <= y1 and point_in_polygon(polygon, x, y)
                       for x, y in samples for x0, y0, x1, y1, polygon, _ in candidates) or any(
                           point_in_polygon(points, x, y) for *_, inner in candidates for x, y in inner):
                    found.append((gx, gy, triangle))
    return found


def group_coplanar_faces(faces, normal_tolerance=1e-3, distance_tolerance=1.0, waste=1.25):
    """Union coplanar faces that touch (share a vertex) into chart groups.

    ``faces`` is a list of (points, unit normal). Faces are coplanar when their normals agree within
    ``normal_tolerance`` (same facing: back-to-back faces never group) and their planes within
    ``distance_tolerance`` world units. Two groups join only while the joined chart's rectangle (in the plane's
    chart basis, plane_chart_basis) is at most ``waste`` times their two rectangles: a run of faces split at portals
    or by the BSP shares one chart and bakes without a seam, but a whole storey's floor does not become one mostly
    empty chart. Returns a list of groups, each a sorted list of face positions, ordered by their first face.
    """
    parent = list(range(len(faces)))
    boxes = []
    for points, normal in faces:
        axis_u, axis_v = plane_chart_basis(normal)
        us = [sum(p[k] * axis_u[k] for k in range(3)) for p in points]
        vs = [sum(p[k] * axis_v[k] for k in range(3)) for p in points]
        boxes.append((min(us), min(vs), max(us), max(vs)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def area(box):
        return (box[2] - box[0] + 1) * (box[3] - box[1] + 1)

    def plane_key(normal, distance):
        scale = 1 / normal_tolerance
        return (round(normal[0] * scale), round(normal[1] * scale), round(normal[2] * scale),
                round(distance / distance_tolerance))

    owners = {}
    for index, (points, normal) in enumerate(faces):
        distance = sum(normal[axis] * points[0][axis] for axis in range(3))
        key = plane_key(normal, distance)
        for point in points:
            vertex = (key, round(point[0]), round(point[1]), round(point[2]))
            other = owners.setdefault(vertex, index)
            first, second = find(index), find(other)
            if first == second:
                continue
            a, b = boxes[first], boxes[second]
            joined = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
            if area(joined) <= waste * (area(a) + area(b)):
                parent[first] = second
                boxes[second] = joined
    groups = {}
    for index in range(len(faces)):
        groups.setdefault(find(index), []).append(index)
    return sorted(groups.values(), key=lambda group: group[0])
