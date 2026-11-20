"""Recorded local sprite geometry edits at generated resolution, before final downsampling.

Color is filtered premultiplied; every material channel uses the identical inverse
map. Mesh controls are editing constraints, never independent acceptance evidence.
"""
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.spatial import Delaunay


def deform(image, mask, specification):
    assert image.mode == 'RGBA' and image.size == mask.size
    assert specification['reason'] and specification['authorization']
    input_size = image.size
    points = np.array([p[key] for p in specification['controls'] for key in ('source_raw', 'target_raw')])
    if len(points):
        assert np.isfinite(points).all() and (points >= 0).all(), 'Invalid local edit coordinates'
        # A downward repair must not lose pixels at the old extraction boundary.
        padded_size = tuple(np.maximum(input_size, np.ceil(points.max(axis=0)).astype(int)+2))
        if padded_size != input_size:
            padded = Image.new('RGBA', padded_size)
            padded.paste(image, (0, 0))
            padded_mask = Image.new(mask.mode, padded_size)
            padded_mask.paste(mask, (0, 0))
            image, mask = padded, padded_mask
    width, height = image.size
    corners = [[0, 0], [width - 1, 0], [0, height - 1], [width - 1, height - 1]]
    source = np.array(corners + [p['source_raw'] for p in specification['controls']], dtype=float)
    target = np.array(corners + [p['target_raw'] for p in specification['controls']], dtype=float)
    assert len(np.unique(source, axis=0)) == len(source), 'Duplicate mesh controls'
    for points in (source, target):
        assert np.isfinite(points).all()
        assert (points >= 0).all() and (points <= [width - 1, height - 1]).all(), 'Mesh outside raw canvas'
    mesh = Delaunay(source)
    yy, xx = np.mgrid[:height, :width]
    coordinates = np.array([yy, xx], dtype=float)
    triangle_ids = np.full((height, width), -1, dtype=np.int32)
    expansions = []
    for index, triangle in enumerate(mesh.simplices):
        src, dst = source[triangle], target[triangle]
        src_basis = (src[1:] - src[0]).T
        dst_basis = (dst[1:] - dst[0]).T
        assert np.linalg.det(dst_basis) / np.linalg.det(src_basis) > 1e-5, 'Folded or collapsed mesh'
        expansions.append(float(np.linalg.svd(dst_basis @ np.linalg.inv(src_basis), compute_uv=False).max()))
        low = np.maximum(0, np.floor(dst.min(axis=0)).astype(int))
        high = np.minimum([width - 1, height - 1], np.ceil(dst.max(axis=0)).astype(int))
        gx, gy = xx[low[1]:high[1]+1, low[0]:high[0]+1], yy[low[1]:high[1]+1, low[0]:high[0]+1]
        positions = np.stack((gx - dst[0, 0], gy - dst[0, 1]), axis=-1)
        bary = positions @ np.linalg.inv(dst_basis).T
        inside = (bary >= -1e-8).all(axis=-1) & (bary.sum(axis=-1) <= 1 + 1e-8)
        mapped = bary @ src_basis.T + src[0]
        for axis in range(2):
            field = coordinates[1-axis, low[1]:high[1]+1, low[0]:high[0]+1]
            field[inside] = mapped[:, :, axis][inside]
        triangle_ids[low[1]:high[1]+1, low[0]:high[0]+1][inside] = index
    assert (triangle_ids >= 0).all(), 'Incomplete inverse mesh'
    coordinates[0] = np.clip(coordinates[0], 0, height - 1)
    coordinates[1] = np.clip(coordinates[1], 0, width - 1)

    def sample(values):
        return map_coordinates(values.astype(float), coordinates, order=1, mode='nearest', prefilter=False)

    pixels = np.array(image, dtype=float)
    alpha = pixels[:, :, 3] / 255
    warped_alpha = sample(alpha)
    output = np.zeros_like(pixels)
    for channel in range(3):
        output[:, :, channel] = sample(pixels[:, :, channel] * alpha) / np.maximum(warped_alpha, 1e-12)
    output[:, :, 3] = warped_alpha * 255
    output = np.clip(np.round(output), 0, 255).astype(np.uint8)
    weights = np.array(mask)
    bands = [sample(weights)] if weights.ndim == 2 else [sample(weights[:, :, c]) for c in range(weights.shape[2])]
    warped_mask = np.clip(np.stack(bands, axis=-1), 0, 255)
    if weights.ndim == 3:
        warped_mask *= np.minimum(1, 255 / np.maximum(1, warped_mask.sum(axis=-1, keepdims=True)))
    warped_mask = (np.floor(warped_mask + 1e-8) if weights.ndim == 3 else
                   np.round(warped_mask)).astype(np.uint8)
    warped_mask[output[:, :, 3] == 0] = 0
    if weights.ndim == 2:
        warped_mask = warped_mask[:, :, 0]
    occupied = np.unique(triangle_ids[output[:, :, 3] > 0])
    # Expansion of entirely transparent canvas does not magnify any artwork.
    maximum_expansion = max([1.0] + [expansions[i] for i in occupied])
    record = dict(reason=specification['reason'], authorization=specification['authorization'],
                  input_size=list(input_size), padded_size=[width, height],
                  source_raw=source.tolist(), target_raw=target.tolist(), triangles=mesh.simplices.tolist(),
                  maximum_occupied_expansion=maximum_expansion,
                  method='Piecewise affine inverse map at generated resolution; linear premultiplied RGBA; identical mask map')
    return Image.fromarray(output), Image.fromarray(warped_mask), record


def transform_points(points, record):
    source, target = np.array(record['source_raw']), np.array(record['target_raw'])
    points = np.array(points, dtype=float)
    result = points.copy()
    assigned = np.zeros(len(points), dtype=bool)
    for triangle in record['triangles']:
        src, dst = source[triangle], target[triangle]
        bary = (points - src[0]) @ np.linalg.inv((src[1:] - src[0]).T).T
        inside = (bary >= -1e-8).all(axis=1) & (bary.sum(axis=1) <= 1 + 1e-8)
        result[inside] = bary[inside] @ (dst[1:] - dst[0]) + dst[0]
        assigned |= inside
    assert assigned.all(), 'Landmark outside mesh'
    return result
