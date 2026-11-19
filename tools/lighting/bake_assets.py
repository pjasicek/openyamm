"""Native bake texture lookup using the runtime's merged development-package order."""
from pathlib import Path
import io
import struct


def read_cooked_surface(path):
    """Decode the desktop runtime's BC7 top mip, including its checked zstd container."""
    from PIL import Image
    import zstandard

    data = path.read_bytes()
    fields = struct.unpack_from('<15Q', data)
    if fields[0] != 0x313030584554594F or fields[1] != 3 or fields[2] != 1:
        raise ValueError('Expected a version-3 BC7 surface: ' + str(path))
    width, height = fields[5:7]
    if not 0 < width <= 8192 or not 0 < height <= 8192 or len(data) != 120 + fields[11]:
        raise ValueError('Invalid cooked surface dimensions or length: ' + str(path))
    blocks = zstandard.ZstdDecompressor().decompress(data[120:], max_output_size=fields[9])
    if len(blocks) != fields[9]:
        raise ValueError('Invalid cooked surface payload: ' + str(path))
    size = ((width + 3) // 4) * ((height + 3) // 4) * 16
    header = [124, 0x81007, height, width, size, 0, 1] + [0] * 11
    header += [32, 4, int.from_bytes(b'DX10', 'little'), 0, 0, 0, 0, 0, 0x1000, 0, 0, 0, 0]
    dds = b'DDS ' + struct.pack('<31I', *header) + struct.pack('<5I', 98, 3, 0, 1, 0)
    return Image.open(io.BytesIO(dds + blocks[:size])).convert('RGBA')


def runtime_surface_paths(asset_root, world):
    worlds = sorted(path.name for path in (asset_root / 'worlds').iterdir() if path.is_dir())
    packages = [Path('worlds') / world, Path('engine')]
    packages += [Path('worlds') / name for name in worlds if name != world]
    paths = {}
    for package in packages:
        for path in sorted((asset_root / package / 'textures_x4').glob('*.oytex')):
            paths.setdefault(path.stem.lower(), path)
    return paths


def runtime_terrain_albedo(asset_root, world, map_name, heights, size, dependency):
    """Diffuse bounce colour from mounted terrain layers, weights and slope settings.

    This exports the large-scale diffuse material. View-dependent specular, normals,
    anti-tiling and animated foliage remain runtime effects, outside the light bake.
    Rows follow the native north-to-south map convention.
    """
    import numpy as np
    from PIL import Image
    import yaml

    folder = asset_root / 'worlds' / world / 'terrain_materials'
    config_path = folder / (Path(map_name).stem + '.yml')
    dependency(config_path)
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    maps = []
    for name in config['weights']:
        path = folder / name
        dependency(path)
        maps.append(np.asarray(Image.open(path).convert('RGBA').resize((size, size)), dtype=np.float32) / 255)
    weights = np.concatenate(maps, axis=2)
    count = config['weighted_layers']
    weights[:, :, count:] = 0
    axis = (np.arange(size, dtype=np.float32) + .5) / size * 65024
    x, y = np.meshgrid(axis - 32768, axis - 32768)
    if 'slope' in config:
        height = np.asarray(heights, dtype=np.float32).reshape(128, 128) * 32
        dy, dx = np.gradient(height, 512)
        up = 1 / np.sqrt(1 + dx * dx + dy * dy)
        up = np.asarray(Image.fromarray(up).resize((size, size)))
        slope = config['slope']
        steep = np.clip((1 - up - slope['start']) / (slope['end'] - slope['start']), 0, 1)
        steep = steep * steep * (3 - 2 * steep)
        weights *= (1 - steep[:, :, None])
        weights[:, :, slope['layer']] += steep
    colour = np.zeros((size, size, 3), dtype=np.float32)
    for index, layer in enumerate(config['layers']):
        if index >= weights.shape[2] or not weights[:, :, index].any():
            continue
        path = asset_root / 'engine/terrain_materials' / layer['library'] / 'albedo_height.oytex'
        dependency(path)
        pixels = np.asarray(read_cooked_surface(path), dtype=np.float32) / 255
        height, width = pixels.shape[:2]
        u = np.floor(np.mod(x / layer['repeat'], 1) * width).astype(int)
        v = np.floor(np.mod(y / layer['repeat'], 1) * height).astype(int)
        samples = pixels[v, u]
        cavity = layer.get('cavity', 0)
        diffuse = samples[:, :, :3] * np.asarray(layer.get('tint', [1, 1, 1]))
        diffuse *= ((1 - cavity) + cavity * (.45 + 1.1 * samples[:, :, 3]))[:, :, None]
        colour += diffuse * weights[:, :, index:index + 1]
    colour /= np.maximum(weights.sum(axis=2, keepdims=True), 1e-6)
    return np.clip(colour, 0, 1)


def dependency_file(asset_root, name):
    """A bake dependency named relative to the runtime tree: a runtime file, or source art at the same relative path
    in assets_source beside it (the original world texture BMPs, which the runtime no longer carries). A model (.glb)
    is its source in assets_source when there is one: the runtime copy may be the cooked one."""
    path = asset_root / name
    source = asset_root.parent / 'assets_source' / name
    if name.endswith('.glb') and source.exists():
        return source
    return path if path.exists() else source


def texture_paths(asset_root, world, category):
    # AssetFileSystem::mountMergedWorldPackageRoots: active world, engine, sorted other worlds. The original texture
    # and terrain BMPs are source art in assets_source, under each package's same relative path.
    source_root = asset_root.parent / 'assets_source'
    worlds = sorted(path.name for path in (asset_root / 'worlds').iterdir() if path.is_dir())
    packages = [Path('worlds') / world, Path('engine')] + [Path('worlds') / name for name in worlds if name != world]
    roots = [root / package / category for package in packages for root in (asset_root, source_root)]
    if category == 'sprites':
        # Approved non-creature BMPs moved here; baked shadows retain their native-source provenance.
        roots.append(asset_root / '_legacy/sprites_original')
    paths = {}
    for root in roots:
        for path in sorted(root.glob('*.bmp')):
            paths.setdefault(path.stem.lower(), path)
    return paths


def bake_texture_paths(asset_root, world):
    textures = texture_paths(asset_root, world, 'textures')
    terrain = texture_paths(asset_root, world, 'terrain')
    # Terrain's native path falls back to textures; bmodels may use terrain liquid materials.
    return dict(terrain, **textures), dict(textures, **terrain)
