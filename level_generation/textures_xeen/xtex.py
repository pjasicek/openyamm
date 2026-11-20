#!/usr/bin/env python3
"""New face textures for the Xeen dungeons (XD-01 to XD-03): generation, finishing, checks and install.

Specs live in specs.yml. Images are made only by Codex image generation through `codex exec` workers, as the surface
texture pipeline does (level_generation/textures_x4/PLAYBOOK.md); everything else is deterministic here.

  xtex.py gen NAME... [--pass main|seam] [--parallel N] [--note TEXT]   one codex call per texture (new version)
  xtex.py finish NAME... [--version N]                                   raw return(s) -> finished/<name>.png (x4)
  xtex.py check NAME...                                                   sheets/check_<name>.png + stats
  xtex.py install --root ROOT [NAME...]                                   cook x4 to BC7 .oytex, x2 PNG, into ROOT

Folders: refs/ (reference images sent), prompts/ (exact prompts), raw/ (unchanged returns and worker logs; the
seam pass's inputs are refs/<name>_v<N>_rolled.png), finished/ (x4 masters, x2 and x1 reductions), sheets/ (checks).
"""
import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MASTERS = ROOT / 'level_generation/textures_x4/masters'
SPECS = HERE / 'specs.yml'
STATE = HERE / 'state.json'
SCALE = 4
BG = np.array([128, 128, 128], float)

STYLE = """Asset: {asset} for Might and Magic VI-VIII (a 1990s first-person fantasy RPG), in the remaster's high-resolution art.
The reference images are finished textures of the same place in the game: {family}.
Paint the new texture as if by the same artists for the same set: the same palette, saturation and contrast, the same
scale of detail (one texel is about one centimetre), the same hand-painted, slightly stylised realism (painted, not a
photograph), the same soft even lighting. Flat orthographic front view, even diffuse light, no perspective, no
vignette, no baked highlights, glare or cast shadows, no watermark or signature.
{body}"""

SIGN_FRAME = """Composition (Reference 1 is the layout guide: the board covers exactly its flat brown rectangle, at the same position,
size and proportions; the grey around it stays plain grey): on a perfectly flat plain mid-grey (#808080) background, one flat rectangular board seen exactly
straight on, its outline perfectly straight and axis-aligned, centred, {w} wide by {h} tall (aspect {ratio:.2f} to 1),
filling about 92 percent of the canvas {fill}. Nothing else on the grey: no shadow, no wall, no nails outside the board.
The board: {what}"""

PICTURE_FRAME = """Composition: full bleed, the subject fills the whole {canvas} canvas edge to edge. {what}
Every edge row and column is the material itself: no dark outline, frame line or vignette along the canvas edges."""

TILE_FRAME = """Composition: a seamless repeating texture that fills the whole {canvas} canvas edge to edge, features spread
evenly with nothing centred, no border, no frame, no darker or lighter edges. {what}"""

EDIT_FRAME = """This is an edit of Reference 1, a finished texture of the set. Keep Reference 1's framing, every rock, crack,
colour and its brightness exactly as they are, at the same positions; change only what is described here:
{what}
Output the whole picture at Reference 1's framing, no border, no vignette."""

CUTOUT_FRAME = """Composition: {what}
The magenta must be one perfectly flat colour #FF00FF with crisp edges against the iron, no gradient, no shadow on it."""

SEAM_PROMPT = """Use case: precise-object-edit.
Reference 1 is a texture for Might and Magic VI-VIII that will repeat seamlessly; it was rolled by half, so it shows a hard
straight seam along its vertical centre line and along its horizontal centre line where mismatched parts meet.
Repaint only a narrow band, about one tenth of the width, along those two centre lines, so the material continues
naturally and invisibly across them, with the same kind of features, colours, brightness and scale as everywhere
else. Keep every other part of the picture exactly as it is, at the same positions and the same framing.
No new objects, no frame, no vignette, flat even lighting."""

WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image(s) as reference images and the IMAGE PROMPT below.
   Output size: {size}.
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""


# ------------------------------------------------------------------------------------------------ helpers

def specs():
    return yaml.safe_load(SPECS.read_text())


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True) + '\n')
    tmp.replace(STATE)


def master(ref):
    world, name = ref.split('/')
    if world == 'sky':
        # Sky references (XD-04's roof): the HD masters of the outdoor skies, which have no face-texture master.
        return Image.open(ROOT / 'level_generation/lighting/sky_art/hd_masters' / f'{name}.png')
    return Image.open(MASTERS / world / f'{name}.png')


def srgb_to_linear(values):
    values = np.asarray(values, float) / 255.0
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(values):
    values = np.clip(values, 0, 1)
    return np.clip(np.where(values <= 0.0031308, values * 12.92, 1.055 * values ** (1 / 2.4) - 0.055) * 255, 0, 255)


LUMA = np.array([0.2126, 0.7152, 0.0722])


def linear_luma(rgb, mask=None):
    lin = srgb_to_linear(rgb[..., :3]) @ LUMA
    return float(lin[mask].mean() if mask is not None else lin.mean())


def to_srgb_luma(lin):
    return float(linear_to_srgb(np.array([lin]))[0])


def canvas_for(aspect):
    if aspect >= 1.25:
        return (1536, 1024), '1536x1024 (landscape)'
    if aspect <= 0.8:
        return (1024, 1536), '1024x1536 (portrait)'
    return (1024, 1024), '1024x1024 (square)'


def master_size(spec):
    return spec['size'][0] * SCALE, spec['size'][1] * SCALE


def art_aspect(spec):
    w, h = spec.get('art', spec['size'])
    return w / h


# ------------------------------------------------------------------------------------------------ references

def reference_sheet(refs, out, height=512):
    """One reference image per family texture, shown at a common height (tiled 2x where small)."""
    paths = []
    for index, ref in enumerate(refs):
        image = master(ref).convert('RGB')
        if image.width < 512 and image.height < 512:
            tiled = Image.new('RGB', (image.width * 2, image.height * 2))
            for dx in (0, 1):
                for dy in (0, 1):
                    tiled.paste(image, (dx * image.width, dy * image.height))
            image = tiled
        scale = min(1024 / image.width, 1024 / image.height, 1.0)
        image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
        path = out.parent / f'{out.stem}_{index + 1}.png'
        image.save(path)
        paths.append(path)
    return paths


def sign_guide(spec, path):
    """Layout reference of a sign: the board's rectangle at its exact aspect, flat brown on the grey."""
    aspect = art_aspect(spec)
    canvas, _ = canvas_for(aspect)
    width, height = canvas
    bw = round(min(width * 0.92, height * 0.92 * aspect))
    bh = round(bw / aspect)
    colour = tuple(int(v) for v in np.asarray(master(spec['refs'][0]).convert('RGB'), float).reshape(-1, 3).mean(0))
    guide = Image.new('RGB', canvas, (128, 128, 128))
    x0, y0 = (width - bw) // 2, (height - bh) // 2
    guide.paste(Image.new('RGB', (bw, bh), colour), (x0, y0))
    guide.save(path)
    return path


def base_image(spec):
    """The family master an edit paints into, cropped (texels) and at 4x."""
    image = master(spec['base']).convert('RGB')
    if 'crop' in spec:
        x0, y0, x1, y1 = spec['crop']
        image = image.crop((x0 * SCALE, y0 * SCALE, x1 * SCALE, y1 * SCALE))
    return image


def build_prompt(name, spec, dungeon_words):
    family = dungeon_words
    what = ' '.join(spec['what'].split())
    kind = spec['kind']
    aspect = art_aspect(spec)
    canvas, canvas_text = canvas_for(aspect if kind != 'edit' else 1.0)
    if kind == 'sign':
        w, h = spec.get('art', spec['size'])
        fill = 'width' if aspect * canvas[1] >= canvas[0] else 'height'
        body = SIGN_FRAME.format(w=w, h=h, ratio=aspect, fill=f'{fill}', what=what)
        asset = 'a painted sign texture'
    elif kind == 'picture':
        body = PICTURE_FRAME.format(canvas=canvas_text, what=what)
        asset = 'a flat single-picture surface texture'
    elif kind == 'tile':
        body = TILE_FRAME.format(canvas=canvas_text, what=what)
        asset = 'a flat repeating surface albedo texture'
    elif kind == 'cutout':
        body = CUTOUT_FRAME.format(what=what)
        asset = 'a flat cut-out surface texture (the magenta is made transparent)'
    else:
        body = EDIT_FRAME.format(what=what)
        asset = 'a flat surface albedo texture'
        canvas_text = '1024x1024 (square)'
    prompt = STYLE.format(asset=asset, family=family, body=body)
    return prompt, canvas_text


def references(name, spec, version):
    out = HERE / 'refs' / f'{name}_v{version}.png'
    paths = []
    if spec['kind'] == 'sign':
        paths.append(sign_guide(spec, out.parent / f'{out.stem}_guide.png'))
    if spec['kind'] == 'edit':
        base = base_image(spec)
        if base.size != (1024, 1024):
            # Edits are painted on a square canvas: the crop is shown centred on its own continuation.
            full = master(spec['base']).convert('RGB')
            base = full
        path = out.parent / f'{out.stem}_base.png'
        base.save(path)
        paths.append(path)
    paths += reference_sheet(spec['refs'], out)
    return paths


# ------------------------------------------------------------------------------------------------ generation

def run_worker(name, prompt, size_text, refs, target):
    log = target.with_suffix('.log')
    worker = WORKER.format(prompt=prompt, target=target, size=size_text)
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in refs:
        command += ['-i', str(ref)]
    started = time.time()
    with open(log, 'w') as stream:
        try:
            result = subprocess.run(command, input=worker, text=True, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=900)
            code = result.returncode
        except subprocess.TimeoutExpired:
            stream.write('\nxtex.py: worker timed out\n')
            code = -1
    return name, target, code == 0 and target.exists(), round(time.time() - started)


def cmd_gen(args):
    data = specs()
    state = load_state()
    jobs = []
    for name in args.names:
        spec = data['textures'][name]
        entry = state.setdefault(name, {'versions': []})
        if args.pass_ == 'main':
            version = len(entry['versions']) + 1
            dungeon = data['dungeons'][spec['dungeon']]
            words = dungeon['family_words']
            if name in ('xnbugtank', 'xntonics', 'xnheartsgn', 'xnfeedsgn', 'xnheartgt'):
                words = words + '; and ' + dungeon['cellar_words']
            prompt, size_text = build_prompt(name, spec, ' '.join(words.split()))
            if args.note:
                prompt += '\nCorrection for this attempt: ' + args.note
            refs = references(name, spec, version)
            target = HERE / 'raw' / f'{name}_v{version}.png'
            entry['versions'].append({'version': version, 'prompt': f'prompts/{name}_v{version}.txt',
                                      'refs': [str(p.relative_to(HERE)) for p in refs], 'raw': str(target.relative_to(HERE)),
                                      'note': args.note or ''})
        else:
            version = args.version or len(entry['versions'])
            rolled = HERE / 'refs' / f'{name}_v{version}_rolled.png'
            if not rolled.exists():
                sys.exit(f'{name}: run finish first (no {rolled.name})')
            prompt = SEAM_PROMPT
            size_text = '1024x1024 (square)' if Image.open(rolled).width == Image.open(rolled).height else (
                '1536x1024 (landscape)' if Image.open(rolled).width > Image.open(rolled).height else '1024x1536 (portrait)')
            refs = [rolled]
            target = HERE / 'raw' / f'{name}_v{version}_seam.png'
            entry['versions'][version - 1]['seam_raw'] = str(target.relative_to(HERE))
        (HERE / 'prompts' / f'{target.stem}.txt').write_text(prompt + '\n')
        jobs.append((name, prompt, size_text, refs, target))
    save_state(state)
    with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
        for name, target, ok, seconds in pool.map(lambda job: run_worker(*job), jobs):
            print(f'{name}: {"ok" if ok else "FAILED"} {seconds}s {target.name}', flush=True)


# ------------------------------------------------------------------------------------------------ finishing

def crop_to_aspect(image, aspect):
    w, h = image.size
    if w / h > aspect:
        nw = round(h * aspect)
        return image.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = round(w / aspect)
    return image.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))


def sign_box(rgb):
    """Bounding box of the board on the grey background (largest run of non-grey rows and columns)."""
    border = np.concatenate([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3), rgb[:, :8].reshape(-1, 3),
                             rgb[:, -8:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    diff = np.abs(rgb - bg).max(axis=2) > 26
    diff = ndimage.binary_opening(diff, iterations=2)
    labels, count = ndimage.label(ndimage.binary_fill_holes(diff))
    largest = 1 + int(np.argmax(ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))))
    board = labels == largest
    # Rows and columns mostly covered by the board (ignores stray marks sticking out of it).
    rows = board.sum(axis=1) > 0.5 * board.sum(axis=1).max()
    cols = board.sum(axis=0) > 0.5 * board.sum(axis=0).max()
    ys, xs = np.where(rows)[0], np.where(cols)[0]
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    inset_x, inset_y = max(2, (x1 - x0) // 120), max(2, (y1 - y0) // 120)
    return x0 + inset_x, y0 + inset_y, x1 - inset_x, y1 - inset_y


def tone(rgb, spec, mask=None):
    """One grey linear gain so the mean linear luma meets the spec's tone; hue and saturation are kept."""
    target = spec.get('tone')
    if not target:
        return rgb, 1.0
    if 'luma' in target:
        goal = float(srgb_to_linear(np.array([target['luma']]))[0])
    else:
        goal = np.mean([linear_luma(np.asarray(master(r).convert('RGB'), float)) for r in target['like']])
        goal *= target.get('factor', 1.0)
    current = linear_luma(rgb, mask)
    gain = goal / max(current, 1e-6)
    out = linear_to_srgb(srgb_to_linear(rgb[..., :3]) * gain)
    return out, gain


def register(a, b):
    """Integer shift (dx, dy) that moves b onto a (phase correlation of luma)."""
    la = ndimage.gaussian_filter(a @ LUMA, 2.0)
    lb = ndimage.gaussian_filter(b @ LUMA, 2.0)
    fa, fb = np.fft.fft2(la - la.mean()), np.fft.fft2(lb - lb.mean())
    product = fa * np.conj(fb)
    corr = np.fft.ifft2(product / (np.abs(product) + 1e-9)).real
    peak = np.unravel_index(np.argmax(corr), corr.shape)
    dy, dx = [p if p <= s // 2 else p - s for p, s in zip(peak, corr.shape)]
    return int(dx), int(dy)


def channel_gains(src, dst, mask):
    """Per-channel linear gains taking src's masked mean to dst's."""
    ls, ld = srgb_to_linear(src), srgb_to_linear(dst)
    return np.array([ld[..., c][mask].mean() / max(ls[..., c][mask].mean(), 1e-6) for c in range(3)])


def finish_edit(name, spec, raw):
    base = np.asarray(master(spec['base']).convert('RGB'), float)
    edit = np.asarray(raw.convert('RGB').resize(base.shape[1::-1], Image.LANCZOS), float)
    dx, dy = register(base, edit)
    edit = np.roll(edit, (dy, dx), axis=(0, 1))
    # Where the model left the rock alone: gain-match it there, then keep only what it really changed.
    rough = np.abs(ndimage.gaussian_filter(edit, (6, 6, 0)) - ndimage.gaussian_filter(base, (6, 6, 0))).sum(axis=2)
    calm = rough < np.percentile(rough, 60)
    gains = channel_gains(edit, base, calm)
    edit = linear_to_srgb(srgb_to_linear(edit) * gains)
    diff = np.abs(ndimage.gaussian_filter(edit, (3, 3, 0)) - ndimage.gaussian_filter(base, (3, 3, 0)))
    score = diff.max(axis=2)
    keep = score > spec.get('threshold', 38)
    keep = ndimage.binary_opening(keep, iterations=2)
    keep = ndimage.binary_dilation(keep, iterations=10)
    alpha = ndimage.gaussian_filter(keep.astype(float), 5)[..., None]
    out = base * (1 - alpha) + edit * alpha
    if 'view_auto' in spec:
        # The face's window (map units = texels of the family master): centred on what was painted, so the paint
        # shows large and the rock round it at the wall's own scale.
        vw, vh = [v * SCALE for v in spec['view_auto']]
        labels, count = ndimage.label(alpha[..., 0] > 0.5)
        sizes = ndimage.sum(np.ones_like(labels), labels, range(1, count + 1))
        # The painted thing: the components holding most of the change (small stray edits left out).
        big = np.isin(labels, 1 + np.nonzero(sizes >= 0.15 * sizes.max())[0])
        ys, xs = np.nonzero(big)
        cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
        x0 = int(np.clip(round(cx - vw / 2), 0, out.shape[1] - vw))
        y0 = int(np.clip(round(cy - vh / 2), 0, out.shape[0] - vh))
        out = out[y0:y0 + vh, x0:x0 + vw]
        spec = {**spec, 'crop_used': [x0 // SCALE, y0 // SCALE]}
    for key in ('crop', 'view'):
        if 'view_auto' in spec:
            break
        if key in spec:
            x0, y0, x1, y1 = [v * SCALE for v in spec[key]]
            out = out[y0:y1, x0:x1]
    info = {'view': spec.get('crop_used'), 'shift': [dx, dy], 'gains': [round(float(g), 3) for g in gains], 'changed': round(float(alpha.mean()), 3)}
    return out, info


def finish_tile_stage1(name, spec, raw, version):
    """Crop to aspect, size the master, roll by half (the seams to the middle) for the seam pass."""
    width, height = master_size(spec)
    image = crop_to_aspect(raw.convert('RGB'), width / height).resize((width, height), Image.LANCZOS)
    rgb = np.asarray(image, float)
    rolled = np.roll(rgb, (height // 2, width // 2), axis=(0, 1))
    canvas, _ = canvas_for(width / height)
    Image.fromarray(rolled.astype(np.uint8)).resize(canvas, Image.LANCZOS).save(
        HERE / 'refs' / f'{name}_v{version}_rolled.png')
    np.save(HERE / 'work' / f'{name}_v{version}_rolled.npy', rolled)
    return rolled


def finish_tile_stage2(name, spec, version, seam_raw):
    rolled = np.load(HERE / 'work' / f'{name}_v{version}_rolled.npy')
    height, width = rolled.shape[:2]
    seam = np.asarray(seam_raw.convert('RGB').resize((width, height), Image.LANCZOS), float)
    dx, dy = register(rolled, seam)
    seam = np.roll(seam, (dy, dx), axis=(0, 1))
    band = np.zeros((height, width), bool)
    bw, bh = max(8, width // 14), max(8, height // 14)
    band[:, width // 2 - bw:width // 2 + bw] = True
    band[height // 2 - bh:height // 2 + bh, :] = True
    ring = ndimage.binary_dilation(band, iterations=max(bw, bh)) & ~band
    gains = channel_gains(seam, rolled, ring)
    seam = linear_to_srgb(srgb_to_linear(seam) * gains)
    alpha = ndimage.gaussian_filter(band.astype(float), max(bw, bh) / 3)
    alpha = np.clip(alpha * 1.6, 0, 1)
    # Never let the patch reach the tile's own edges (they are the untouched, continuous interior).
    edge = np.ones((height, width))
    margin = max(bw, bh)
    ramp = np.clip(np.minimum.reduce([np.arange(width)[None, :].repeat(height, 0),
                                      np.arange(width)[::-1][None, :].repeat(height, 0),
                                      np.arange(height)[:, None].repeat(width, 1),
                                      np.arange(height)[::-1][:, None].repeat(width, 1)]) / margin, 0, 1)
    alpha = (alpha * ramp * edge)[..., None]
    out = rolled * (1 - alpha) + seam * alpha
    return out, {'seam_shift': [dx, dy], 'seam_gains': [round(float(g), 3) for g in gains]}


def finish_cutout(spec, raw):
    width, height = master_size(spec)
    image = crop_to_aspect(raw.convert('RGB'), art_aspect(spec)).resize((width, height), Image.LANCZOS)
    rgb = np.asarray(image, float)
    magenta = np.array([255, 0, 255], float)
    distance = np.sqrt(((rgb - magenta) ** 2).sum(axis=2))
    # Pixels clearly magenta are transparent; the fringe is opaque only when it is clearly not magenta.
    hue_m = (rgb[..., 0] > rgb[..., 1] + 60) & (rgb[..., 2] > rgb[..., 1] + 60)
    opaque = (distance > 140) & ~hue_m
    opaque = ndimage.binary_opening(opaque, iterations=1)
    # Fill transparent texels with the nearest opaque colour, so filtering never brings magenta in.
    _, (iy, ix) = ndimage.distance_transform_edt(~opaque, return_indices=True)
    filled = rgb[iy, ix]
    alpha = (opaque * 255).astype(np.uint8)
    return filled, alpha


def cmd_finish(args):
    data = specs()
    state = load_state()
    for name in args.names:
        spec = data['textures'][name]
        entry = state[name]
        version = args.version or len(entry['versions'])
        record = entry['versions'][version - 1]
        raw = Image.open(HERE / record['raw'])
        width, height = master_size(spec)
        alpha = None
        info = {'raw_size': list(raw.size)}
        kind = spec['kind']
        if kind == 'tile':
            if not record.get('seam_raw') or not (HERE / record['seam_raw']).exists():
                finish_tile_stage1(name, spec, raw, version)
                print(f'{name} v{version}: rolled for the seam pass (xtex.py gen {name} --pass seam)')
                save_state(state)
                continue
            rgb, more = finish_tile_stage2(name, spec, version, Image.open(HERE / record['seam_raw']))
            info.update(more)
        elif kind == 'edit':
            rgb, more = finish_edit(name, spec, raw)
            info.update(more)
            rgb = np.asarray(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((width, height),
                                                                                         Image.LANCZOS), float)
        elif kind == 'sign':
            full = np.asarray(raw.convert('RGB'), float)
            x0, y0, x1, y1 = sign_box(full)
            info['box'] = [int(x0), int(y0), int(x1), int(y1)]
            info['box_aspect'] = round((x1 - x0) / (y1 - y0), 3)
            crop = raw.convert('RGB').crop((x0, y0, x1, y1))
            rgb = np.asarray(crop.resize((width, height), Image.LANCZOS), float)
        elif kind == 'picture':
            image = crop_to_aspect(raw.convert('RGB'), art_aspect(spec)).resize((width, height), Image.LANCZOS)
            rgb = np.asarray(image, float)
        elif kind == 'cutout':
            rgb, alpha = finish_cutout(spec, raw)
        else:
            sys.exit(f'unknown kind {kind}')
        if kind != 'edit':
            mask = alpha > 0 if alpha is not None else None
            rgb, gain = tone(rgb, spec, mask)
            info['gain'] = round(float(gain), 3)
        rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
        image = Image.fromarray(rgb) if alpha is None else Image.fromarray(np.dstack([rgb, alpha]), 'RGBA')
        assert image.size == (width, height), (name, image.size)
        out = HERE / 'finished' / f'{name}.png'
        image.save(out)
        image.resize((width // 2, height // 2), Image.LANCZOS).save(HERE / 'finished' / f'{name}_x2.png')
        image.resize((width // 4, height // 4), Image.LANCZOS).save(HERE / 'finished' / f'{name}_x1.png')
        record['finished'] = info
        entry['chosen'] = version
        print(name, f'v{version}', info)
    save_state(state)


# ------------------------------------------------------------------------------------------------ checks

def stats(rgb, mask=None):
    pixels = rgb[..., :3][mask] if mask is not None else rgb[..., :3].reshape(-1, 3)
    lin = srgb_to_linear(pixels)
    luma = linear_to_srgb(lin @ LUMA)
    hsv = np.asarray(Image.fromarray(pixels.reshape(1, -1, 3).astype(np.uint8)).convert('HSV'), float)[0]
    return {'mean_rgb': [round(float(v)) for v in linear_to_srgb(lin.mean(axis=0))],
            'luma': round(to_srgb_luma(float((lin @ LUMA).mean())), 1),
            'luma_p5_p50_p95': [round(float(np.percentile(luma, q))) for q in (5, 50, 95)],
            'sat': round(float(hsv[:, 1].mean()), 1)}


def seam_ratio(rgb, axis):
    luma = rgb[..., :3] @ LUMA
    if axis == 'v':
        luma = luma.T
    interior = np.abs(np.diff(luma, axis=1)).mean()
    boundary = np.abs(luma[:, 0] - luma[:, -1]).mean()
    return round(float(boundary / max(interior, 1e-6)), 2)


def cmd_check(args):
    data = specs()
    report = {}
    for name in args.names:
        spec = data['textures'][name]
        image = Image.open(HERE / 'finished' / f'{name}.png')
        rgba = np.asarray(image.convert('RGBA'), float)
        mask = rgba[..., 3] > 0
        info = {'size_x4': list(image.size), 'logical': [image.width // SCALE, image.height // SCALE],
                'pow2': all((v & (v - 1)) == 0 for v in (image.width // SCALE, image.height // SCALE)),
                'stats': stats(rgba, mask)}
        info['seam_u'] = seam_ratio(rgba, 'u')
        info['seam_v'] = seam_ratio(rgba, 'v')
        family = spec.get('tone', {}).get('like') or spec.get('refs', [])
        if spec['kind'] == 'edit':
            family = [spec['base']] + spec['refs']
        info['family'] = {ref: stats(np.asarray(master(ref).convert('RGB'), float)) for ref in family}
        report[name] = info
        # Sheet: the texture (as the face shows it), 3x3 repeat, the family beside it, luma histograms.
        cell = 360
        shown = image.convert('RGB')
        aspect = art_aspect(spec)
        shown_view = shown.resize((cell, max(1, round(cell / aspect))) if aspect >= 1
                                  else (max(1, round(cell * aspect)), cell), Image.LANCZOS)
        tile = Image.new('RGB', (shown.width * 3, shown.height * 3))
        for dx in range(3):
            for dy in range(3):
                tile.paste(shown, (dx * shown.width, dy * shown.height))
        tile.thumbnail((cell * 2, cell * 2), Image.LANCZOS)
        fams = []
        for ref in family[:4]:
            m = master(ref).convert('RGB')
            m.thumbnail((cell // 2 * 2 // 2, cell // 2 * 2 // 2), Image.LANCZOS)
            fams.append((ref, m))
        sheet = Image.new('RGB', (cell + 2 * cell + 20 + 200, 2 * cell + 120), (36, 36, 36))
        draw = ImageDraw.Draw(sheet)
        sheet.paste(shown_view, (0, 20))
        draw.text((4, 4), f'{name} as seen ({spec.get("art", spec["size"])})', fill=(255, 255, 0))
        sheet.paste(tile, (cell + 10, 20))
        draw.text((cell + 14, 4), '3x3 repeat', fill=(255, 255, 0))
        y = 20
        for ref, m in fams:
            sheet.paste(m, (3 * cell + 30, y))
            draw.text((3 * cell + 30, y + m.height), ref, fill=(200, 200, 200))
            y += m.height + 16
        # Luma histograms: texture (yellow) over each family texture (grey).
        hx, hy, hw, hh = 4, cell + 40, cell, 70
        def histogram(rgb, colour, msk=None):
            values = (rgb[..., :3][msk] if msk is not None else rgb[..., :3].reshape(-1, 3)) @ LUMA
            counts, _ = np.histogram(values, bins=64, range=(0, 255))
            counts = counts / max(counts.max(), 1)
            points = [(hx + i * hw / 64, hy + hh - c * hh) for i, c in enumerate(counts)]
            draw.line(points, fill=colour, width=2)
        for ref, _ in fams:
            histogram(np.asarray(master(ref).convert('RGB'), float), (140, 140, 140))
        histogram(rgba, (255, 220, 0), mask)
        draw.text((hx, hy + hh + 4), 'luma histogram: texture (yellow), family (grey)', fill=(200, 200, 200))
        text = json.dumps({k: info[k] for k in ('logical', 'pow2', 'seam_u', 'seam_v')}) + '\n' + \
            'tex ' + json.dumps(info['stats']) + '\n' + '\n'.join(f'{k[:14]:14} {json.dumps(v)}' for k, v in
                                                               info['family'].items())
        draw.text((hx + hw + 20, hy), text, fill=(230, 230, 230))
        sheet.save(HERE / 'sheets' / f'check_{name}.png')
        print(name, json.dumps({k: info[k] for k in ('logical', 'pow2', 'seam_u', 'seam_v', 'stats')}))
    out = HERE / 'sheets' / 'checks.json'
    old = json.loads(out.read_text()) if out.exists() else {}
    old.update(report)
    out.write_text(json.dumps(old, indent=1) + '\n')


# ------------------------------------------------------------------------------------------------ install

def cmd_install(args):
    sys.path.insert(0, str(ROOT / 'tools'))
    import cook_surface_textures as cook
    cooker = ROOT / 'build/game/openyamm_model_texture_cook'
    data = specs()
    names = args.names or [n for n in data['textures'] if (HERE / 'finished' / f'{n}.png').exists()]
    work = HERE / 'work' / 'cook'
    (work / 'cooked').mkdir(parents=True, exist_ok=True)
    jobs = []
    for name in names:
        source = HERE / 'finished' / f'{name}.png'
        target = work / 'cooked' / f'{name}.oytex'
        if target.exists() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            continue
        jobs.append('\t'.join((str(source), str(target), 'bc7', *cook.job_settings(cook.FULL_SIZE),
                               cook.sha256(source)[:16], 'surface')) + '\n')
    if jobs:
        (work / 'jobs.tsv').write_text(''.join(jobs))
        result = subprocess.run([str(cooker), str(work / 'jobs.tsv')], text=True, capture_output=True)
        cooked = sum(line.startswith('cooked\t') for line in result.stdout.splitlines())
        if cooked != len(jobs):
            sys.exit(f'cooked {cooked} of {len(jobs)}\n{result.stdout}\n{result.stderr}')
    root = Path(args.root).resolve()
    for name in names:
        for folder, source, filename in (('textures_x4', work / 'cooked' / f'{name}.oytex', f'{name}.oytex'),
                                         ('textures_x2', HERE / 'finished' / f'{name}_x2.png', f'{name}.png')):
            directory = root / 'worlds' / args.world / folder
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / filename
            bytes_ = source.read_bytes()
            if target.exists() and target.read_bytes() == bytes_:
                continue
            # A new file renamed over the old name: never written through a hard link, never seen half-written.
            temporary = directory / f'.{filename}.tmp'
            temporary.write_bytes(bytes_)
            temporary.replace(target)
        print('installed', name, '->', root / 'worlds' / args.world)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    gen = sub.add_parser('gen')
    gen.add_argument('names', nargs='+')
    gen.add_argument('--pass', dest='pass_', choices=['main', 'seam'], default='main')
    gen.add_argument('--parallel', type=int, default=8)
    gen.add_argument('--note', default='')
    gen.add_argument('--version', type=int)
    finish = sub.add_parser('finish')
    finish.add_argument('names', nargs='+')
    finish.add_argument('--version', type=int)
    check = sub.add_parser('check')
    check.add_argument('names', nargs='+')
    install = sub.add_parser('install')
    install.add_argument('names', nargs='*')
    install.add_argument('--root', required=True)
    install.add_argument('--world', default='mm7')
    args = parser.parse_args()
    {'gen': cmd_gen, 'finish': cmd_finish, 'check': cmd_check, 'install': cmd_install}[args.command](args)


if __name__ == '__main__':
    main()
