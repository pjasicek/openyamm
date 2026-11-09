#!/usr/bin/env python3
"""Generate the surface material maps of MM6-MM8 face textures (devdocs/SURFACE_MATERIALS_PLAN.md, README.md here).

Per texture, two Codex image-generation calls on its accepted 4x master (assets_source/worlds/<w>/textures_x4):
a height map and a material class map (tools/cook/surface_materials.yml). The returns are aligned to the master,
snapped (classes to the key colours along the master's edges; heights made seamless on the axes the texture repeats),
given their texture family's exact maps where the masters share pixels, checked, and installed into
assets_source/worlds/<w>/surface_materials/ for tools/surface_materials.py to cook.

  mat.py status [--world W]
  mat.py next --world W [--map M] [--names a,b] [--count N]   claim pending textures into a job (24 at most);
                                                               --redo --names a,b claims installed ones again
  mat.py gen [--world W] [--job ID] [--parallel N]             run the missing Codex workers of open jobs
  mat.py process JOB                                           candidates, checks and the review sheet
  mat.py accept JOB [NAME...]                                  install candidates (all checked ones by default)
  mat.py retry JOB NAME --kind height|classes [--note TEXT]    a new attempt of one map
  mat.py release JOB [NAME...]                                 back to pending
  mat.py auto --world W [--map M] [--jobs N]                   next, gen, process and accept, job after job
  mat.py relabel mm6/NAME FROM TO                              review fix: one class of an installed map to another

The texture inventory (wrap axes, relatives, duplicates, maps) is level_generation/textures_x4/inventory.json.
Exact duplicates follow their canonical texture and are installed with it.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import surface_materials  # noqa: E402

INVENTORY = ROOT / 'level_generation/textures_x4/inventory.json'
SOURCES = ROOT / 'assets_source'
LEDGER = HERE / 'ledger.jsonl'
JOBS = HERE / 'jobs'
JOB_SIZE = 24
KINDS = ('height', 'classes')
# Checks (process): heights that follow the master's brightness traced the colours, not the shape.
MAX_HEIGHT_LUMINANCE_CORRELATION = 0.9
MAX_OFF_PALETTE = 0.04
MAX_SHIFT_FRACTION = 0.01

HEIGHT_PROMPT = """Convert this texture into a DEPTH PASS (Z-depth / displacement map) of the very same surface, as a \
3D renderer outputs it: an unlit greyscale image where brightness encodes only distance from the wall plane. Keep \
exactly the same framing, composition and proportions: every brick, stone block, plank, ornament, frame, figure and \
edge in exactly the same place as in the reference, so the map overlays the texture pixel for pixel.
Brightness = height: white = most raised toward the viewer, black = deepest recess. There is NO light source: no \
highlights, no shadows, no bevel shading, no ambient occlusion, no light-from-the-top-left. A flat face is one even \
grey over its whole area, with the same value on its left and right, top and bottom edges. Raised edges get brighter \
only by how far they stand out, never by which side faces a light. Mortar joints, cracks and gaps: darker grey \
(recessed). Brick and stone faces: even light grey with faint undulation. Carved relief and sculpture: smooth \
gradients following their 3D form, brightest at the most protruding points. Wood planks: even mid-light grey, dark \
narrow gaps between them. Metal bands, studs, nails and frames: raised. Glass panes: flat, slightly recessed behind \
their frames.
No colour, no text, no texture copied from the colours: a dark brick is exactly as high as a light one.{repeat}"""

CLASSES_PROMPT = """Convert this texture into a flat MATERIAL SEGMENTATION MAP of the very same surface. Keep exactly \
the same framing, composition and proportions: every region must sit in exactly the same place as in the reference, \
so the map overlays the texture pixel for pixel.
Paint every pixel in exactly one of these flat colours, by what material it depicts (no shading, no gradients, no \
outlines, no texture, no anti-aliasing, no text):
{legend}
A window's glass is cyan wherever light would shine through it, including everything a stained-glass window depicts \
(figures, animals, buildings, sky, landscape, ornament), and tinted glass of any colour (amber, red, green) is cyan too; \
only its lead lines, bars and frame take other colours. Yellow is only for things that give light themselves.
Use only these colours.{repeat}"""

REPEAT_NOTE = ('\nThe reference shows {count} identical copies of one texture {direction}; treat each copy the same '
               'way and keep the copies identical.')

WORKER_PROMPT = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image as the reference image and the IMAGE PROMPT below.
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""


def now():
    return datetime.datetime.now().isoformat(timespec='seconds')


def load_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=1) + '\n')
    temporary.replace(path)


def append_events(events):
    with open(LEDGER, 'a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        for event in events:
            stream.write(json.dumps({'time': now(), **event}) + '\n')


def ledger_state():
    """{texture id: {'status': pending|claimed|accepted, 'job': id}} folded from the ledger."""
    state = {}
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            event = json.loads(line)
            record = state.setdefault(event['id'], {'status': 'pending'})
            if event['event'] == 'claim':
                record.update(status='claimed', job=event['job'])
            elif event['event'] == 'accept':
                record.update(status='accepted', job=event['job'])
            elif event['event'] == 'release':
                record.update(status='pending', job=None)
    return state


def inventory():
    """{id: entry} of in-scope textures with an installed master."""
    result = {}
    for entry in load_json(INVENTORY)['textures']:
        if entry.get('exclude'):
            continue
        result[entry['id']] = entry
    return result


def master_path(entry):
    return SOURCES / 'worlds' / entry['world'] / 'textures_x4' / f"{entry['name']}.png"


def installed(entry):
    folder = SOURCES / 'worlds' / entry['world'] / 'surface_materials'
    return (folder / f"{entry['name']}_h.png").is_file() and (folder / f"{entry['name']}_m.png").is_file()


def candidates_for(textures, state, world, map_name, names, redo=False):
    picked = []
    for texture_id, entry in sorted(textures.items(), key=lambda item: (-item[1].get('area', 0), item[0])):
        if entry['world'] != world or entry.get('canonical', texture_id) != texture_id:
            continue
        status = state.get(texture_id, {}).get('status', 'pending')
        if status == 'claimed' or (not redo and (status != 'pending' or installed(entry))):
            continue
        if not master_path(entry).is_file():
            continue
        if map_name and map_name not in entry.get('maps', []):
            continue
        if names and entry['name'] not in names:
            continue
        picked.append(texture_id)
    return picked


# --------------------------------------------------------------------------------------------------- references

def reference_layout(width, height):
    """How many copies the reference stacks to stay within 1:2-2:1 (imagegen keeps such aspects exactly), and along
    which axis ('rows': stacked vertically, for wide textures)."""
    aspect = width / height
    if aspect > 2.0:
        return int(np.ceil(aspect / 2.0)), 'rows'
    if aspect < 0.5:
        return int(np.ceil(1.0 / aspect / 2.0)), 'columns'
    return 1, None


def build_reference(entry, target):
    with Image.open(master_path(entry)) as image:
        master = image.convert('RGBA')
    count, axis = reference_layout(*master.size)
    width, height = master.size
    size = (width, height * count) if axis == 'rows' else (width * count, height)
    reference = Image.new('RGB', size, (0, 0, 0))
    flat = Image.new('RGB', master.size, (128, 128, 128))
    flat.paste(master, mask=master.getchannel('A'))
    for index in range(count):
        reference.paste(flat, (0, index * height) if axis == 'rows' else (index * width, 0))
    # Imagegen reads about 1.5 MP; larger references only cost upload time.
    scale = min(1.0, (1.6e6 / (size[0] * size[1])) ** 0.5)
    if scale < 1.0:
        reference = reference.resize((round(size[0] * scale), round(size[1] * scale)), Image.LANCZOS)
    reference.save(target)
    return count, axis


def prompt_for(kind, count, axis, classes):
    repeat = '' if count == 1 else REPEAT_NOTE.format(
        count=count, direction='stacked vertically' if axis == 'rows' else 'side by side')
    if kind == 'height':
        return HEIGHT_PROMPT.format(repeat=repeat)
    legend = '\n'.join(f"- {entry['name'].replace('_', ' ')} {tuple(entry['key'])}: {entry['describe']}"
                       for entry in classes)
    return CLASSES_PROMPT.format(legend=legend, repeat=repeat)


# --------------------------------------------------------------------------------------------------- jobs

def job_dir(job_id):
    return JOBS / job_id


def load_job(job_id):
    return load_json(job_dir(job_id) / 'job.json')


def save_job(job):
    write_json(job_dir(job['id']) / 'job.json', job)


def cmd_next(args):
    textures = inventory()
    state = ledger_state()
    names = set(args.names.split(',')) if args.names else None
    picked = candidates_for(textures, state, args.world, args.map, names, getattr(args, 'redo', False))
    picked = picked[:min(args.count, JOB_SIZE)]
    if not picked:
        print('nothing pending')
        return
    job_id = f"{args.world}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    folder = job_dir(job_id)
    for sub in ('refs', 'raw', 'candidates', 'review'):
        (folder / sub).mkdir(parents=True, exist_ok=True)
    requests = {}
    for texture_id in picked:
        entry = textures[texture_id]
        count, axis = build_reference(entry, folder / 'refs' / f"{entry['name']}.png")
        requests[texture_id] = {'name': entry['name'], 'copies': count, 'axis': axis,
                                'versions': {kind: 1 for kind in KINDS}, 'notes': {}}
    save_job({'id': job_id, 'world': args.world, 'created': now(), 'textures': picked, 'requests': requests})
    append_events([{'event': 'claim', 'id': texture_id, 'job': job_id} for texture_id in picked])
    print(f'{job_id}: {len(picked)} textures')


def raw_path(job_id, request, kind):
    return job_dir(job_id) / 'raw' / f"{request['name']}_{kind}_v{request['versions'][kind]}.png"


def run_worker(job_id, request, kind, classes):
    folder = job_dir(job_id)
    target = raw_path(job_id, request, kind)
    prompt = prompt_for(kind, request['copies'], request['axis'], classes)
    note = request['notes'].get(f"{kind}_v{request['versions'][kind]}")
    if note:
        prompt += '\nCorrection for this attempt: ' + note
    log = target.with_suffix('.log')
    started = time.time()
    with open(log, 'w') as stream:
        try:
            process = subprocess.run(
                ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(folder), '--skip-git-repo-check',
                 '-i', str(folder / 'refs' / f"{request['name']}.png")],
                input=WORKER_PROMPT.format(target=target, prompt=prompt), text=True, stdout=stream,
                stderr=subprocess.STDOUT, timeout=900)
            code = process.returncode
        except subprocess.TimeoutExpired:
            stream.write('\nmat.py: worker timed out after 900 s\n')
            code = -1
    return request['name'], kind, code == 0 and target.exists(), round(time.time() - started)


def open_jobs(state, world=None, only=None):
    jobs = []
    for path in sorted(JOBS.glob('*/job.json')):
        job = load_json(path)
        if (world and job['world'] != world) or (only and job['id'] != only):
            continue
        if any(state.get(t, {}).get('status') == 'claimed' and state[t].get('job') == job['id']
               for t in job['textures']):
            jobs.append(job)
    return jobs


def cmd_gen(args):
    classes = surface_materials.load_classes()
    state = ledger_state()
    work = []
    for job in open_jobs(state, args.world, args.job):
        for texture_id, request in job['requests'].items():
            if state.get(texture_id, {}).get('status') != 'claimed' or state[texture_id].get('job') != job['id']:
                continue
            for kind in KINDS:
                if not raw_path(job['id'], request, kind).exists():
                    work.append((job['id'], request, kind))
    print(f'{len(work)} workers', flush=True)
    failed = []
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [pool.submit(run_worker, job_id, request, kind, classes) for job_id, request, kind in work]
        for future in as_completed(futures):
            name, kind, ok, seconds = future.result()
            print(f"  {'ok' if ok else 'FAILED'} {name} {kind} ({seconds} s)", flush=True)
            if not ok:
                failed.append((name, kind))
    # One more round for the failures (a worker that hung or returned nothing).
    if failed and not args.no_retry:
        retry = [(job_id, request, kind) for job_id, request, kind in work
                 if (request['name'], kind) in failed and not raw_path(job_id, request, kind).exists()]
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            for future in as_completed([pool.submit(run_worker, j, r, k, classes) for j, r, k in retry]):
                name, kind, ok, seconds = future.result()
                print(f"  retry {'ok' if ok else 'FAILED'} {name} {kind} ({seconds} s)", flush=True)


# --------------------------------------------------------------------------------------------------- processing

def split_copies(array, count, axis):
    if count == 1:
        return [array]
    return np.split(array, count, axis=0 if axis == 'rows' else 1)


def returned(path, size, count, axis, resample):
    """The raw return resized to the stacked reference's full-resolution size, split into its copies."""
    width, height = size
    full = (width, height * count) if axis == 'rows' else (width * count, height) if axis else (width, height)
    with Image.open(path) as image:
        array = np.asarray(image.convert('RGB').resize(full, resample))
    return split_copies(array, count, axis)


def edges(gray):
    smooth = ndimage.gaussian_filter(gray.astype(np.float32), 1.5)
    return np.hypot(ndimage.sobel(smooth, 0), ndimage.sobel(smooth, 1))


def phase_shift(a, b):
    spectrum = np.fft.fft2(a - a.mean()) * np.conj(np.fft.fft2(b - b.mean()))
    spectrum /= np.abs(spectrum) + 1e-9
    correlation = np.fft.ifft2(spectrum).real
    y, x = np.unravel_index(np.argmax(correlation), correlation.shape)
    y = y - correlation.shape[0] if y > correlation.shape[0] // 2 else y
    x = x - correlation.shape[1] if x > correlation.shape[1] // 2 else x
    return int(y), int(x)


def seamless(height, wrap, band=24):
    """Removes the step where the map meets its own opposite edge on the axes the texture repeats."""
    result = height.copy()
    for axis, letter in ((1, 'u'), (0, 'v')):
        if letter not in wrap:
            continue
        size = result.shape[axis]
        band = min(band, size // 4)
        first = np.take(result, [0], axis=axis)
        last = np.take(result, [size - 1], axis=axis)
        step = ndimage.gaussian_filter1d((last - first).squeeze(axis), 4.0, mode='wrap')
        ramp = np.zeros(size, dtype=np.float32)
        ramp[:band] = 0.5 * (1.0 - np.arange(band) / band)
        ramp[size - band:] = -0.5 * (np.arange(band) + 1) / band
        shape = [1, 1]
        shape[axis] = size
        result += np.expand_dims(step, axis) * ramp.reshape(shape)
    return result


def guided(guide, source, radius, epsilon):
    """He et al.'s guided filter: source smoothed while following the guide's edges."""
    box = lambda image: ndimage.uniform_filter(image, 2 * radius + 1, mode='nearest')
    mean_guide, mean_source = box(guide), box(source)
    variance = box(guide * guide) - mean_guide ** 2
    covariance = box(guide * source) - mean_guide * mean_source
    a = covariance / (variance + epsilon)
    b = mean_source - a * mean_guide
    return box(a) * guide + box(b)


def snap_classes(copies, master, classes):
    """Class indices from the returned copies: every texel's nearest key colour, voted across copies, with the class
    edges moved onto the master's edges and specks merged. Also the share of texels far from every key."""
    keys = np.array([entry['key'] for entry in classes], dtype=np.float32)
    votes = np.zeros(master.shape[:2] + (len(classes),), dtype=np.float32)
    off_palette = 0.0
    for copy in copies:
        distance = np.linalg.norm(copy.astype(np.float32)[..., None, :] - keys, axis=-1)
        nearest = distance.argmin(-1)
        off_palette += float((distance.min(-1) > 70.0).mean()) / len(copies)
        votes += np.eye(len(classes), dtype=np.float32)[nearest]
    guide = master[..., :3].astype(np.float32) @ surface_materials.LUMA / 255.0
    present = [index for index in range(len(classes)) if votes[..., index].any()]
    refined = np.full(votes.shape, -1.0, dtype=np.float32)
    for index in present:
        refined[..., index] = guided(guide, votes[..., index] / len(copies), 3, 2e-3)
    indices = refined.argmax(-1)
    # Specks smaller than a few texels join their surroundings.
    for _ in range(2):
        counts = np.stack([ndimage.uniform_filter((indices == i).astype(np.float32), 3) for i in present], -1)
        majority = np.array(present)[counts.argmax(-1)]
        indices = np.where(counts.max(-1) > 0.66, majority, indices)
    return indices, off_palette


def family_copy(entry, textures, height, indices, master):
    """Copies an accepted relative's maps wherever this master and the relative's share exact pixels (wall pieces
    cut from one canvas), and eases the generated height into them, so joints between the pieces match."""
    copied = np.zeros(height.shape, dtype=bool)
    target_height = height.copy()
    target_indices = indices.copy()
    used = []
    for relative in entry.get('relatives', []):
        other = textures.get(relative['id'])
        if other is None or not installed(other):
            continue
        folder = SOURCES / 'worlds' / other['world'] / 'surface_materials'
        with Image.open(master_path(other)) as image:
            other_master = np.asarray(image.convert('RGBA'))
        other_height = surface_materials.read_height(folder / f"{other['name']}_h.png")
        with Image.open(folder / f"{other['name']}_m.png") as image:
            other_indices = surface_materials.class_indices(np.asarray(image.convert('RGB')), CLASSES)
        # The relative's pixel (x, y) is this texture's (x + dx, y + dy), in native pixels.
        dx, dy = relative['dx'] * surface_materials.TIER_SCALE, relative['dy'] * surface_materials.TIER_SCALE
        h, w = height.shape
        oh, ow = other_height.shape
        x0, y0 = max(0, dx), max(0, dy)
        x1, y1 = min(w, ow + dx), min(h, oh + dy)
        if x1 <= x0 or y1 <= y0:
            continue
        mine = master[y0:y1, x0:x1]
        theirs = other_master[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
        same = (mine == theirs).all(-1) & ~copied[y0:y1, x0:x1]
        if same.mean() < 0.02:
            continue
        region = (slice(y0, y1), slice(x0, x1))
        target_height[region] = np.where(same, other_height[y0 - dy:y1 - dy, x0 - dx:x1 - dx], target_height[region])
        target_indices[region] = np.where(same, other_indices[y0 - dy:y1 - dy, x0 - dx:x1 - dx],
                                          target_indices[region])
        copied[region] |= same
        used.append(relative['id'])
    if copied.any():
        # The generated side takes the step at the copied edge away over a few texels.
        difference = np.where(copied, target_height - height, 0.0)
        weight = ndimage.gaussian_filter(copied.astype(np.float32), 6.0)
        correction = ndimage.gaussian_filter(difference, 6.0) / np.maximum(weight, 1e-4)
        fade = np.exp(-ndimage.distance_transform_edt(~copied) / 6.0)
        target_height = np.where(copied, target_height, height + correction * fade * (weight > 1e-3))
    return np.clip(target_height, 0.0, 1.0), target_indices, used


CLASSES = surface_materials.load_classes()


def candidate(job, texture_id, textures):
    """The aligned, snapped and family-matched maps of one texture, with its check results."""
    request = job['requests'][texture_id]
    entry = textures[texture_id]
    with Image.open(master_path(entry)) as image:
        master = np.asarray(image.convert('RGBA'))
    size = (master.shape[1], master.shape[0])
    problems = []
    heights = [copy.astype(np.float32).mean(-1) / 255.0 for copy in returned(
        raw_path(job['id'], request, 'height'), size, request['copies'], request['axis'], Image.LANCZOS)]
    height = np.mean(heights, axis=0)
    luminance = master[..., :3].astype(np.float32) @ surface_materials.LUMA / 255.0
    shift = phase_shift(edges(luminance), edges(height))
    if max(abs(shift[0]) / size[1], abs(shift[1]) / size[0]) > MAX_SHIFT_FRACTION:
        problems.append(f'height misaligned by {shift} texels')
    correlation = float(np.corrcoef(luminance.ravel(), height.ravel())[0, 1])
    if correlation > MAX_HEIGHT_LUMINANCE_CORRELATION:
        problems.append(f'height follows the colours (correlation {correlation:.2f})')
    height = seamless(height, entry.get('wrap') or '')
    classes_copies = returned(raw_path(job['id'], request, 'classes'), size, request['copies'], request['axis'],
                              Image.NEAREST)
    indices, off_palette = snap_classes(classes_copies, master, CLASSES)
    if off_palette > MAX_OFF_PALETTE:
        problems.append(f'{off_palette:.0%} of the class map is no key colour')
    height, indices, used = family_copy(entry, textures, height, indices, master)
    return master, height, indices, used, problems, correlation


def write_candidate(folder, name, height, indices):
    Image.fromarray(np.clip(np.rint(height * 65535.0), 0, 65535).astype(np.uint16)).save(folder / f'{name}_h.png')
    palette = np.array([entry['key'] for entry in CLASSES], dtype=np.uint8)
    Image.fromarray(palette[indices]).save(folder / f'{name}_m.png')


def cmd_process(args):
    job = load_job(args.job)
    textures = inventory()
    state = ledger_state()
    folder = job_dir(job['id'])
    rows = []
    report = {}
    for texture_id, request in job['requests'].items():
        if state.get(texture_id, {}).get('status') != 'claimed' or state[texture_id].get('job') != job['id']:
            continue
        if not all(raw_path(job['id'], request, kind).exists() for kind in KINDS):
            print(f"  {request['name']}: waiting for generation")
            continue
        master, height, indices, used, problems, correlation = candidate(job, texture_id, textures)
        write_candidate(folder / 'candidates', request['name'], height, indices)
        normal, detail = surface_materials.build_maps(master, height, indices, CLASSES,
                                                      {'wrap': textures[texture_id].get('wrap') or ''})
        report[texture_id] = {'problems': problems, 'family': used, 'correlation': round(correlation, 3),
                              'versions': request['versions']}
        rows.append((request['name'], master, height, indices, normal, detail, problems))
        print(f"  {request['name']}: {'; '.join(problems) if problems else 'ok'}"
              + (f" (family {', '.join(used)})" if used else ''))
    write_json(folder / 'results.json', report)
    if rows:
        sheet = review_sheet(rows)
        sheet.save(folder / 'review' / 'sheet.png')
        print(f"review sheet {folder / 'review' / 'sheet.png'}")


def review_sheet(rows, cell=220):
    palette = np.array([entry['key'] for entry in CLASSES], dtype=np.uint8)
    columns = 5
    sheet = Image.new('RGB', (columns * cell, len(rows) * (cell + 14)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for row, (name, master, height, indices, normal, detail, problems) in enumerate(rows):
        tiles = [master[..., :3], np.repeat((height * 255).astype(np.uint8)[..., None], 3, -1), palette[indices],
                 surface_materials.lit_preview(master, normal, detail, (-0.85, 0.55, 0.3)),
                 surface_materials.lit_preview(master, normal, detail, (0.8, -0.4, 0.35))]
        for column, tile in enumerate(tiles):
            image = Image.fromarray(np.ascontiguousarray(tile))
            image.thumbnail((cell - 4, cell - 4), Image.LANCZOS)
            sheet.paste(image, (column * cell + 2, row * (cell + 14) + 2))
        label = name + ('  ! ' + '; '.join(problems) if problems else '')
        draw.text((4, row * (cell + 14) + cell), label, fill=(255, 120, 120) if problems else (230, 230, 230))
    return sheet


def install(entry, height_path, classes_path, textures):
    """Copies a candidate into assets_source for the texture and its exact duplicates, with their settings."""
    targets = [entry] + [other for other in textures.values()
                         if other.get('canonical') == entry['id'] and other['id'] != entry['id']]
    for target in targets:
        folder = SOURCES / 'worlds' / target['world'] / 'surface_materials'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{target['name']}_h.png").write_bytes(height_path.read_bytes())
        (folder / f"{target['name']}_m.png").write_bytes(classes_path.read_bytes())
        settings_path = folder / 'textures.yml'
        with open(settings_path.with_suffix('.lock'), 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            settings = (yaml.safe_load(settings_path.read_text()) or {}) if settings_path.is_file() else {}
            settings.setdefault(target['name'], {})['wrap'] = target.get('wrap') or ''
            settings_path.write_text(
                '# Surface material settings per texture (level_generation/surface_materials/mat.py writes wrap;\n'
                '# depth and painted_shading are review overrides, tools/surface_materials.py).\n'
                + yaml.safe_dump(dict(sorted(settings.items())), sort_keys=True))
    return [target['id'] for target in targets]


def cmd_accept(args):
    job = load_job(args.job)
    textures = inventory()
    state = ledger_state()
    report = load_json(job_dir(job['id']) / 'results.json', {})
    events = []
    for texture_id, request in job['requests'].items():
        if args.names and request['name'] not in args.names:
            continue
        if state.get(texture_id, {}).get('status') != 'claimed' or texture_id not in report:
            continue
        if report[texture_id]['problems'] and not args.names:
            print(f"  skip {request['name']}: {'; '.join(report[texture_id]['problems'])}")
            continue
        # Re-match the family: relatives accepted since processing are copied in now.
        master, height, indices, used, _, _ = candidate(job, texture_id, textures)
        folder = job_dir(job['id']) / 'candidates'
        write_candidate(folder, request['name'], height, indices)
        ids = install(textures[texture_id], folder / f"{request['name']}_h.png",
                      folder / f"{request['name']}_m.png", textures)
        events += [{'event': 'accept', 'id': i, 'job': job['id'], 'family': used} for i in ids]
        print(f"  accepted {request['name']}" + (f" (+{len(ids) - 1} duplicates)" if len(ids) > 1 else ''))
    append_events(events)


def cmd_retry(args):
    job = load_job(args.job)
    for texture_id, request in job['requests'].items():
        if request['name'] == args.name:
            request['versions'][args.kind] += 1
            if args.note:
                request['notes'][f"{args.kind}_v{request['versions'][args.kind]}"] = args.note
            save_job(job)
            print(f"{args.name}: {args.kind} v{request['versions'][args.kind]}")
            return
    raise SystemExit(f'{args.name} is not in {args.job}')


def cmd_release(args):
    job = load_job(args.job)
    state = ledger_state()
    append_events([{'event': 'release', 'id': texture_id, 'job': job['id']}
                   for texture_id, request in job['requests'].items()
                   if (not args.names or request['name'] in args.names)
                   and state.get(texture_id, {}).get('status') == 'claimed'])


def cmd_auto(args):
    """Production: job after job of the world (or map), generated, processed and installed where the checks pass;
    flagged textures stay claimed for review (their sheets stay in the jobs)."""
    for index in range(args.jobs):
        before = {path.parent.name for path in JOBS.glob('*/job.json')}
        cmd_next(argparse.Namespace(world=args.world, map=args.map, names=None, count=JOB_SIZE))
        created = sorted({path.parent.name for path in JOBS.glob('*/job.json')} - before)
        if not created:
            break
        job_id = created[0]
        cmd_gen(argparse.Namespace(world=None, job=job_id, parallel=args.parallel, no_retry=False))
        cmd_process(argparse.Namespace(job=job_id))
        cmd_accept(argparse.Namespace(job=job_id, names=[]))
        print(f'auto: job {index + 1}/{args.jobs} {job_id} done', flush=True)


def cmd_relabel(args):
    """A review correction of an installed class map: every texel of one class becomes another (amber glass that came
    back as the glowing class). Also its exact duplicates."""
    world, name = args.texture.split('/')
    names = [entry['name'] for entry in CLASSES]
    source, target = names.index(args.source), names.index(args.target)
    textures = inventory()
    entry = textures[args.texture]
    folder = SOURCES / 'worlds' / world / 'surface_materials'
    with Image.open(folder / f'{name}_m.png') as image:
        indices = surface_materials.class_indices(np.asarray(image.convert('RGB')), CLASSES)
    changed = int((indices == source).sum())
    indices[indices == source] = target
    write_candidate(folder, f'{name}.relabel', np.zeros(indices.shape), indices)
    (folder / f'{name}.relabel_h.png').unlink()
    for other in [entry] + [o for o in textures.values() if o.get('canonical') == entry['id'] and o['id'] != entry['id']]:
        target_folder = SOURCES / 'worlds' / other['world'] / 'surface_materials'
        (target_folder / f"{other['name']}_m.png").write_bytes((folder / f'{name}.relabel_m.png').read_bytes())
    (folder / f'{name}.relabel_m.png').unlink()
    print(f'{args.texture}: {changed} texels {args.source} -> {args.target}')


def cmd_status(args):
    textures = inventory()
    state = ledger_state()
    for world in ([args.world] if args.world else surface_materials.WORLDS):
        counts = {}
        for texture_id, entry in textures.items():
            if entry['world'] != world or not master_path(entry).is_file():
                continue
            status = 'accepted' if installed(entry) else state.get(texture_id, {}).get('status', 'pending')
            counts[status] = counts.get(status, 0) + 1
        print(world, ' '.join(f'{key} {value}' for key, value in sorted(counts.items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('status')
    command.add_argument('--world')
    command = sub.add_parser('next')
    command.add_argument('--world', required=True)
    command.add_argument('--map')
    command.add_argument('--names')
    command.add_argument('--count', type=int, default=JOB_SIZE)
    command.add_argument('--redo', action='store_true', help='claim installed textures again (named ones)')
    command = sub.add_parser('gen')
    command.add_argument('--world')
    command.add_argument('--job')
    command.add_argument('--parallel', type=int, default=8)
    command.add_argument('--no-retry', action='store_true')
    command = sub.add_parser('process')
    command.add_argument('job')
    command = sub.add_parser('relabel')
    command.add_argument('texture', help='<world>/<name> of an installed texture')
    command.add_argument('source')
    command.add_argument('target')
    command = sub.add_parser('auto')
    command.add_argument('--world', required=True)
    command.add_argument('--map')
    command.add_argument('--jobs', type=int, default=1)
    command.add_argument('--parallel', type=int, default=10)
    command = sub.add_parser('accept')
    command.add_argument('job')
    command.add_argument('names', nargs='*')
    command = sub.add_parser('retry')
    command.add_argument('job')
    command.add_argument('name')
    command.add_argument('--kind', choices=KINDS, required=True)
    command.add_argument('--note')
    command = sub.add_parser('release')
    command.add_argument('job')
    command.add_argument('names', nargs='*')
    args = parser.parse_args()
    JOBS.mkdir(parents=True, exist_ok=True)
    {'status': cmd_status, 'next': cmd_next, 'gen': cmd_gen, 'process': cmd_process, 'accept': cmd_accept,
     'retry': cmd_retry, 'release': cmd_release, 'auto': cmd_auto,
     'relabel': cmd_relabel}[args.command](args)


if __name__ == '__main__':
    main()
