#!/usr/bin/env python3
"""Cook the surface material maps of BLV and BModel face textures (devdocs/SURFACE_MATERIALS_PLAN.md).

Authored per texture, beside the accepted 4x master in assets_source (written by level_generation/surface_materials/
mat.py, never by hand):

  assets_source/worlds/<w>/surface_materials/<stem>_h.png   16-bit grey height: white raised, black recessed
  assets_source/worlds/<w>/surface_materials/<stem>_m.png   material classes as flat key colours (tools/cook/
                                                            surface_materials.yml)
  assets_source/worlds/<w>/surface_materials/textures.yml   per texture: wrap axes, optional depth and
                                                            painted_shading

Cooked beside the colour texture's tier, one pair per texture, both BC7 at half the colour texture's size
(MAP_REDUCTION) with the full mip chain below it; the runtime samples them with the colour texture's coordinates:

  assets_dev/worlds/<w>/surface_materials_x4/<stem>_n.oytex  r, g: tangent-space normal x, y (+x along +u, +y up the
                                                             image); b: glow (0 none, (0, 0.45] at night, [0.55, 1]
                                                             always); a: 1
  assets_dev/worlds/<w>/surface_materials_x4/<stem>_d.oytex  r: ambient occlusion, g: roughness, b: metal, a: height
                                                             (1 at the face plane, MAX_DEPTH world units at 0)

The normals and occlusion come from the height map in world units (one native texel is one world unit), wrapping on
the axes the texture repeats on its faces; roughness, metal, relief strength and glow come from the classes, the
roughness varied by the colour texture's fine brightness detail. painted_shading (0-1) weakens relief and occlusion on
art whose relief is already painted with shading.

  tools/surface_materials.py cook [--world W] [--only 'mm6/th*'] [--force] [--plan]
  tools/surface_materials.py verify [--world W]
  tools/surface_materials.py preview mm6/thlgdr OUT.png     maps and lit renders of one texture, for review

tools/cook_surface_textures.py runs the desktop cook and verify after its own, so the build's incremental cook
(target openyamm_cook_surface_textures) keeps these current. Receipts: assets_source/.cook-cache/surface_materials/.
"""
import argparse
import fcntl
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage
import yaml

ROOT = Path(__file__).resolve().parent.parent
CLASSES = ROOT / 'tools/cook/surface_materials.yml'
WORLDS = ('mm6', 'mm7', 'mm8')
SOURCE_TIER = 'textures_x4'
OUTPUT_TIER = 'surface_materials_x4'
# Master texels per native texel (world unit) in the x4 tier.
TIER_SCALE = 4
# game/shaders/surface_material.sh SURFACE_MAX_DEPTH: the deepest recess the height channel encodes.
MAX_DEPTH = 8.0
# Bump when the maps computed from the same inputs change.
COOK_REVISION = 7
# The cooked maps are this much smaller than the colour texture on each axis: half the size carries nearly all of the
# relief a face shows and costs a quarter of the disk and video memory (full size: 1.7 times the colour texture on
# disk, 164 MB of video memory in New Sorpigal).
MAP_REDUCTION = 2
# Texels over which the relief flattens toward an edge the texture does not tile across (build_maps).
EDGE_TEXELS = 8
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load_classes(path=CLASSES):
    classes = []
    for name, entry in yaml.safe_load(path.read_text())['classes'].items():
        classes.append({'name': name, 'key': tuple(entry['key']), 'describe': entry['describe'],
                        'roughness': tuple(entry['roughness']), 'gloss': bool(entry.get('gloss', False)),
                        'metal': float(entry['metal']), 'normal': float(entry['normal']), 'ao': float(entry['ao']),
                        'depth': float(entry['depth']), 'glow': entry.get('glow', 'none')})
    keys = [entry['key'] for entry in classes]
    if len(set(keys)) != len(keys):
        raise SystemExit(f'{path}: two classes share a key colour')
    return classes


def class_indices(rgb, classes):
    """Index of every texel's class; a colour that is no class key is an error (maps are snapped when accepted)."""
    packed = (rgb[..., 0].astype(np.int32) << 16) | (rgb[..., 1].astype(np.int32) << 8) | rgb[..., 2]
    result = np.full(packed.shape, -1, dtype=np.int32)
    for index, entry in enumerate(classes):
        r, g, b = entry['key']
        result[packed == ((r << 16) | (g << 8) | b)] = index
    if (result < 0).any():
        raise ValueError(f'{int((result < 0).sum())} texels are no class key colour')
    return result


def blur(image, sigma, modes):
    return ndimage.gaussian_filter(image, sigma, mode=modes) if sigma > 0 else image


def axis_modes(wrap):
    """Blur and gradient edge modes (rows, columns): rows are v, columns u."""
    return ['wrap' if 'v' in wrap else 'nearest', 'wrap' if 'u' in wrap else 'nearest']


def gradient(image, axis, mode):
    if mode == 'wrap':
        return (np.roll(image, -1, axis) - np.roll(image, 1, axis)) * 0.5
    return np.gradient(image, axis=axis)


def normalized_height(height):
    low, high = np.percentile(height, [0.5, 99.5])
    if high - low < 0.02:
        return np.ones_like(height)
    return np.clip((height - low) / (high - low), 0.0, 1.0)


def build_maps(master, height, classes_index, classes, settings):
    """(normal RGBA8, detail RGBA8) from the master (RGBA8), the height (float 0-1) and class indices."""
    modes = axis_modes(settings.get('wrap', ''))
    texel = 1.0 / TIER_SCALE
    count = len(classes)

    def class_property(values, sigma=0.7):
        # Per-texel property of the class, softened across class edges.
        return blur(np.asarray(values, dtype=np.float32)[classes_index], sigma, modes)

    weights = np.bincount(classes_index.ravel(), minlength=count) / classes_index.size
    depth = float(settings.get('depth', sum(w * entry['depth'] for w, entry in zip(weights, classes))))
    depth = min(max(depth, 0.1), MAX_DEPTH)
    painted = float(settings.get('painted_shading', 0.0))
    relief = normalized_height(height)
    world = relief * depth

    strength = class_property([entry['normal'] for entry in classes], 2.0) * (1.0 - 0.6 * painted)
    dzdx = gradient(world, 1, modes[1]) / texel * strength
    dzdrow = gradient(world, 0, modes[0]) / texel * strength
    # +x along +u (right); +y up the image, so the slope down the rows faces it.
    normal = np.stack([-dzdx, dzdrow, np.ones_like(world)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    # Faces sample with repeat even where the texture does not tile, so filtering and parallax rays at a face edge
    # reach the opposite edge: on those axes the relief flattens to the face plane over the outer texels, or a
    # tilted or recessed edge (a column's side) draws a dark line along the neighbouring face.
    flat = np.ones(world.shape, dtype=np.float32)
    ramp = np.minimum(np.arange(EDGE_TEXELS + 1, dtype=np.float32) / EDGE_TEXELS, 1.0)[1:]
    for axis, letter in ((1, 'u'), (0, 'v')):
        if letter not in settings.get('wrap', ''):
            size = world.shape[axis]
            edge = np.ones(size, dtype=np.float32)
            edge[:EDGE_TEXELS] = ramp - ramp[0]
            edge[size - EDGE_TEXELS:] = (ramp - ramp[0])[::-1]
            flat = flat * (edge[None, :] if axis == 1 else edge[:, None])
    normal[..., :2] *= flat[..., None]
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)

    occlusion = np.zeros_like(world)
    for radius in (0.5, 1.5, 4.0, 10.0):
        occlusion += np.clip((blur(world, radius / texel, modes) - world) / radius, 0.0, 1.0)
    occlusion_strength = class_property([entry['ao'] for entry in classes], 2.0) * (1.0 - 0.8 * painted)
    ao = np.clip(1.0 - 0.75 * occlusion * occlusion_strength, 0.15, 1.0)

    luminance = master[..., :3].astype(np.float32) @ LUMA / 255.0
    detail = luminance - blur(luminance, 3.0, modes)
    swing = np.tanh(detail / (2.0 * (detail.std() + 1e-4)))
    low = class_property([entry['roughness'][0] for entry in classes])
    high = class_property([entry['roughness'][1] for entry in classes])
    direction = class_property([-1.0 if entry['gloss'] else 1.0 for entry in classes])
    roughness = low + (high - low) * (0.5 + 0.5 * swing * direction)
    metal = class_property([entry['metal'] for entry in classes])

    # The shader gives every glowing texel its own hue (surfaceGlowColor): the mask is the class alone.
    night = class_property([1.0 if entry['glow'] == 'night' else 0.0 for entry in classes])
    always = class_property([1.0 if entry['glow'] == 'always' else 0.0 for entry in classes])
    # Night glow in (0, 0.45], always [0.55, 1] (surface_material.sh): the gap survives block compression.
    glow = np.where(always > 0.02, 0.55 + 0.45 * always, 0.45 * night)

    stored_height = np.clip(1.0 - (1.0 - relief * flat - (1.0 - flat)) * depth / MAX_DEPTH, 0.0, 1.0)
    to_byte = lambda image: np.clip(np.rint(image * 255.0), 0, 255).astype(np.uint8)
    normal_map = np.stack([to_byte(normal[..., 0] * 0.5 + 0.5), to_byte(normal[..., 1] * 0.5 + 0.5), to_byte(glow),
                           np.full(world.shape, 255, np.uint8)], axis=-1)
    detail_map = np.stack([to_byte(ao), to_byte(roughness), to_byte(metal), to_byte(stored_height)], axis=-1)
    return normal_map, detail_map


def read_height(path):
    with Image.open(path) as image:
        array = np.asarray(image.convert('I;16') if image.mode != 'I;16' else image).astype(np.float32)
    return array / 65535.0


def world_settings(sources_root, world):
    path = sources_root / 'worlds' / world / 'surface_materials' / 'textures.yml'
    return (yaml.safe_load(path.read_text()) or {}) if path.is_file() else {}


def texture_inputs(sources_root, world, stem):
    folder = sources_root / 'worlds' / world / 'surface_materials'
    return (sources_root / 'worlds' / world / SOURCE_TIER / f'{stem}.png', folder / f'{stem}_h.png',
            folder / f'{stem}_m.png')


def compute_maps(sources_root, world, stem, classes, settings):
    master_path, height_path, classes_path = texture_inputs(sources_root, world, stem)
    with Image.open(master_path) as image:
        master = np.asarray(image.convert('RGBA'))
    height = read_height(height_path)
    with Image.open(classes_path) as image:
        classes_rgb = np.asarray(image.convert('RGB'))
    if height.shape != master.shape[:2] or classes_rgb.shape[:2] != master.shape[:2]:
        raise ValueError(f'{world}/{stem}: height or class map size differs from the master {master.shape[1::-1]}')
    indices = class_indices(classes_rgb, classes)
    return master, height, indices, build_maps(master, height, indices, classes, settings)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def file_stat(path):
    stat = path.stat()
    return [stat.st_size, stat.st_mtime_ns]


def texture_receipt_inputs(sources_root, world, stem, classes_hash, settings, receipt):
    """The receipt inputs of a texture; unchanged sources are recognised by size and modification time, so the
    build's incremental cook reads no images."""
    sources = texture_inputs(sources_root, world, stem)
    stats = [file_stat(p) for p in sources]
    if receipt and receipt['inputs'].get('stats') == stats:
        hashes = receipt['inputs']['sources']
    else:
        hashes = [sha256(p) for p in sources]
    return {'revision': COOK_REVISION, 'classes': classes_hash, 'settings': settings, 'sources': hashes,
            'stats': stats}


def outputs_current(receipt, targets):
    if not all(t.is_file() for t in targets):
        return False
    if receipt.get('output_stats') == [file_stat(t) for t in targets]:
        return True
    return receipt['outputs'] == [sha256(t) for t in targets]


def same_inputs(left, right):
    keys = ('revision', 'classes', 'settings', 'sources')
    return all(left.get(key) == right.get(key) for key in keys)


def receipts_path(output_root):
    try:
        name = output_root.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        name = output_root.resolve().as_posix().lstrip('/')
    return ROOT / 'assets_source/.cook-cache/surface_materials' / (name.replace('/', '__') + '.json')


def authored(sources_root, world, only):
    """Stems of the world with both authored maps."""
    folder = sources_root / 'worlds' / world / 'surface_materials'
    if not folder.is_dir():
        return []
    stems = sorted(path.name[:-6] for path in folder.glob('*_h.png') if (folder / f'{path.name[:-6]}_m.png').is_file())
    return [stem for stem in stems if not only or any(fnmatch.fnmatch(f'{world}/{stem}', p) for p in only)]


def cook(sources_root, output_root, cooker, only, force, plan, worlds):
    classes = load_classes()
    classes_hash = sha256(CLASSES)
    path = receipts_path(output_root)
    receipts = {} if force or not path.is_file() else json.loads(path.read_text())
    pending, orphans, total = [], [], 0
    for world in worlds:
        if not (sources_root / 'worlds' / world).is_dir():
            continue
        settings = world_settings(sources_root, world)
        stems = authored(sources_root, world, only)
        output_dir = output_root / 'worlds' / world / OUTPUT_TIER
        for stem in stems:
            total += 1
            key = f'{world}/{stem}'
            receipt = receipts.get(key)
            inputs = texture_receipt_inputs(sources_root, world, stem, classes_hash, settings.get(stem, {}), receipt)
            targets = [output_dir / f'{stem}_n.oytex', output_dir / f'{stem}_d.oytex']
            if receipt and same_inputs(receipt['inputs'], inputs) and outputs_current(receipt, targets):
                receipt['inputs'] = inputs
                continue
            pending.append((world, stem, inputs, targets, settings.get(stem, {})))
        if not only and output_dir.is_dir():
            expected = {f'{stem}_{kind}.oytex' for stem in stems for kind in 'nd'}
            orphans += [p for p in sorted(output_dir.glob('*.oytex')) if p.name not in expected]
    print(f'surface materials: {total} textures, {len(pending)} to cook, {len(orphans)} orphaned cooked files',
          flush=True)
    if plan:
        for world, stem, *_ in pending[:20]:
            print(f'  cook {world}/{stem}')
        for orphan in orphans[:20]:
            print(f'  remove {orphan.relative_to(output_root)}')
        return
    for orphan in orphans:
        orphan.unlink()
        receipts.pop(f'{orphan.parent.parent.name}/{orphan.name[:-8]}', None)
    if pending and not cooker.is_file():
        raise SystemExit(f'Missing cooker {cooker}; cmake --build build --target openyamm_model_texture_cook')
    failures = 0
    for start in range(0, len(pending), 64):
        batch = pending[start:start + 64]
        with tempfile.TemporaryDirectory() as scratch:
            jobs = []
            for world, stem, inputs, targets, settings in batch:
                _, _, _, (normal, detail) = compute_maps(sources_root, world, stem, classes, settings)
                identity = {key: inputs[key] for key in ('revision', 'classes', 'settings', 'sources')}
                source_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
                for image, target in ((normal, targets[0]), (detail, targets[1])):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    intermediate = Path(scratch) / target.with_suffix('.png').name
                    Image.fromarray(image, 'RGBA').save(intermediate)
                    # Computed at the master's size, shipped at half of it (the cooker drops the top level).
                    max_size = str(max(image.shape[:2]) // MAP_REDUCTION)
                    jobs.append('\t'.join((str(intermediate), str(target), 'bc7', 'linear', '0', '1', max_size, '1',
                                           source_hash, 'model')))
            job_file = Path(scratch) / 'jobs.tsv'
            job_file.write_text('\n'.join(jobs) + '\n')
            result = subprocess.run([str(cooker), str(job_file)], text=True, capture_output=True)
        print(result.stderr, end='')
        done = {Path(line.split('\t')[1]) for line in result.stdout.splitlines() if line.startswith('cooked\t')}
        for world, stem, inputs, targets, _ in batch:
            if all(target in done for target in targets):
                receipts[f'{world}/{stem}'] = {'inputs': inputs, 'outputs': [sha256(t) for t in targets],
                                               'output_stats': [file_stat(t) for t in targets]}
            else:
                failures += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipts, indent=1, sort_keys=True) + '\n')
        print(f'  cooked {min(start + 64, len(pending))}/{len(pending)}', flush=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipts, indent=1, sort_keys=True) + '\n')
    if failures:
        raise SystemExit(f'{failures} of {len(pending)} surface material textures failed to cook')


def verify(sources_root, output_root, worlds):
    """Every authored texture has both cooked maps made from its current inputs, and none is orphaned."""
    classes_hash = sha256(CLASSES)
    path = receipts_path(output_root)
    receipts = json.loads(path.read_text()) if path.is_file() else {}
    problems = []
    for world in worlds:
        if not (sources_root / 'worlds' / world).is_dir():
            continue
        settings = world_settings(sources_root, world)
        stems = authored(sources_root, world, None)
        output_dir = output_root / 'worlds' / world / OUTPUT_TIER
        for stem in stems:
            targets = [output_dir / f'{stem}_n.oytex', output_dir / f'{stem}_d.oytex']
            if not all(t.is_file() for t in targets):
                problems.append(f'missing {world}/{stem} surface material maps')
                continue
            receipt = receipts.get(f'{world}/{stem}')
            inputs = texture_receipt_inputs(sources_root, world, stem, classes_hash, settings.get(stem, {}), None)
            if not receipt or not same_inputs(receipt['inputs'], inputs) \
                    or receipt['outputs'] != [sha256(t) for t in targets]:
                problems.append(f'stale {world}/{stem} surface material maps')
        if output_dir.is_dir():
            expected = {f'{stem}_{kind}.oytex' for stem in stems for kind in 'nd'}
            problems += [f'orphaned {p.relative_to(output_root)}' for p in sorted(output_dir.glob('*.oytex'))
                         if p.name not in expected]
    for problem in problems[:40]:
        print(problem)
    print(f'surface materials: {len(problems)} problems')
    return problems


def lit_preview(master, normal_map, detail_map, light):
    """A quick render under one directional light (towards the light, in tangent space) with occlusion and a GGX-ish
    highlight, for review sheets."""
    albedo = (master[..., :3].astype(np.float32) / 255.0) ** 2.2
    normal = np.stack([normal_map[..., 0] / 127.5 - 1.0, normal_map[..., 1] / 127.5 - 1.0, np.zeros(master.shape[:2])],
                      axis=-1)
    normal[..., 2] = np.sqrt(np.clip(1.0 - normal[..., 0] ** 2 - normal[..., 1] ** 2, 0.0, 1.0))
    ao = detail_map[..., 0] / 255.0
    roughness = detail_map[..., 1] / 255.0
    metal = detail_map[..., 2] / 255.0
    light = np.asarray(light, dtype=np.float32)
    light /= np.linalg.norm(light)
    nl = np.clip(normal @ light, 0.0, 1.0)
    half = light + np.array([0.0, 0.0, 1.0])
    half /= np.linalg.norm(half)
    nh = np.clip(normal @ half, 0.0, 1.0)
    alpha2 = np.maximum(roughness ** 4, 1e-4)
    highlight = alpha2 / (np.pi * (nh * nh * (alpha2 - 1.0) + 1.0) ** 2) * nl * 0.25
    f0 = 0.04 * (1.0 - metal[..., None]) + albedo * metal[..., None]
    color = albedo * (1.0 - 0.5 * metal[..., None]) * (0.25 * ao + 1.1 * nl)[..., None] \
        + f0 * highlight[..., None] * np.pi
    glow = normal_map[..., 2] / 255.0
    color += albedo * np.where(glow >= 0.5, np.clip((glow - 0.55) / 0.45, 0.0, 1.0), 0.0)[..., None] * 1.1
    return np.clip(color ** (1.0 / 2.2) * 255.0, 0, 255).astype(np.uint8)


def preview(sources_root, texture, output, classes=None):
    world, stem = texture.split('/')
    classes = classes or load_classes()
    settings = world_settings(sources_root, world).get(stem, {})
    master, height, indices, (normal, detail) = compute_maps(sources_root, world, stem, classes, settings)
    palette = np.array([entry['key'] for entry in classes], dtype=np.uint8)
    tiles = [master[..., :3], np.repeat((height * 255).astype(np.uint8)[..., None], 3, -1), palette[indices],
             normal[..., :3], np.repeat(detail[..., 0:1], 3, -1), np.repeat(detail[..., 1:2], 3, -1),
             lit_preview(master, normal, detail, (-0.8, 0.6, 0.35)),
             lit_preview(master, normal, detail, (0.9, -0.2, 0.3))]
    size = 384
    sheet = Image.new('RGB', (4 * size, 2 * size * master.shape[0] // master.shape[1]))
    cell_height = sheet.height // 2
    for index, tile in enumerate(tiles):
        image = Image.fromarray(np.ascontiguousarray(tile)).resize((size, cell_height), Image.LANCZOS)
        sheet.paste(image, ((index % 4) * size, (index // 4) * cell_height))
    sheet.save(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('cook', 'verify'):
        command = sub.add_parser(name)
        command.add_argument('--world', action='append')
        command.add_argument('--sources', type=Path, default=ROOT / 'assets_source')
        command.add_argument('--output', type=Path, default=ROOT / 'assets_dev')
        if name == 'cook':
            command.add_argument('--cooker', type=Path, default=ROOT / 'build/game/openyamm_model_texture_cook')
            command.add_argument('--only', action='append')
            command.add_argument('--force', action='store_true')
            command.add_argument('--plan', action='store_true')
    command = sub.add_parser('preview')
    command.add_argument('texture', help='<world>/<stem>')
    command.add_argument('output', type=Path)
    command.add_argument('--sources', type=Path, default=ROOT / 'assets_source')
    args = parser.parse_args()
    if args.command == 'preview':
        print(preview(args.sources, args.texture, args.output))
        return
    worlds = tuple(args.world or WORLDS)
    if args.command == 'verify':
        if verify(args.sources, args.output, worlds):
            raise SystemExit('run tools/surface_materials.py cook')
        return
    lock_path = receipts_path(args.output).with_suffix('.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cook(args.sources, args.output, args.cooker, args.only, args.force, args.plan, worlds)


if __name__ == '__main__':
    main()
