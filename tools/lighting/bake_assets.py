"""Native bake texture lookup using the runtime's merged development-package order."""


def texture_paths(asset_root, world, category):
    # AssetFileSystem::mountMergedWorldPackageRoots: active world, engine, sorted other worlds.
    active = asset_root / 'worlds' / world / category
    roots = [active, asset_root / 'engine' / category]
    roots.extend(path for path in sorted((asset_root / 'worlds').glob('*/' + category)) if path != active)
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
