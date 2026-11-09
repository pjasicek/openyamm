"""Engine burn death (v8): drop the flame cards, card bones and charred remains, then bake one burn map per material.

The native death sets the outline alight first (wing edges, head, tail tip) and burns inward, the membranes fastest,
until the whole body is a shape of fire. Burn order = surface distance from those ignition points (wing faces at half
cost), with broad 3D noise, equalised to 0..1 by surface area; texels add fine noise so the front is ragged.
Red: burn order. Green: ridged noise for the glowing cracks of the charred band. Reads work/reduced_v7_source.blend,
writes work/burn_v8_source.blend and textures/drg1_{body,head,wings}_burn.png.
"""
import bpy
import heapq
import json
import numpy as np
from pathlib import Path

P = Path(__file__).resolve().parents[1]
SIZE = 1024
WING_COST = 0.5

bpy.ops.wm.open_mainfile(filepath=str(P / 'work/reduced_v7_source.blend'))
body = bpy.data.objects['Body']
rig = bpy.data.objects['Rig']
bpy.data.objects.remove(bpy.data.objects['DeathFlames'], do_unlink=True)

# Charred remains (material slot 3) go: the burnt-out corpse draws nothing and the loot satchel takes its place.
import bmesh
bm = bmesh.new()
bm.from_mesh(body.data)
remains = [f for f in bm.faces if f.material_index == 3]
bmesh.ops.delete(bm, geom=remains, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(body.data)
bm.free()
assert body.data.materials[3].name == 'DrakeRemains'
body.data.materials.pop(index=3)
for group in [g for g in body.vertex_groups if g.name == 'Remains' or g.name.startswith('Burn_')]:
    body.vertex_groups.remove(group)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for bone in [b for b in rig.data.edit_bones if b.name == 'Remains' or b.name.startswith('Burn_')]:
    rig.data.edit_bones.remove(bone)
bpy.ops.object.mode_set(mode='OBJECT')
print('REMOVED remains faces', len(remains), 'bones now', len(rig.data.bones))

me = body.data
co = np.array([v.co[:] for v in me.vertices])
material = np.array([p.material_index for p in me.polygons])
names = [g.name for g in body.vertex_groups]
dominant = [names[max(v.groups, key=lambda e: e.weight).group] if len(v.groups) else '' for v in me.vertices]

# Surface graph; an edge on wing faces costs half its length.
wing_vertex = np.zeros(len(co), bool)
for polygon in me.polygons:
    if polygon.material_index == 2:
        wing_vertex[list(polygon.vertices)] = True
edge_faces = {}
for polygon in me.polygons:
    for key in polygon.edge_keys:
        edge_faces.setdefault(key, []).append(polygon.index)
neighbours = [[] for _ in co]
for (a, b), faces in edge_faces.items():
    cost = np.linalg.norm(co[a] - co[b]) * (WING_COST if wing_vertex[a] and wing_vertex[b] else 1.0)
    neighbours[a].append((b, cost))
    neighbours[b].append((a, cost))

# Ignition: the membranes' open edges, the head and the tail tip.
sources = set()
for (a, b), faces in edge_faces.items():
    if len(faces) == 1 and all(material[f] == 2 for f in faces):
        sources.update((a, b))
sources.update(i for i, name in enumerate(dominant) if name in ('Head', 'Tail8', 'Tail9'))
distance = np.full(len(co), np.inf)
queue = [(0.0, i) for i in sources]
for _, i in queue:
    distance[i] = 0.0
heapq.heapify(queue)
while queue:
    d, i = heapq.heappop(queue)
    if d > distance[i]:
        continue
    for j, cost in neighbours[i]:
        if d + cost < distance[j]:
            distance[j] = d + cost
            heapq.heappush(queue, (d + cost, j))
unreached = ~np.isfinite(distance)
distance[unreached] = distance[~unreached].max()


def hash3(cells):
    h = (cells[..., 0] * 73856093) ^ (cells[..., 1] * 19349663) ^ (cells[..., 2] * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xffff).astype(np.float64) / 65535.0


def value_noise(points):
    cell = np.floor(points).astype(np.int64)
    f = points - cell
    f = f * f * (3 - 2 * f)
    result = 0.0
    for corner in range(8):
        offset = np.array([(corner >> axis) & 1 for axis in range(3)])
        weight = np.prod(np.where(offset == 1, f, 1 - f), axis=-1)
        result = result + weight * hash3(cell + offset)
    return result


def fbm(points, octaves=3):
    total, amplitude, scale = 0.0, 0.5, 1.0
    for _ in range(octaves):
        total = total + amplitude * value_noise(points * scale)
        amplitude *= 0.5
        scale *= 2.03
    return total / (1 - 0.5 ** octaves)


order = distance / distance.max() + 0.22 * (fbm(co * 3.2 + 11.0) - 0.5)
# Equalise by surface area, not vertex count, so the front sweeps area evenly (the dense head is no slower).
area = np.zeros(len(co))
for polygon in me.polygons:
    area[list(polygon.vertices)] += polygon.area / len(polygon.vertices)
sorted_vertices = np.argsort(order, kind='stable')
cumulative = np.cumsum(area[sorted_vertices])
vertex_order = np.empty(len(co))
vertex_order[sorted_vertices] = 0.02 + 0.94 * (cumulative - 0.5 * area[sorted_vertices]) / cumulative[-1]

uv = me.uv_layers.active.data
me.calc_loop_triangles()
report = {'remains_faces_removed': len(remains), 'ignition_vertices': len(sources),
          'unreached_vertices': int(unreached.sum()), 'maps': {}}
for slot, label in enumerate(['body', 'head', 'wings']):
    values = np.full((SIZE, SIZE), np.nan)
    position = np.zeros((SIZE, SIZE, 3))
    overlap = 0
    for triangle in me.loop_triangles:
        if material[triangle.polygon_index] != slot:
            continue
        corners = np.array([uv[loop].uv[:] for loop in triangle.loops]) * SIZE
        vertices = list(triangle.vertices)
        x0, y0 = np.maximum(np.floor(corners.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(corners.max(0)).astype(int), SIZE - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = corners
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.01) & (w1 >= -0.01) & (w2 >= -0.01)
        if not inside.any():
            continue
        rows = (SIZE - 1 - (ys[inside] - 0.5)).astype(int)   # image rows run top-down, Blender v bottom-up
        columns = (xs[inside] - 0.5).astype(int)
        weights = np.stack([w0[inside], w1[inside], w2[inside]], -1)
        overlap += int(np.isfinite(values[rows, columns]).sum())
        values[rows, columns] = weights @ vertex_order[vertices]
        position[rows, columns] = weights @ co[vertices]
    covered = np.isfinite(values)
    fine = fbm(position * 14.0 + 3.0) - 0.5
    red = np.where(covered, np.clip(values + 0.12 * fine, 0.0, 1.0), np.nan)
    ridge = 1.0 - np.abs(2.0 * fbm(position * 9.0 + 29.0, 2) - 1.0)
    green = np.where(covered, ridge ** 4, np.nan)
    # Pad islands so filtering and mips at their borders keep island values.
    for _ in range(16):
        missing = ~np.isfinite(red)
        if not missing.any():
            break
        stack_r = np.stack([np.roll(np.roll(red, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
        stack_g = np.stack([np.roll(np.roll(green, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
        known = np.isfinite(stack_r)
        count = known.sum(0)
        fill = missing & (count > 0)
        red[fill] = np.nansum(stack_r, 0)[fill] / count[fill]
        green[fill] = np.nansum(stack_g, 0)[fill] / count[fill]
    red = np.nan_to_num(red, nan=1.0)
    green = np.nan_to_num(green, nan=0.0)
    rgba = np.ones((SIZE, SIZE, 4), np.float32)
    rgba[..., 0] = np.round(red * 255) / 255
    rgba[..., 1] = np.round(green * 255) / 255
    rgba[..., 2] = 0.0
    image = bpy.data.images.new(f'drg1_{label}_burn', SIZE, SIZE, alpha=False)
    image.colorspace_settings.name = 'Non-Color'
    image.pixels.foreach_set(rgba[::-1].ravel())   # Blender pixel rows run bottom-up
    image.filepath_raw = str(P / f'textures/drg1_{label}_burn.png')
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)
    report['maps'][label] = {'covered_texels': int(covered.sum()), 'overlapping_writes': overlap,
                             'order_range': [float(np.nanmin(values)), float(np.nanmax(values))]}
    print('BURN_MAP', label, report['maps'][label])

bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/burn_v8_source.blend'))
(P / 'review/burn_v8').mkdir(parents=True, exist_ok=True)
(P / 'review/burn_v8/burn_maps.json').write_text(json.dumps(report, indent=2))
