"""Approved layered minimap processing, shared by the pilot and batch exporter."""
import io
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def rgba(array):
    return Image.fromarray(np.round(np.clip(array, 0, 1)*255).astype('uint8'))


def grade(array, recipe):
    rgb, alpha = array[:, :, :3], array[:, :, 3:]
    settings = recipe['global_grade']
    pivot = settings['contrast_pivot']
    rgb = np.clip((rgb-pivot)*settings['contrast']+pivot, 0, 1)
    gray = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
    rgb = np.clip(gray[:, :, None] + (rgb-gray[:, :, None])*settings['saturation'], 0, 1)
    # Normalized convolution keeps invisible black RGB from causing bright outline halos.
    unsharp = recipe['unsharp']
    radius = unsharp['radius_master_pixels']
    blurred_alpha = gaussian_filter(alpha, (radius, radius, 0))
    blurred = gaussian_filter(rgb*alpha, (radius, radius, 0))/np.maximum(blurred_alpha, 1e-6)
    difference = rgb-blurred
    rgb += np.where(abs(difference)*255 >= unsharp['threshold_255'], difference*unsharp['amount'], 0)
    return np.concatenate((np.clip(rgb, 0, 1), alpha), axis=2)


def random_pick(array, settings):
    """Seeded neighbor sampling, bounded to one output pixel; never run on buildings."""
    rng = np.random.default_rng(settings['seed'])
    radius = settings['radius_master_pixels']
    neighbors = np.array([(dy, dx) for dy in range(-radius, radius+1) for dx in range(-radius, radius+1)
                          if dx*dx+dy*dy <= radius*radius])
    height, width = array.shape[:2]
    offsets = neighbors[rng.integers(len(neighbors), size=(height, width))]
    y, x = np.indices((height, width))
    sampled = array[np.clip(y+offsets[:, :, 0], 0, height-1), np.clip(x+offsets[:, :, 1], 0, width-1)]
    weight = (rng.random((height, width)) < settings['probability'])*settings['blend']
    result = array*(1-weight[:, :, None])+sampled*weight[:, :, None]
    # No transparency/coverage change, including the map boundary.
    result[:, :, 3] = array[:, :, 3]
    return result.astype(np.float32)


def composite(terrain, objects):
    # Terrain extends to the camera boundary. Its edge AA does not make a minimap transparent.
    terrain = terrain.copy()
    terrain[:, :, 3] = 1
    return Image.alpha_composite(rgba(terrain), rgba(objects)).convert('RGB')


def openraster(path, terrain, objects, merged, name='New Sorpigal - vinevi process'):
    root = ET.Element('image', w=str(merged.width), h=str(merged.height), name=name,
                      version='0.0.3')
    stack = ET.SubElement(root, 'stack')
    layers = [('Objects - levels, grade, sharpen; original alpha', 'data/objects.png', rgba(objects)),
              ('Terrain - bounded Random Pick, grade, sharpen', 'data/terrain.png', rgba(terrain))]
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for name, src, image in layers:
            ET.SubElement(stack, 'layer', name=name, src=src, x='0', y='0', opacity='1.0', visibility='visible',
                          **{'composite-op': 'svg:src-over'})
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            archive.writestr(src, buffer.getvalue())
        archive.writestr('stack.xml', ET.tostring(root, encoding='utf-8'))
        buffer = io.BytesIO()
        merged.save(buffer, format='PNG')
        archive.writestr('mergedimage.png', buffer.getvalue())
        merged = merged.copy()
        merged.thumbnail((256, 256))
        buffer = io.BytesIO()
        merged.save(buffer, format='PNG')
        archive.writestr('Thumbnails/thumbnail.png', buffer.getvalue())
