"""Native bake texture lookup using the runtime's merged development-package order."""
from pathlib import Path
import re


def source_roots(asset_root, extra_sources=()):
    """Where source art lives beside a runtime tree: its sibling assets_source, then any extra roots (a staged
    world's gathered sources, such as the Hesper stage's sources/)."""
    return [asset_root.parent / 'assets_source'] + [Path(root) for root in extra_sources]


def native_texture_file(asset_root, name):
    """The extracted original MM6-MM8 texture BMP (assets_source/textures/native_mm6_mm8/<world>/textures/) that a
    package texture path (worlds/mm7/textures/sgdock.bmp) stands for, when the world's own source folder has no copy.
    None for any other name."""
    parts = Path(name).parts
    if len(parts) != 4 or parts[0] != 'worlds' or parts[2] != 'textures':
        return None
    return asset_root.parent / 'assets_source' / 'textures' / 'native_mm6_mm8' / parts[1] / 'textures' / parts[3]


def dependency_name(asset_root, path, extra_sources=()):
    """How a bake records a file it read: relative to the runtime tree; source art in assets_source and the extra
    roots keeps the same relative path, and a native archive texture its package path (worlds/<world>/textures/...).
    Always with forward slashes, so a bake made on Windows records the same names as one made elsewhere."""
    archive = asset_root.parent / 'assets_source' / 'textures' / 'native_mm6_mm8'
    if path.is_relative_to(archive):
        parts = path.relative_to(archive).parts
        if len(parts) == 3 and parts[1] == 'textures':
            return (Path('worlds') / parts[0] / 'textures' / parts[2]).as_posix()
    base = next((root for root in source_roots(asset_root, extra_sources) if path.is_relative_to(root)), asset_root)
    return path.relative_to(base).as_posix()


def dependency_file(asset_root, name, extra_sources=()):
    """A bake dependency named relative to the runtime tree: a runtime file, or source art at the same relative path
    in assets_source beside it (the original world texture BMPs, which the runtime no longer carries). A model (.glb)
    is its source in assets_source when there is one: the runtime copy may be the cooked one."""
    path = asset_root / name
    sources = [root / name for root in source_roots(asset_root, extra_sources)]
    if name.endswith('.glb'):
        for source in sources:
            if source.exists():
                return source
    if path.exists():
        return path
    native = native_texture_file(asset_root, name)
    if native is not None:
        sources.append(native)
    return next((source for source in sources if source.exists()), sources[0])


def texture_paths(asset_root, world, category, extra_sources=(), pattern='*.bmp'):
    # AssetFileSystem::mountMergedWorldPackageRoots: active world, engine, sorted other worlds. The original texture
    # and terrain BMPs are source art in assets_source, under each package's same relative path.
    worlds = sorted(path.name for path in (asset_root / 'worlds').iterdir() if path.is_dir())
    packages = [Path('worlds') / world, Path('engine')] + [Path('worlds') / name for name in worlds if name != world]
    roots = [root / package / category for package in packages
             for root in [asset_root] + source_roots(asset_root, extra_sources)]
    if category == 'textures':
        # The extracted original BMPs, last: a world texture its package's source folder lacks (MM7's sgdock.bmp).
        archive = asset_root.parent / 'assets_source' / 'textures' / 'native_mm6_mm8'
        roots += [archive / package.name / 'textures' for package in packages if package.parts[0] == 'worlds']
    if category == 'sprites':
        # Approved non-creature BMPs moved here; baked shadows retain their native-source provenance.
        roots.append(asset_root / '_legacy/sprites_original')
    paths = {}
    for root in roots:
        for path in sorted(root.glob(pattern)):
            paths.setdefault(path.stem.lower(), path)
    return paths


def bake_texture_paths(asset_root, world, extra_sources=()):
    textures = texture_paths(asset_root, world, 'textures', extra_sources)
    terrain = texture_paths(asset_root, world, 'terrain', extra_sources)
    # Faces of a world without native BMPs (Hesper, Xeen's new textures) resolve to their 4x PNG masters (textures_x4
    # sources, a quarter of their size in texels), with or without --sources; a native BMP of the same name wins.
    masters = texture_paths(asset_root, world, 'textures_x4', extra_sources, '*.png')
    textures = dict(masters, **textures)
    # Terrain's native path falls back to textures; bmodels may use terrain liquid materials.
    return dict(terrain, **textures), dict(textures, **terrain)


def texture_logical_scale(path):
    """Texels of a source image per logical texel: 4 for a textures_x4 master, 1 for the native BMPs."""
    return 4 if 'textures_x4' in Path(path).parts else 1


def liquid_face_colours(assets, world):
    """Texture name -> linear colour of the liquids.yml entries that apply to faces of `world` (a small reader of the
    file's flow lists: color, applies_to, worlds, texture_names)."""
    path = assets / 'engine' / 'liquids' / 'liquids.yml'
    colours, entries = {}, []
    if not path.is_file():
        return colours, path
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('  - id:'):
            entries.append({})
            continue
        match = re.match(r'\s+(color|applies_to|worlds|texture_names):\s*\[(.*)\]', line)
        if match and entries:
            entries[-1][match.group(1)] = [item.strip() for item in match.group(2).split(',') if item.strip()]
    for entry in entries:
        if 'face' not in entry.get('applies_to', []) or len(entry.get('color', [])) != 3:
            continue
        if 'worlds' in entry and world not in entry['worlds']:
            continue
        srgb = [float(value) / 255 for value in entry['color']]
        linear = tuple(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in srgb)
        for name in entry.get('texture_names', []):
            colours.setdefault(name.lower(), linear)
    return colours, path
