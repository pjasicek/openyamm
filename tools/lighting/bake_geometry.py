"""Geometry checks shared by the offline lighting producer and its regression tests."""
import math


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


def pack_lightmap_charts(chart_sizes, page_size, padding=4):
    """Pack chart rectangles into deterministic shelves and return cropped pages.

    Placements identify the chart area; each chart retains ``padding`` texels on
    every side for the bake margin. Pages are cropped to the occupied outer
    rectangles instead of retaining the square packing limit.
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
            for shelf_index, shelf in enumerate(page['shelves']):
                if outer_height <= shelf['height'] and shelf['x'] + outer_width <= page_size:
                    score = (shelf['height'] - outer_height,
                             page_size - shelf['x'] - outer_width, page_index, shelf_index)
                    if best is None or score < best[0]:
                        best = score, page_index, shelf_index
            if page['height'] + outer_height <= page_size:
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
