"""Fitted paperdoll art for the Hesper equipment (pieces.yml), at the engine's x2 icon scale.

    python3 scripts/paperdoll.py prepare <piece>        targets, Codex inputs and one job per master
    python3 scripts/paperdoll.py codex <piece> [types]  run the Codex image workers (at most four at once)
    python3 scripts/paperdoll.py candidates <piece>     every generation fitted and worn, side by side, to pick from
    python3 scripts/paperdoll.py fit <piece> [t<N>=<raw file> ...]
                                                        key and fit the picked generations, derive the doll files
    python3 scripts/paperdoll.py review <piece>         previews on every doll in both poses, pair checks
    python3 scripts/paperdoll.py install <piece>        copy the reviewed files to runtime/ and record them
    python3 scripts/paperdoll.py glove <gauntlets> [prepare | codex | fit <raw file>]
                                                        a pair of gauntlets drawn as one glove for the jewellery slot

The reference item's fitted MM files own canvas, silhouette and placement; the Hesper icon owns the design (the MM9
workflow, devdocs/mm9/MM9_ARMOR_PAPERDOLL_AI_GENERATION.md). A generated image is only an RGB proposal: it is keyed and
fitted into the exact target alpha by tools/mm9_import_discovery/fit_mm9_ai_equipment_variant.py.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

import dolls as D
import fit_mm9_ai_equipment_variant as fitter

PROJECT = D.PROJECT
WORK = PROJECT / 'work'
RUNTIME = PROJECT / 'runtime'
RUNS = PROJECT / 'generation_runs_paperdoll.json'
ICON_MASTERS = D.ROOT / 'design/kreegan_world/art/item_icons/masters'
ICONS_X2 = D.ROOT / 'design/kreegan_world/art/item_icons/x2'
DRAFT_ITEMS = D.ROOT / 'design/kreegan_world/data/items.txt'
COVERAGE = yaml.safe_load((D.ROOT / 'tools/mm9_import_discovery/mm9_armor_foot_exclusions.yml').read_text())
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
# The image tool's canvases; a frame around the target takes the closest aspect.
CANVASES = ((1024, 1536), (1024, 1024), (1536, 1024))
# character.yml CharacterDollGauntletsSlot: the jewellery panel's gauntlet frame (logical pixels). The engine draws a
# gauntlet icon from its top-left corner plus the item's complex_item_pictures point; MM's single gloves fit it.
GAUNTLET_SLOT = (40, 72)
MIN_COMPONENT = 48        # physical pixels: smaller detached alpha islands in a reference are stray native pixels
# The doll types each slot draws and the file suffix of each (the engine's resolveEquippedItemHudTextureName).
SLOT_TYPES = {'Armor': (0, 1, 2, 3, 4), 'Helm': (0, 1, 3, 4), 'Boots': (0, 1, 3, 4), 'Belt': (0, 1, 2, 3, 4),
              'Cloak': (0, 1, 4)}
# What the prompt calls each slot's piece, and what it may paint.
SLOT_NOUN = {'Armor': 'armour', 'Helm': 'helm', 'Boots': 'pair of boots', 'Belt': 'belt', 'Cloak': 'cloak'}
SLOT_RULES = {
    'Armor': 'Body armour pixels only. Construct the neck opening, shoulders, armholes, torso, waist and hem around '
             'the body. The armour ends at the hips: no legs, trousers, boots or feet. Do not paint skin, arms, '
             'hands, a weapon, a shield, a belt item or a cloak.',
    'Helm': 'Helm pixels only: a closed helmet enclosing the whole head, as Image 1 does; the face is hidden behind '
            'its visor or faceplate. Do not paint skin, a face, hair, horns, the neck below the helm\'s rim, '
            'shoulders or armour.',
    'Boots': 'Boot pixels only: both boots, each from the top of its shaft on the shin down to the sole, in Image 1\'s '
             'stance with the same foot forward and the same toe directions. Do not paint legs, trousers, skin, '
             'the ground or a shadow.',
    'Belt': 'Belt pixels only: the belt around the waist as Image 1 draws it, following its curve around the body, '
            'with its buckle or centre piece at the front where Image 1 has it. Do not paint the body, clothes, '
            'skin or anything hanging below the grey shape.',
    'Cloak': 'Cloak pixels only. Image 1 is the cloak as the game draws it: hanging behind the wearer and seen from '
             'the front, so what shows is the inside of the cloak (its lining), the collar standing up behind the '
             'neck and the edges falling past the shoulders and legs; the body is drawn over its middle later. '
             'Paint the inside, collar and edges of this cloak in the item\'s materials and colours. Do not paint '
             'the person, a face or a hood over a head, clasps or anything in front of the body.',
}


def pieces():
    return yaml.safe_load((PROJECT / 'pieces.yml').read_text())['pieces']


def master_of(piece, doll_type):
    """The doll type whose generated master this type's file reuses: `shares` in pieces.yml, else, outside armour
    (whose targets differ by the feet), the first earlier type whose reference file is pixel-identical."""
    shares = piece.get('shares', {})
    if doll_type in shares or piece['slot'] == 'Armor':
        return shares.get(doll_type, doll_type)
    icon = D.ENGINE_ITEMS[piece['reference']].icon_name
    own = np.asarray(D.layer(icon + suffix(piece['slot'], doll_type)))
    for other in SLOT_TYPES[piece['slot']]:
        if other == doll_type:
            break
        if master_of(piece, other) == other:
            pixels = np.asarray(D.layer(icon + suffix(piece['slot'], other)))
            if pixels.shape == own.shape and np.array_equal(pixels, own):
                return other
    return doll_type


def master_types(piece):
    return piece.get('masters') or [t for t in SLOT_TYPES[piece['slot']] if master_of(piece, t) == t]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def suffix(slot, doll_type, weapon=False):
    number = 1 if slot == 'Cloak' and doll_type in (2, 3) else doll_type + 1
    if slot == 'Armor':
        return f'v{number}' if weapon else f'v{number}a'
    return f'v{number}a' if slot == 'Cloak' else f'v{number}'


def foot_mask(doll_type):
    """The physical full-doll region body armour must leave visible: a native boot (MM7 Leather Boots) on the dolls
    that wear boots, the minotaur's hooves below the MM9 pipeline's reviewed line."""
    if doll_type == 2:
        mask = np.zeros((D.HEIGHT, D.WIDTH), dtype=bool)
        for character in (21, 22):
            doll = D.preview.read_character_dolls(D.TABLES / 'character_data.txt')[character]
            body = D.alpha(D.layer(doll.body_asset))
            mask |= D.place(body, (doll.body_x, doll.body_y))
        mask[:307 * D.SCALE] = False
    else:
        boots = D.ENGINE_ITEMS[917]
        mask = D.place(D.alpha(D.layer(f'{boots.icon_name}v{doll_type + 1}')), D.ENGINE_POINTS[917][doll_type])
    return ndimage.binary_dilation(mask, iterations=D.SCALE)


def clean_components(mask):
    labels, count = ndimage.label(mask, structure=np.ones((3, 3)))
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = np.isin(labels, [index + 1 for index, size in enumerate(sizes) if size >= MIN_COMPONENT])
    return keep, int(np.count_nonzero(mask & ~keep))


def target_alpha(piece, doll_type, weapon=False):
    """The audited target alpha of one doll file (layer-local, physical, uint8): the reference file's own soft
    alpha, cut by the coverage profile (feathered over two pixels), cleared of near-invisible noise, stray islands and,
    for armour, the feet."""
    reference = D.ENGINE_ITEMS[piece['reference']]
    point = D.ENGINE_POINTS[piece['reference']][doll_type]
    image = D.layer(reference.icon_name + suffix(piece['slot'], doll_type, weapon))
    soft = np.asarray(image)[:, :, 3].copy()
    report = {'reference_file': reference.icon_name + suffix(piece['slot'], doll_type, weapon),
              'reference_alpha': int((soft > 0).sum())}
    if piece.get('coverage'):
        limit = COVERAGE['coverage_profiles'][piece['coverage']]['max_global_y_exclusive']
        limit = {**(limit or {}), **piece.get('coverage_limits', {})} or None
        if limit is not None and doll_type in limit:
            local = max(0, (limit[doll_type] - point[1]) * D.SCALE)
            report['coverage_removed'] = int((soft[local:] > 0).sum())
            soft[local:] = 0
            for offset, keep in ((1, 1 / 3), (2, 2 / 3)):
                if 0 <= local - offset < soft.shape[0]:
                    soft[local - offset] = (soft[local - offset] * keep).astype(np.uint8)
    soft[soft < 16] = 0
    soft[soft >= 248] = 255          # the restored native icons are 252-253 where they mean opaque
    kept, report['stray_removed'] = clean_components(soft > 0)
    soft[~kept] = 0
    if piece.get('smooth_crown'):
        # A morphological opening over the file's top half takes the reference's crown studs or spikes off the
        # outline (the design is the Hesper icon's, not MM's); the cut edge is feathered like the coverage cut.
        radius = piece['smooth_crown']
        disk = np.hypot(*np.mgrid[-radius:radius + 1, -radius:radius + 1]) <= radius
        opened = ndimage.binary_opening(soft > 0, structure=disk)
        removed = (soft > 0) & ~opened
        removed[soft.shape[0] // 2:] = False
        soft[removed] = 0
        near = ndimage.binary_dilation(removed, iterations=2) & (soft > 0)
        soft[near] = (soft[near] * 2 / 3).astype(np.uint8)
        report['crown_removed'] = int(removed.sum())
    if piece['slot'] == 'Armor':
        placed = D.place(soft > 0, point)
        local = np.zeros(soft.shape, dtype=bool)
        x, y = point[0] * D.SCALE, point[1] * D.SCALE
        ys, xs = np.nonzero(placed & foot_mask(doll_type))
        local[ys - y, xs - x] = True
        report['foot_removed'] = int(local.sum())
        soft[local] = 0
    report['target_alpha'] = int((soft > 0).sum())
    return soft, image, point, report


def frame_for(mask, point):
    """A doll-space rectangle around the target, padded to the closest image-tool canvas aspect."""
    ys, xs = np.nonzero(D.place(mask, point))
    left, top, right, bottom = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    width, height = right - left, bottom - top
    canvas = min(CANVASES, key=lambda size: abs(np.log((size[0] / size[1]) / (width / height))))
    scale = min(canvas[0] / (width * 1.16), canvas[1] / (height * 1.16))
    frame_width, frame_height = canvas[0] / scale, canvas[1] / scale
    center_x, center_y = (left + right) / 2, (top + bottom) / 2
    box = (center_x - frame_width / 2, center_y - frame_height / 2, center_x + frame_width / 2,
           center_y + frame_height / 2)
    return canvas, tuple(round(value) for value in box)


def framed(image, box, canvas, background, resample=Image.Resampling.NEAREST):
    """Crop a doll-space image to the frame (outside the doll filled) and scale it to the canvas."""
    padded = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), background + (255,))
    padded.alpha_composite(image, (-box[0], -box[1]))
    return padded.convert('RGB').resize(canvas, resample)


def prompt(piece, doll_type, canvas):
    name = piece['name']
    noun = SLOT_NOUN[piece['slot']]
    follows = 'the body, chest, shoulders and waist it follows' if piece['slot'] == 'Armor' else 'the body it fits'
    return f"""Use case: precise-object-edit
Asset type: one fitted equipment-layer sprite for a late-1990s Might and Magic VI-VIII style RPG paperdoll

Paint {name}, a piece of Hesper equipment, as a fitted {D.DOLL_NAMES[doll_type]} paperdoll layer.

Inputs:
- Image 1 is the edit base: the fitted Might and Magic {noun} this layer replaces, already worn in the exact pose.
  Repaint it as {name}. Keep its outline, perspective, anatomical fit, lighting direction and painted sprite style;
  replace its design, colours and ornament completely with the design of Image 4.
- Image 2 is the exact two-colour target mask on the same canvas: grey is where the {noun} goes, magenta is
  background. The result must cover the grey shape and nothing else.
- Image 3 is the {D.DOLL_NAMES[doll_type]} doll the {noun} is worn on, on the same canvas: {follows}. Do not paint
  the person.
- Image 4 is the item's inventory picture. It owns the design: materials, colours, plates, trim and ornaments.

Design facts: {piece['facts']}

Keep the outline of Image 1 and Image 2 exactly: same position, size and silhouette on the canvas, the same
three-quarter turn of the body. Do not draw the flat front view of the inventory picture. Never stretch, tile or
paste the flat inventory picture; redraw its plates, trim and ornaments at a scale that fits this body.
Keep the item's identity; invent nothing that is not in Image 4.

{SLOT_RULES[piece['slot']]}

Style: hand-painted Might and Magic VI-VIII paperdoll equipment; neutral frontal light slightly brighter from the upper
left; modest painted highlights; crisp and readable after downsampling to about a quarter of this size; no modern
glossy 3D, no photorealism.

Output: one image of {canvas[0]}x{canvas[1]} pixels, the {noun} on one perfectly uniform solid #FF00FF magenta
background exactly where Image 2 is magenta. No checkerboard, gradient, shadow, glow, text, border or watermark;
magenta never inside the {noun}."""


def prepare(name):
    piece = pieces()[name]
    folder = WORK / name
    jobs = []
    for doll_type in master_types(piece):
        job = folder / f't{doll_type}'
        (job / 'raw').mkdir(parents=True, exist_ok=True)
        soft, reference, point, report = target_alpha(piece, doll_type)
        mask = soft >= 128
        canvas, box = frame_for(mask, point)
        placed = D.place(mask, point)
        guide = Image.new('RGBA', (D.WIDTH, D.HEIGHT), MAGENTA + (255,))
        guide.paste(Image.new('RGBA', guide.size, GRAY + (255,)), mask=Image.fromarray(placed.astype(np.uint8) * 255))
        framed(guide, box, canvas, MAGENTA).save(job / 'in_2_mask.png')
        base = np.asarray(reference).copy()
        base[:, :, 3] = np.minimum(base[:, :, 3], soft)
        base_layer = Image.new('RGBA', (D.WIDTH, D.HEIGHT))
        base_layer.alpha_composite(Image.fromarray(base), (point[0] * D.SCALE, point[1] * D.SCALE))
        framed(base_layer, box, canvas, MAGENTA).save(job / 'in_1_reference.png')
        framed(D.doll(doll_type), box, canvas, (40, 40, 40)).save(job / 'in_3_doll.png')
        icon = Image.open(ICON_MASTERS / f'{name}.png').convert('RGBA')
        sheet = Image.new('RGBA', icon.size, (255, 255, 255, 255))
        sheet.alpha_composite(icon)
        sheet.convert('RGB').save(job / 'in_4_icon.png')
        target = np.dstack([np.full(mask.shape + (3,), 128, np.uint8), soft])
        Image.fromarray(target).save(job / 'target.png')
        meta = {'piece': name, 'doll_type': doll_type, 'suffix': suffix(piece['slot'], doll_type), 'point': point,
                'canvas': canvas, 'frame': box, **report}
        if piece['slot'] == 'Armor':
            weapon_mask, _, _, weapon_report = target_alpha(piece, doll_type, weapon=True)
            Image.fromarray(np.dstack([np.full(weapon_mask.shape + (3,), 128, np.uint8), weapon_mask])).save(
                job / 'target_weapon.png')
            meta['weapon'] = weapon_report
            meta['weapon_outside_master'] = int(((weapon_mask > 0) & (soft == 0)).sum())
            meta['weapon_identical'] = bool(np.array_equal(weapon_mask, soft))
        (job / 'job.json').write_text(json.dumps(meta, indent=2) + '\n')
        (job / 'prompt.txt').write_text(prompt(piece, doll_type, canvas) + '\n')
        jobs.append(job)
        print(job.relative_to(PROJECT), canvas, report)
    return jobs


def run_codex(job):
    images = sorted(job.glob('in_*.png'))
    rel = job.relative_to(D.ROOT)
    instruction = (f'Follow level_generation/ui/hesper_paperdoll/CODEX_BRIEF.md exactly for the job folder {rel}. '
                   f'The {len(images)} attached images are its inputs 1-{len(images)} in order.')
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', str(D.ROOT), '--skip-git-repo-check',
                 '--add-dir', str(Path.home() / '.codex/generated_images')]
    for image in images:
        arguments += ['-i', str(image)]
    with (job / 'raw/codex_run.log').open('a') as log:
        result = subprocess.run(arguments, input=instruction, text=True, stdout=log, stderr=subprocess.STDOUT)
    return job, result.returncode


def codex(name, types=None):
    piece = pieces()[name]
    wanted = [int(value) for value in types.split(',')] if types else master_types(piece)
    jobs = [WORK / name / f't{doll_type}' for doll_type in wanted]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for job, code in pool.map(run_codex, jobs):
            print('DONE', job.relative_to(PROJECT), code, sorted(path.name for path in (job / 'raw').glob('gen_*.png')))


def candidates(name):
    """Every generation of every master fitted into its target and worn on its doll, beside the reference, with the
    share of the target the fitter had to fill from neighbours (work/<piece>/review/candidates.jpg)."""
    piece = pieces()[name]
    rows = []
    for doll_type in master_types(piece):
        job = WORK / name / f't{doll_type}'
        meta = json.loads((job / 'job.json').read_text())
        target = Image.open(job / 'target.png')
        point = tuple(meta['point'])
        base = D.doll(doll_type)
        x, y = point[0] * D.SCALE, point[1] * D.SCALE
        box = (max(0, x - 40), max(0, y - 40), min(D.WIDTH, x + target.width + 40), min(D.HEIGHT, y + target.height + 40))
        cells = []
        reference = D.layer(meta['suffix'] and D.ENGINE_ITEMS[piece['reference']].icon_name + meta['suffix'])
        for label, layer in [('reference', reference)] + [
                (raw.name, raw) for raw in sorted((job / 'raw').glob('gen_*.png'))]:
            worn = base.copy()
            if isinstance(layer, Path):
                fitted, report = fitter.fit_generated_art(Image.open(layer), target, None, 242, 2, 150, 'hybrid',
                                                          'magenta', True)
                label += f" fill {100 * report['filled_pixels'] / report['target_alpha_pixels']:.0f}%"
                layer = fitted
            if piece['slot'] == 'Cloak':              # the doll render is opaque: show the cloak alone
                worn = Image.new('RGBA', worn.size, (70, 70, 74, 255))
                worn.alpha_composite(layer.convert('RGBA'), (x, y))
            else:
                worn.alpha_composite(layer.convert('RGBA'), (x, y))
            cell = worn.crop(box).convert('RGB')
            ImageDraw.Draw(cell).text((4, 4), f't{doll_type} {label}', fill=(255, 255, 0))
            cells.append(cell)
        row = Image.new('RGB', (sum(cell.width for cell in cells), cells[0].height), (20, 20, 20))
        offset = 0
        for cell in cells:
            row.paste(cell, (offset, 0))
            offset += cell.width
        rows.append(row)
    sheet = Image.new('RGB', (max(row.width for row in rows), sum(row.height for row in rows)), (20, 20, 20))
    offset = 0
    for row in rows:
        sheet.paste(row, (0, offset))
        offset += row.height
    out = WORK / name / 'review'
    out.mkdir(parents=True, exist_ok=True)
    scale = min(1.0, 1800 / sheet.width)
    sheet.resize((round(sheet.width * scale), round(sheet.height * scale)), Image.Resampling.LANCZOS).save(
        out / 'candidates.jpg', quality=88)
    print(out / 'candidates.jpg')


def derive_pose(master, alternate):
    """The other arm pose: the master's pixels inside the alternate (soft) alpha; pixels the master lacks take the
    nearest master pixel (counted, so the review sees them)."""
    pixels = np.asarray(master).copy()
    inside = pixels[:, :, 3] > 0
    output = np.zeros_like(pixels)
    output[:, :, :3] = pixels[:, :, :3]
    missing = (alternate > 0) & ~inside
    if missing.any():
        near_y, near_x = fitter.nearest_indices(inside)
        output[missing, :3] = pixels[near_y[missing], near_x[missing], :3]
    output[:, :, 3] = alternate
    output[alternate == 0, :3] = 0
    return Image.fromarray(output), int(missing.sum())


def fit(name, picks):
    piece = pieces()[name]
    out = WORK / name / 'fitted'
    out.mkdir(parents=True, exist_ok=True)
    chosen = dict(pick.split('=', 1) for pick in picks)
    records = {}
    for doll_type in SLOT_TYPES[piece['slot']]:
        master_type = master_of(piece, doll_type)
        job = WORK / name / f't{master_type}'
        meta = json.loads((job / 'job.json').read_text())
        raw = job / 'raw' / chosen.get(f't{master_type}', 'gen_1.png')
        if doll_type == master_type:
            target = Image.open(job / 'target.png')
            fitted, report = fitter.fit_generated_art(Image.open(raw), target, None, 242, 2, 150, 'hybrid',
                                                      'magenta', True)
            report['alpha_exact'] = fitted.getchannel('A').tobytes() == target.getchannel('A').tobytes()
        else:
            fitted = Image.open(out / f"{name}{suffix(piece['slot'], master_type)}.png")
            report = {'shared_from': master_type}
        master_name = f"{name}{suffix(piece['slot'], doll_type)}"
        fitted.save(out / f'{master_name}.png')
        record = {'file': master_name + '.png', 'raw': raw.relative_to(PROJECT).as_posix(), 'raw_sha256': sha256(raw),
                  'fit': report, 'sha256': sha256(out / f'{master_name}.png')}
        if piece['slot'] == 'Armor':
            weapon = np.asarray(Image.open(job / 'target_weapon.png'))[:, :, 3]
            weapon_image, filled = derive_pose(fitted, weapon)
            weapon_name = f"{name}{suffix('Armor', doll_type, weapon=True)}"
            weapon_image.save(out / f'{weapon_name}.png')
            record['weapon_pose'] = {'file': weapon_name + '.png', 'filled_outside_master': filled,
                                     'identical': weapon_image.tobytes() == fitted.convert('RGBA').tobytes(),
                                     'sha256': sha256(out / f'{weapon_name}.png')}
        records[f't{doll_type}'] = record
        print(f't{doll_type}', json.dumps({key: record[key] for key in record if key != 'fit'}),
              'alpha_exact' if report.get('alpha_exact', True) else 'ALPHA MISMATCH')
    (out / 'fit.json').write_text(json.dumps(records, indent=2) + '\n')


def picture_rows(names):
    """complex_item_pictures rows: each piece takes its reference's logical points (its canvases are the
    reference's); then the gauntlets (pieces.yml `gauntlets`), centred on the jewellery panel's slot."""
    rows = [['', '', 'Hesper equipment', 'Settings', 't0', '', 't1', '', 't2', '', 't3', '', 't4', '', 't5', ''],
            ['Id', 'Item id', 'Notes', ''] + ['X', 'Y'] * 6]
    for name in names:
        piece = pieces()[name]
        points = D.ENGINE_POINTS[piece['reference']]
        rows.append([str(len(rows) - 1), str(piece['id']), piece['name'], piece['slot']]
                    + [str(value) for point in points for value in point])
    for name, item_id in yaml.safe_load((PROJECT / 'pieces.yml').read_text())['gauntlets'].items():
        drawn = RUNTIME / 'icons_x2' / f'{name}v1.png'            # its single glove, or still the pair's icon
        with Image.open(drawn if drawn.exists() else ICONS_X2 / f'{name}.png') as icon:
            point = ((GAUNTLET_SLOT[0] - icon.width // D.SCALE) // 2, (GAUNTLET_SLOT[1] - icon.height // D.SCALE) // 2)
        rows.append([str(len(rows) - 1), str(item_id), name, 'Gauntlets'] + [str(value) for value in point] * 6)
    return rows


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join('\t'.join(row) + '\n' for row in rows))


def review(name):
    piece = pieces()[name]
    out = WORK / name / 'review'
    out.mkdir(parents=True, exist_ok=True)
    fitted = WORK / name / 'fitted'
    table = out / 'complex_item_pictures.txt'
    write_rows(table, picture_rows([name]))
    items = DRAFT_ITEMS          # its Pic File column names each piece's icon
    script = D.ROOT / 'tools/mm9_import_discovery/render_paperdoll_equipment_preview.py'
    shown = (0, 1, 2, 3, 4) if piece['slot'] == 'Cloak' else SLOT_TYPES[piece['slot']]   # cloaks: v1a on 2 and 3
    types = ','.join(str(t) for t in shown)
    for pose, extra in (('empty', []), ('weapon', ['--right-hand-weapon'])):
        if pose == 'weapon' and piece['slot'] != 'Armor':
            continue
        subprocess.run([sys.executable, str(script), '--item-id', str(piece['id']), '--doll-types', types,
                        '--mode', 'complete', '--output', str(out / f'{pose}.png'), '--report',
                        str(out / f'{pose}.json'), '--extra-icon-root', str(fitted), '--extra-icon-scale', '2',
                        '--extra-items-table', str(items), '--extra-complex-picture-table', str(table),
                        '--fail-on-issues'] + extra, check=True)
        reference = [sys.executable, str(script), '--item-id', str(piece['reference']), '--doll-types', types,
                     '--mode', 'complete', '--output', str(out / f'reference_{pose}.png')] + extra
        subprocess.run(reference, check=True, stdout=subprocess.DEVNULL)
    checks = {}
    for doll_type in SLOT_TYPES[piece['slot']]:
        file = fitted / f"{name}{suffix(piece['slot'], doll_type)}.png"
        image = np.asarray(Image.open(file).convert('RGBA'))
        inside = image[:, :, 3] > 0
        magenta = inside & (image[:, :, 0] > 200) & (image[:, :, 1] < 60) & (image[:, :, 2] > 200)
        check = {'opaque_magenta': int(magenta.sum()), 'partial_alpha': int(((image[:, :, 3] > 0)
                                                                              & (image[:, :, 3] < 255)).sum())}
        if piece['slot'] == 'Armor':
            point = D.ENGINE_POINTS[piece['reference']][doll_type]
            for weapon in (False, True):
                pose_file = fitted / f"{name}{suffix('Armor', doll_type, weapon)}.png"
                pose_alpha = D.alpha(Image.open(pose_file))
                check['feet_overlap_' + ('weapon' if weapon else 'empty')] = int(
                    (D.place(pose_alpha, point) & foot_mask(doll_type)).sum())
            empty = np.asarray(Image.open(fitted / f"{name}{suffix('Armor', doll_type)}.png"))
            weapon = np.asarray(Image.open(fitted / f"{name}{suffix('Armor', doll_type, True)}.png"))
            common = (empty[:, :, 3] > 0) & (weapon[:, :, 3] > 0)
            check['pair_common_rgba_differences'] = int((np.any(empty != weapon, axis=2) & common).sum())
        checks[f't{doll_type}'] = check
    (out / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps(checks))
    sheet(name, out)


def sheet(name, out):
    """One review sheet: per pose, the MM reference row above the Hesper row (half size), plus the icon."""
    rows = []
    for pose in ('empty', 'weapon'):
        if not (out / f'{pose}.png').exists():
            continue
        for kind in (f'reference_{pose}', pose):
            image = Image.open(out / f'{kind}.png')
            rows.append(image.resize((image.width // 2, image.height // 2), Image.Resampling.LANCZOS))
    icon = Image.open(ICONS_X2 / f'{name}.png').convert('RGBA')
    width = max(row.width for row in rows) + icon.width + 20
    canvas = Image.new('RGBA', (width, sum(row.height for row in rows)), (28, 28, 30, 255))
    y = 0
    for row in rows:
        canvas.alpha_composite(row.convert('RGBA'), (0, y))
        y += row.height
    canvas.alpha_composite(icon, (width - icon.width - 10, 10))
    canvas.convert('RGB').save(out / 'sheet.jpg', quality=90)
    print(out / 'sheet.jpg')


def install(name):
    piece = pieces()[name]
    fitted = WORK / name / 'fitted'
    icons = RUNTIME / 'icons_x2'
    icons.mkdir(parents=True, exist_ok=True)
    files = sorted(fitted.glob(f'{name}v*.png'))
    for file in files:
        shutil.copy2(file, icons / file.name)
    installed = [key for key in pieces() if any(icons.glob(f'{key}v*.png'))]
    write_rows(RUNTIME / 'complex_item_pictures.txt', picture_rows(installed))
    runs = json.loads(RUNS.read_text()) if RUNS.exists() else {}
    runs[name] = {'id': piece['id'], 'slot': piece['slot'], 'reference': piece['reference'],
                  'coverage': piece.get('coverage'), 'masters': json.loads((fitted / 'fit.json').read_text()),
                  'files': {file.name: sha256(file) for file in files}}
    RUNS.write_text(json.dumps(runs, indent=2) + '\n')
    print('installed', [file.name for file in files])


def glove_prompt(name):
    return f"""Use case: precise-object-edit
Asset type: one equipment icon for a late-1990s Might and Magic VI-VIII style RPG character screen

Image 1 is how Might and Magic draws a worn gauntlet in the character screen's jewellery panel: a single glove,
standing upright with the fingers up and the cuff at the bottom, seen from the back of the hand, filling a tall
narrow frame. Image 2 is a pair of Hesper gauntlets.

Paint ONE gauntlet of the pair in Image 2 (the right one) in the pose, framing and proportions of Image 1: upright,
fingers up, cuff down, back of the hand toward the viewer, slightly turned as in Image 1. Keep every detail of the
Image 2 design exactly: materials, colours, plates, lights, trim and finger segments. Do not copy Image 1's leather or
colours; it gives only the pose and framing.

Style: hand-painted Might and Magic VI-VIII item art, light slightly brighter from the upper left, crisp and readable
when shrunk to about 35 x 65 pixels; no modern glossy 3D, no photorealism.

Output: one 1024x1536 image, the single gauntlet large and centred, on one perfectly uniform solid #FF00FF magenta
background. No second glove, no hand or arm inside it, no shadow, glow outside the glove, text, border or watermark;
magenta never inside the gauntlet."""


GLOVE_BOX = (34, 64)      # logical pixels inside the 40 x 72 slot, as MM's single gloves


def glove(name, rest):
    job = WORK / name / 'glove'
    (job / 'raw').mkdir(parents=True, exist_ok=True)
    action = rest[0] if rest else 'prepare'
    if action == 'prepare':
        reference = D.layer('item127')
        canvas = Image.new('RGBA', (1024, 1536), MAGENTA + (255,))
        scale = min(800 / reference.width, 1300 / reference.height)
        enlarged = reference.resize((round(reference.width * scale), round(reference.height * scale)),
                                    Image.Resampling.LANCZOS)
        canvas.alpha_composite(enlarged, ((1024 - enlarged.width) // 2, (1536 - enlarged.height) // 2))
        canvas.convert('RGB').save(job / 'in_1_reference.png')
        icon = Image.open(ICON_MASTERS / f'{name}.png').convert('RGBA')
        sheet = Image.new('RGBA', icon.size, (255, 255, 255, 255))
        sheet.alpha_composite(icon)
        sheet.convert('RGB').save(job / 'in_2_icon.png')
        (job / 'prompt.txt').write_text(glove_prompt(name) + '\n')
    elif action == 'codex':
        print('DONE', *run_codex(job))
    elif action == 'fit':
        source = Image.open(job / 'raw' / rest[1]).convert('RGBA')
        foreground, mode = fitter.generated_foreground(source, 242, 'magenta')
        rgb, _ = fitter.despill_magenta_source(np.asarray(source)[:, :, :3].copy(), foreground)
        labels, count = ndimage.label(foreground)
        sizes = ndimage.sum(foreground, labels, range(1, count + 1))
        foreground = labels == int(np.argmax(sizes)) + 1          # the glove, without stray specks
        near_y, near_x = fitter.nearest_indices(foreground)
        rgb = rgb[near_y, near_x]                                  # no magenta under the soft edge
        ys, xs = np.nonzero(foreground)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        width, height = box[2] - box[0], box[3] - box[1]
        scale = min(GLOVE_BOX[0] * D.SCALE / width, GLOVE_BOX[1] * D.SCALE / height)
        size = (round(width * scale), round(height * scale))
        color = Image.fromarray(rgb).crop(box).resize(size, Image.Resampling.LANCZOS)
        alpha = Image.fromarray(foreground.astype(np.uint8) * 255).crop(box).resize(size, Image.Resampling.LANCZOS)
        result = color.convert('RGBA')
        result.putalpha(alpha)
        out = job / 'fitted'
        out.mkdir(exist_ok=True)
        for doll_type in range(5):                                 # the engine looks for <icon>v<doll type + 1>
            result.save(out / f'{name}v{doll_type + 1}.png')
        print('glove', size, 'logical', (size[0] // D.SCALE, size[1] // D.SCALE), mode)
    elif action == 'install':
        icons = RUNTIME / 'icons_x2'
        files = sorted((job / 'fitted').glob(f'{name}v*.png'))
        for file in files:
            shutil.copy2(file, icons / file.name)
        installed = [key for key in pieces() if any(icons.glob(f'{key}v*.png'))]
        write_rows(RUNTIME / 'complex_item_pictures.txt', picture_rows(installed))
        runs = json.loads(RUNS.read_text()) if RUNS.exists() else {}
        runs[name] = {'slot': 'Gauntlets', 'note': 'one glove of the pair for the jewellery slot',
                      'raw': json.loads((job / 'raw/runs.json').read_text()) if (job / 'raw/runs.json').exists()
                      else None, 'files': {file.name: sha256(file) for file in files}}
        RUNS.write_text(json.dumps(runs, indent=2) + '\n')
        print('installed', [file.name for file in files])


def main():
    command, name, *rest = sys.argv[1:]
    if command == 'prepare':
        prepare(name)
    elif command == 'codex':
        codex(name, rest[0] if rest else None)
    elif command == 'candidates':
        candidates(name)
    elif command == 'fit':
        fit(name, rest)
    elif command == 'review':
        review(name)
    elif command == 'install':
        install(name)
    elif command == 'glove':
        glove(name, rest)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
