"""Scoped complete-fidget repairs with separate enhanced appearances for shared native frames.

Native source identities remain unchanged. The staged atlas can give an animation its
own restored appearance while other actions retain their exact accepted artwork.
Shared restoration tools and the shared reviewer are used without modification.
"""
import argparse
import copy
import hashlib
import json
import math
import os
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TOOLS = REPO / 'level_generation/creatures/mm6_remaining/redo_2x'
COLLECTION = REPO / 'level_generation/creatures/mm6_packed_outline_collection_20261001'
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
from prepare_packed_outline import native_2x, best_grid
from whole_animation_resolution import DEFAULT_POLICY, METHOD

FAMILIES = ['mnk1', 'mer1', 'spi1', 'wfigt1', 'arc1', 'ske', 'dwa1', 'min1', 'cle']
CONTEXT = ('TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration '
           'of an EXISTING Might and Magic VI (MM6) fantasy role-playing game sprite asset, using the supplied '
           'original animation bitmaps. Restore the existing fantasy-game character and its original animation; '
           'preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return str(Path(path).relative_to(REPO))


def prepare():
    queue_path = HERE / 'repairs.json'
    existing = {r['family']: r for r in read(queue_path)['families']} if queue_path.exists() else {}
    collection = read(COLLECTION / 'collection.json')
    queue = {'method': METHOD, 'scope': 'Regenerate only the nine affected MM6 fidgets; preserve all other actions, source projects, shared code and runtime assets.',
             'enhanced_appearance_contract': 'Animation-specific enhanced frame IDs map explicitly to original native source frame IDs. Native groups, timing, scale, mirrors and source reuse remain authoritative and unchanged.',
             'families': []}
    for family in FAMILIES:
        if family in existing:
            entry = existing[family]
            job = read(REPO / entry['work_project'] / 'redo_2x/run.json')['jobs'][0]
            assert all(sha(REPO / a['path']) == a['sha256'] for a in job['prepared_assets'])
            queue['families'].append(entry)
            print('Resume valid preparation:', entry['label'])
            continue
        selected = next(r for r in collection['families'] if r['creature'] == 'mm6:' + family)
        old = (COLLECTION / selected['manifest']).resolve().parent
        root = HERE / ('mm6_' + family)
        out = root / 'redo_2x'
        work = root / 'fidget_work'
        wo = work / 'redo_2x'
        root.mkdir(exist_ok=True)
        if not out.exists():
            shutil.copytree(old, out, symlinks=False)
        for name in ['sources.json', 'config.json', 'recolor_vectors.json', 'inventory.json', 'materials.py']:
            source = old / name if (old / name).exists() else old.parent / name
            if source.exists():
                shutil.copy2(source, root / name)
        sources, config, manifest = read(root / 'sources.json'), read(root / 'config.json'), read(old / 'manifest.json')
        write(root / 'manifest.json', manifest)
        for name in ['review/acceptance.json', 'review/decision.json', 'acceptance.json']:
            if (out / name).exists():
                (out / name).unlink()
        validation = read(out / 'validation.json')
        validation['visual_review_complete'] = False
        write(out / 'validation.json', validation)
        work.mkdir(exist_ok=True)
        for folder in ['references', 'prompts', 'raw', 'review']:
            (wo / folder).mkdir(parents=True, exist_ok=True)
        for name in ['config.json', 'recolor_vectors.json', 'materials.py']:
            if (root / name).exists():
                shutil.copy2(root / name, work / name)
        names = [s['frame'] for s in manifest['animations']['fidget']['views']['0']]
        count = len(names)
        assert count > 1
        all_views = manifest['animations']['fidget']['views']
        assert all([s['frame'] for s in steps] == names for steps in all_views.values()), 'Multiple stored fidgets need separate work jobs.'
        subset_sources = copy.deepcopy(sources)
        subset_sources['sources'] = {n: sources['sources'][n] for n in names}
        subset_sources['pixel_aliases'] = {}
        write(work / 'sources.json', subset_sources)
        inventory = read(root / 'inventory.json')
        inv = copy.deepcopy(inventory[family])
        inv['sources'] = {n: inv['sources'][n] for n in names}
        inv['pixel_aliases'] = {}
        inv['unreferenced'] = []
        for variant in inv['variants'].values():
            variant['actions'] = {'fidget': variant['actions']['fidget']}
        write(work / 'inventory.json', {family: inv})
        wm = copy.deepcopy(manifest)
        wm['frames'] = {n: wm['frames'][n] for n in names}
        wm['animations'] = {'fidget': wm['animations']['fidget']}
        for palette in wm['animations_by_palette']:
            wm['animations_by_palette'][palette] = {'fidget': wm['animations_by_palette'][palette]['fidget']}
        wm['native_group_bindings'] = inv['variants']
        write(work / 'manifest.json', wm)
        images = [native_2x(sources['sources'][n], sources, sources['base_palette'])[0] for n in names]
        boxes = [im.getbbox() for im in images]
        crop2 = [min(b[0] for b in boxes) - 4, min(b[1] for b in boxes) - 4,
                 max(b[2] for b in boxes) + 4, max(b[3] for b in boxes) + 4]
        cell = [(crop2[2] - crop2[0]) // 2, (crop2[3] - crop2[1]) // 2]
        budget, _, columns, rows, envelope = best_grid(count, *cell)
        native = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
        outline = Image.new('RGB', native.size, 'white')
        for i, im in enumerate(images):
            cropped = im.crop(crop2)
            reconstructed = Image.new('RGBA', im.size)
            reconstructed.paste(cropped, tuple(crop2[:2]))
            assert np.array_equal(np.asarray(im), np.asarray(reconstructed)), names[i]
            xy = (i % columns * cropped.width, i // columns * cropped.height)
            native.paste(cropped, xy)
            inside = np.asarray(cropped.getchannel('A'))[::2, ::2] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[boundary] = 0
            outline.paste(Image.fromarray(guide).resize(cropped.size, Image.Resampling.NEAREST), xy)
        native_path = wo / 'references/fidget_0_sheet_native.png'
        outline_path = wo / 'references/fidget_0_sheet_outline.png'
        native.save(native_path)
        outline.save(outline_path)
        # Material crops carry detail without presenting a competing full-body silhouette.
        identity = Image.open(old / 'cleaned' / (names[0] + '.png')).convert('RGBA')
        b = identity.getbbox()
        identity = identity.crop(b)
        iw, ih = identity.size
        materials = Image.new('RGB', (900, 620), (35, 43, 38))
        d = ImageDraw.Draw(materials)
        patch_specs = [(.15, 0, .85, .27, 'Face / head material'),
                       (.15, .28, .85, .57, 'Torso material and native costume'),
                       (.12, .6, .88, .9, 'Lower materials / equipment finish'),
                       (.55, .25, 1, .65, 'Equipment / surface detail')]
        for i, (x0, y0, x1, y1, label) in enumerate(patch_specs):
            patch = identity.crop((int(x0 * iw), int(y0 * ih), int(x1 * iw), int(y1 * ih)))
            patch.thumbnail((435, 275), Image.Resampling.LANCZOS)
            x, y = i % 2 * 450, i // 2 * 310
            materials.paste(patch, (x + (450 - patch.width) // 2, y + 27), patch)
            d.text((x + 8, y + 7), label + ' — appearance only', fill='white')
        material_path = wo / 'references/fidget_0_sheet_materials.png'
        materials.save(material_path)
        refs = [native_path, outline_path, material_path]
        prompt_path = wo / 'prompts/fidget_0_sheet_v1.txt'
        anatomical = ('Retain the native shoulder/elbow/wrist/finger and hip/knee/ankle/toe relationships, body mass, head size, costume folds, equipment grips and original fidget steps.')
        if family == 'spi1':
            anatomical = 'Preserve all EIGHT native spider legs, every segment and bend, exact near/far ownership and foot locations, the cephalothorax/abdomen relationship and native fang/head movement. Do not alter leg count or flatten the native leg arch.'
        specific = {
            'mnk1': 'The lower navy robe has a NARROW native hem and a tapered silhouette. At native size its planted lower hem is about 70 pixels wide for about 257 pixels height: do not broaden it into an 88-pixel cylindrical skirt. Keep its lower contour and rope belt placement stable; preserve the small native upper-body/head fidget only. The face remains concealed black shadow.',
            'cle': 'The native lower cloak contour and ground contacts stay nearly fixed. Do not invent wind-driven cape flutter, a changing hem width, a new staff length or moving planted feet. Preserve the actual native head and hand movements.',
            'ske': 'The native feet and lower leg stance stay fixed apart from any small explicit native contour change. Do not invent a foot turn, a new stride or alternating toe angles. Preserve the thin bone anatomy and exact native hand/equipment movement.',
            'dwa1': 'Keep the short native leg proportions, planted boot contacts and spacing fixed across the fidget. The beard, helmet and equipment must retain their native size and ownership. No widening stance or changing boot design between cells.',
            'min1': 'Retain the exact native bovine/humanoid body proportions, horn shapes, equipment and heavy native anatomy. Both planted feet and lower-leg stance remain stable; do not invent a step or widen/re-angle the feet between cells.',
            'wfigt1': 'Preserve the native werewolf identity, costume and limb lengths. Keep the planted foot positions, stance width and lower body fixed while reproducing the native fidget movement. Do not slide the entire character between rows or cells.',
            'arc1': 'Preserve the native bow hand/grip, string, quiver and straps. Keep the planted feet and leg proportions stable. Reproduce every original head/arm/bow movement without shifting the whole body.',
            'mer1': 'Keep the same native merchant face, hair, tunic, belt, leg proportions and planted feet in every cell. Preserve the actual mouth/expression fidget; do not replace it with a different character or broaden the shoulders between cells.',
            'spi1': 'Match the foot and leg contacts in EACH supplied native cell. Do not independently recenter the body or move the outer legs merely to fit the grid.'
        }[family]
        repeated = [n for i, n in enumerate(names) if n in names[:i]]
        if repeated:
            specific += ' Native held steps repeat the SAME bitmap: ' + ', '.join(repeated) + '. Their repeated cells must show the identical pose and geometry, not an invented movement. Native playback will retain that exact repeated hold.'
        prompt = '\n\n'.join([CONTEXT,
            f'Generate exactly ONE COMPLETE {config["title"]} FIDGET animation sheet: all {count} original chronological steps, {columns} columns × {rows} rows, row-major order {", ".join(names)}. Include the FIRST pose on this sheet even when its native bitmap is also reused by another action. Return precisely one RGBA image containing the complete cycle.',
            f'Image 1 is untouched native colour and alpha for ALL {count} poses and is the authority for pose, anatomy, proportions, costume coverage, equipment, camera, placement, animation movement and base colour. Image 2 is its matching separate OUTLINE-ONLY geometry guide: thin black boundaries and white interior/exterior encode geometry only. Never copy outline strokes, grooves, contour bands or the white background into the result. Image 3 contains detailed material crops from the same family, for finish only; do not infer body proportions or poses from those crops.',
            'Character: ' + config['description'], anatomical + ' ' + specific,
            'Keep one consistent detailed painted/pre-rendered fantasy-game character across the entire cycle. Preserve fine facial or bone detail, cloth weave and natural folds, hair/fur/scales, leather grain, seams, metal wear and equipment detail where native. Retain native tonal weight and natural shading. No waxy smoothing, washed-out contrast, artificial shading bands, heavy dark grooves, blur, pixel blocks, dither, sharpened halos or noisy invented surface patterns.',
            f'Use one common native-coordinate crop {[v / 2 for v in crop2]}, cell {cell}, actor canvas {sources["logical_canvas"]}. Each cell must have the same scale and coordinate origin; no per-cell centering, zoom or silhouette fitting. Preserve the first native pose AND all {count - 1} subsequent fidget poses as one coherent generation. Use the native outline to keep stationary feet or robe hem stationary throughout the cycle, while retaining all genuine native head, torso, arm and equipment movement.',
            f'Generate only base palette {sources["base_palette"]} as shown by Image 1. Recolour variants will be derived separately. Keep 2 NATIVE pixels of transparent safety padding, full fingers, toes, horns, bowstrings and equipment tips. Aim for at least 2.2× actual detail, preferably 2.6×, requested master {math.ceil(columns * cell[0] * 2.6)} × {math.ceil(rows * cell[1] * 2.6)} or larger. Whole-cycle completeness takes priority over sampling; never split it. Exactly one complete transparent RGBA sheet, no grid, labels, ground, cast shadow, paper, gradient or painted checkerboard.'
        ])
        prompt_path.write_text(prompt + '\n')
        job = {'id': 'fidget_0_sheet', 'action': 'fidget', 'view': 0, 'frames': names,
               'bindings': [{'action': 'fidget', 'view': int(v), 'native_frames': names} for v in all_views],
               'native_sequence': True, 'native_crop': [v / 2 for v in crop2], 'cell_native_size': cell,
               'columns': columns, 'rows': rows, 'observed_envelope': list(envelope), 'planned_sampling': budget,
               'references': [rel(p) for p in refs], 'reference_roles': ['untouched_native_complete_animation', 'outline_only_geometry_no_shading', 'same_family_detailed_material_crops'],
               'prompt': rel(prompt_path), 'attempts': [], 'selected_raw': None, 'status': 'prepared',
               'prepared_assets': [{'path': rel(p), 'sha256': sha(p)} for p in refs + [prompt_path]]}
        write(wo / 'run.json', {'source_project': rel(old.parent), 'project': rel(work), 'method': METHOD, 'padding_native_px': 2, 'status': 'prepared', 'jobs': [job]})
        write(wo / 'processing.json', {'preserve_matte_hued_materials': True, 'supplied_alpha_noise_floor': 0,
              'whole_animation_resolution_policy': DEFAULT_POLICY, 'connected_body_extraction_jobs': ['fidget_0_sheet']})
        other = {step['frame'] for action, animation in manifest['animations'].items() if action != 'fidget' for steps in animation['views'].values() for step in steps}
        shared = sorted(set(names) & other)
        entry = {'family': family, 'label': selected['label'], 'project': rel(root), 'work_project': rel(work),
                 'source_package': rel(old), 'source_selection': selected, 'frames': names, 'shared_native_frames': shared,
                 'enhanced_aliases': {n + '__fidget_0': n for n in shared}, 'status': 'prepared',
                 'source_hashes': {str(p.relative_to(old)): sha(p) for p in old.rglob('*') if p.is_file()}}
        queue['families'].append(entry)
        write(queue_path, queue)
        # Inspect the actual reference pair at native-size or larger, plus material crops.
        contact = Image.new('RGB', (1600, 1150), (35, 43, 38))
        d = ImageDraw.Draw(contact)
        for i, ref in enumerate([native, outline]):
            im = ref.copy(); im.thumbnail((785, 775), Image.Resampling.NEAREST)
            x = i * 800; contact.paste(im, (x, 28), im if im.mode == 'RGBA' else None)
            d.text((x + 5, 5), selected['label'] + (' untouched native' if i == 0 else ' OUTLINE ONLY'), fill='white')
        mat = materials.copy(); mat.thumbnail((540, 360), Image.Resampling.LANCZOS)
        contact.paste(mat, (530, 790))
        contact.save(wo / 'review/fidget_reference_inputs.png')
        print(selected['label'], count, 'poses', f'{columns}x{rows}', 'native cell', cell, 'shared source IDs', shared)
    write(queue_path, queue)


def entries(families=None):
    return [e for e in read(HERE / 'repairs.json')['families'] if not families or e['family'] in families]


def native_image(root, name):
    s = read(root / 'sources.json')
    return native_2x(s['sources'][name], s, s['base_palette'])[0]


def footprint(im, scale, family=None):
    mask = np.asarray(im.getchannel('A')) >= 128
    ys, xs = np.where(mask)
    bottom = int(ys.max())
    if family == 'cle':
        from annotate_packed_body import points
        cap = points(im, scale)['body_cap']
        xx = np.arange(mask.shape[1])
        mask[:, np.abs(xx - cap[0]) > (bottom - cap[1]) * .25] = False
        bottom = int(np.where(mask)[0].max())
    low = mask[max(0, bottom - round(7 * scale)):bottom + 1]
    yy, xx = np.where(low)
    return [(int(xx.min()) + int(xx.max())) / 2, float(bottom)], [int(xx.min()), int(xx.max())]


def process(families):
    import extract_run
    from annotate_packed_body import annotate
    from register_packed_outline import register
    # The shared extractor's 1x diagnostic rejects half-pixel anchors. Generate its
    # diagnostic from an exact 2x native reference; all registration/export uses 2x.
    original_native = extract_run.native
    extract_run.native = lambda root, name: native_image(root, name).resize(
        tuple(read(root / 'sources.json')['logical_canvas']), Image.Resampling.NEAREST)
    try:
        for e in entries(families):
            root = REPO / e['work_project']; out = root / 'redo_2x'
            policy = read(out / 'processing.json')
            policy['supplied_alpha_noise_floor'] = 8
            policy['alpha_noise_review'] = 'Remove only reviewed near-transparent alpha <=8 background speckles and bridges; preserve silhouette cores, thin features and exact half-pixel native coordinates.'
            write(out / 'processing.json', policy)
            extract_run.extract(e['work_project'], ['fidget_0_sheet'])
            report = read(out / 'review/fidget_0_sheet_extraction.json')
            for row in report['frames']:
                row['native_bounds'] = [v / 2 for v in native_image(root, row['frame']).getbbox()]
            write(out / 'review/fidget_0_sheet_extraction.json', report)
            annotate(e['work_project'], job_ids=['fidget_0_sheet'])
            policy = read(out / 'processing.json')
            calibration = policy['anatomical_sheet_calibration']['fidget_0_sheet']
            p = calibration['landmarks']; first, second = [p[k] for k in calibration['scale_pair']]
            sampling = (second['clean'][1] - first['clean'][1]) / (second['native'][1] - first['native'][1])
            seen = set()
            for row in report['frames']:
                name = row['frame']
                if name in seen:
                    continue
                seen.add(name)
                clean_path = REPO / row['clean_path']; clean = Image.open(clean_path).convert('RGBA')
                npnt, nw = footprint(native_image(root, name), 2, e['family'])
                cpnt, cw = footprint(clean, sampling, e['family'])
                policy['frame_translation_calibration'][name] = dict(
                    raw_sha256=report['raw_sha256'], clean_sha256=sha(clean_path), axes=[0, 1],
                    landmark='planted_footprint_midpoint_and_contact', native=[v / 2 for v in npnt], clean=cpnt,
                    method='Translate the entire pose to its native planted-foot or hem contact midpoint. Retain ONE common first-pose anatomical scale for the whole returned cycle; no deformation, per-pose resizing or copied limbs.',
                    unfitted_native_contact_width=(nw[1] - nw[0]) / 2,
                    unfitted_generated_contact_width=(cw[1] - cw[0]) / sampling)
            write(out / 'processing.json', policy)
            register(e['work_project'])
            reg = read(out / 'registration.json')
            print(e['family'], 'contact widths', [(n, round(r['translation_calibration']['unfitted_native_contact_width'], 2), round(r['translation_calibration']['unfitted_generated_contact_width'], 2)) for n, r in reg.items()])
    finally:
        extract_run.native = original_native


def candidate_export(families):
    from export_run import export
    import package_family
    for e in entries(families):
        root = REPO / e['work_project']; out = root / 'redo_2x'
        inventory = read(root / 'inventory.json'); original = read(root / 'manifest.json')
        run = read(out / 'run.json')
        saved = [copy.deepcopy(x) for x in (inventory, original, run)]
        # The shared whole-family packager reads standing to label its contacts and
        # native scale. Supply a temporary diagnostic alias in this fidget-only
        # scratch project; it is never shipped or written into native source data.
        for variant in inventory[e['family']]['variants'].values():
            variant['actions']['standing'] = copy.deepcopy(variant['actions']['fidget'])
        original['animations']['standing'] = copy.deepcopy(original['animations']['fidget'])
        original['animations']['standing'].update(playback='loop', next_action=None)
        for palette, actions in original['animations_by_palette'].items():
            actions['standing'] = copy.deepcopy(actions['fidget'])
            actions['standing'].update(playback='loop', next_action=None)
        run['jobs'][0]['bindings'].extend(dict(b, action='standing') for b in list(run['jobs'][0]['bindings']))
        write(root / 'inventory.json', inventory); write(root / 'manifest.json', original); write(out / 'run.json', run)
        full_family_contacts = package_family.make_contacts
        # Its fixed contact order requires actions outside the authorized scope.
        # Use the same atlas exporter and the actual fidget-only contacts below.
        package_family.make_contacts = lambda *args: None
        try:
            export(e['work_project'], with_viewer=False)
        finally:
            package_family.make_contacts = full_family_contacts
            write(root / 'inventory.json', saved[0]); write(root / 'manifest.json', saved[1]); write(out / 'run.json', saved[2])
        m = read(out / 'manifest.json')
        m['animations'].pop('standing', None)
        for actions in m['animations_by_palette'].values(): actions.pop('standing', None)
        m['native_group_bindings'] = saved[0][e['family']]['variants']
        write(out / 'manifest.json', m)
        contacts(e, out)


def atlas_tile(out, m, name, palette=None, mask=False):
    f = m['frames'][name]; page = m['pages'][f['page']]
    path = page['mask'] if mask else page['base'] if palette is None else page['variant_previews'][str(palette)]
    x, y, w, h = f['atlas_xywh']
    return Image.open(out / path).crop((x, y, x + w, y + h))


def aligned_from_atlas(out, m, name, palette=None):
    f = m['frames'][name]; im = Image.new('RGBA', tuple(f['aligned_canvas_size_px']))
    im.paste(atlas_tile(out, m, name, palette), tuple(f['crop_in_aligned_px'][:2]))
    return im


def contacts(e, out):
    m = read(out / 'manifest.json'); reg = read(out / 'registration.json')
    work = REPO / e['work_project']; names = e['frames']
    aliases = {native: alias for alias, native in e['enhanced_aliases'].items()}
    names2 = [aliases.get(n, n) if aliases.get(n, n) in m['frames'] else n for n in names]
    canvas = m['logical_canvas']; w, h = canvas
    # Native at exact 2x coordinates, restored at physical 2x, all chronological
    # steps including the exact repeated native holds. No size normalization.
    sheet = Image.new('RGB', (w * 2 * 3, (h * 4 + 44) * 2), (38, 45, 40)); d = ImageDraw.Draw(sheet)
    for i, (native_name, name) in enumerate(zip(names, names2)):
        x, y = i % 3 * w * 2, i // 3 * (h * 4 + 44)
        im = native_image(work, native_name); sheet.paste(im, (x, y + 22), im)
        enhanced = aligned_from_atlas(out, m, name); origin = m['frames'][name]['aligned_canvas_origin_px']
        sheet.paste(enhanced, (x + origin[0], y + h * 2 + 34 + origin[1]), enhanced)
        d.text((x + 4, y + 3), f'{i+1}: {native_name} / complete-return pose', fill='white')
        npoint, _ = footprint(im, 2, e['family']); rpoint, _ = footprint(enhanced, 2, e['family'])
        for px, py, color in [(npoint[0], npoint[1] + y + 22, 'cyan'), (rpoint[0] + origin[0], rpoint[1] + y + h * 2 + 34 + origin[1], 'orange')]:
            d.ellipse((x + px - 3, py - 3, x + px + 3, py + 3), outline=color, width=1)
    sheet.save(out / 'review/fidget_native_restored_2x.png')
    # Every palette and material-mask pose, at native logical size (no enlargement).
    pals = list(m['variants']); contact = Image.new('RGB', (w * 6, (h + 24) * (len(pals) + 1)), (38, 45, 40)); d = ImageDraw.Draw(contact)
    for row, pal in enumerate(pals + [None]):
        for i, name in enumerate(names2):
            im = aligned_from_atlas(out, m, name, pal)
            if pal is None:
                f = m['frames'][name]; mask = Image.new(atlas_tile(out, m, name, mask=True).mode, tuple(f['aligned_canvas_size_px']))
                mask.paste(atlas_tile(out, m, name, mask=True), tuple(f['crop_in_aligned_px'][:2]))
                import package_family
                im = package_family.overlay(im, mask)
            im = im.convert('RGBa').resize((round(im.width / 2), round(im.height / 2)), Image.Resampling.LANCZOS).convert('RGBA')
            origin = m['frames'][name]['aligned_canvas_origin_px']
            contact.paste(im, (i * w + round(origin[0] / 2), row * (h + 24) + 20 + round(origin[1] / 2)), im)
            d.text((i * w + 4, row * (h + 24) + 3), (f'Palette {pal}' if pal else 'Mask overlay') + f' — step {i+1}', fill='white')
    contact.save(out / 'review/fidget_palettes_masks.png')
    # 100% generated material crops and worst actual exported edge on light/dark.
    edge = read(out / 'review/edge_current.json')
    worst = sorted(set(names2), key=lambda n: edge['frames'].get(n, edge['frames'].get(e['enhanced_aliases'].get(n, n), {})).get('atlas_extracted', {}).get('candidates_above_16', 0), reverse=True)
    panel = Image.new('RGB', (1800, 850), (38, 45, 40)); d = ImageDraw.Draw(panel)
    report = read(work / 'redo_2x/review/fidget_0_sheet_extraction.json')
    for i, r in enumerate(report['frames']):
        im = Image.open(REPO / r['clean_path']).convert('RGBA'); b = im.getbbox()
        patch = im.crop((max(0, (b[0] + b[2]) // 2 - 140), b[1], min(im.width, (b[0] + b[2]) // 2 + 140), min(im.height, b[1] + 290)))
        panel.paste(patch, (i * 300, 24), patch); d.text((i * 300 + 4, 4), f'Step {i+1}: generated pixels 100%', fill='white')
    for i, name in enumerate(worst[:3]):
        tile = atlas_tile(out, m, name).convert('RGBA'); box = tile.getbbox()
        patch = tile.crop((max(0, box[0] - 4), max(0, box[3] - 180), min(tile.width, box[0] + 280), min(tile.height, box[3] + 4)))
        for side, bg in enumerate([(245,245,245), (14,16,18)]):
            x, y = i * 600 + side * 300, 350
            panel.paste(bg, (x, y, x + 295, y + 200)); panel.paste(patch, (x, y), patch)
            d.text((x + 3, y + 210), name + ' alpha / ' + ('light' if side == 0 else 'dark'), fill='white')
    panel.save(out / 'review/fidget_detail_edges_100percent.png')


def normalized_native(m):
    result = copy.deepcopy(m)
    aliases = result.get('enhanced_appearance_aliases', {})
    for actions in [result['animations']] + list(result['animations_by_palette'].values()):
        for action, animation in actions.items():
            for view, steps in animation['views'].items():
                for step in steps:
                    name = step['frame']
                    if name in aliases:
                        assert action == 'fidget', 'Scoped aliases are only authorized for fidget'
                        native = aliases[name]
                        assert native in result['frames']
                        assert result['frames'][name]['native_source_frame'] == native
                        assert result['frames'][name]['source'] == result['frames'][native]['source']
                        step['frame'] = native
    return result


def assemble(families):
    from exact_placement import validate_manifest, validate_animation_bindings
    from whole_animation_resolution import validate_policy, record_detail_policy
    for e in entries(families):
        root = REPO / e['project']; out = root / 'redo_2x'; wo = REPO / e['work_project'] / 'redo_2x'
        old = REPO / e['source_package']; m = read(old / 'manifest.json'); cm = read(wo / 'manifest.json')
        cr = read(wo / 'registration.json'); reg = read(old / 'registration.json'); run = read(old / 'run.json')
        for n, row in reg.items():
            if 'clean_path' not in row:
                path = old / 'cleaned' / (n + '.png')
                if 'clean_sha256' in row: assert sha(path) == row['clean_sha256']
                row['clean_path'] = rel(path); row['clean_sha256'] = sha(path)
                row['scope_provenance_note'] = 'Older accepted registration omitted clean-path fields; bind the unchanged canonical cleaned asset explicitly.'
        assert not any(r['raw_clip'] for r in cr.values())
        assert len(read(wo / 'review/fidget_0_sheet_extraction.json')['frames']) == len(e['frames'])
        assert cm['recolor_model'] == m['recolor_model']
        native_to_alias = {n: a for a, n in e['enhanced_aliases'].items()}
        newid = 'fidget_0_sheet_repair_20261003'
        def cp(source, target):
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target); assert sha(source) == sha(target)
        def copied_path(value):
            if not isinstance(value, str): return value
            source = Path(value)
            if not source.is_absolute(): source = REPO / source
            if not source.is_file() or not source.is_relative_to(wo): return value
            part = source.relative_to(wo)
            if part.parts[0] not in ('raw', 'prompts', 'references', 'review'): return value
            target = out / part.parts[0] / 'fidget_repair' / Path(*part.parts[1:])
            cp(source, target); return rel(target)
        def remap(value):
            if isinstance(value, dict): return {k: remap(v) for k, v in value.items()}
            if isinstance(value, list): return [remap(v) for v in value]
            return copied_path(value)
        cj = remap(read(wo / 'run.json')['jobs'][0]); cj['id'] = newid
        cj['bindings'] = [b for b in cj['bindings'] if b['action'] == 'fidget']
        run['jobs'] = [j for j in run['jobs'] if j['id'] != newid] + [cj]
        run['status'] = 'pending_fidget_visual_acceptance'; run['method'] = METHOD
        offset = len(m['pages']); page_map = {}
        for i, page in enumerate(cm['pages']):
            page = copy.deepcopy(page)
            def page_asset(path):
                if path not in page_map:
                    part = Path(path); target = out / part.parent / ('fidget_repair_' + part.name)
                    cp(wo / path, target); page_map[path] = str(target.relative_to(out))
                return page_map[path]
            for k in ('base', 'mask', 'mask_overlay'):
                if k in page: page[k] = page_asset(page[k])
            page['variant_previews'] = {p: page_asset(path) for p, path in page['variant_previews'].items()}
            m['pages'].append(page)
        changed = []
        for name, r in cr.items():
            target = native_to_alias.get(name, name); changed.append(target)
            for folder in ('aligned_2x', 'masks_2x', 'trimmed_2x', 'trimmed_masks_2x'):
                cp(wo / folder / (name + '.png'), out / folder / (target + '.png'))
            cp(REPO / r['clean_path'], out / 'cleaned' / newid / (name + '.png'))
            cp(REPO / r['clean_path'], out / 'cleaned' / (target + '.png'))
            r = copy.deepcopy(r); r['batch'] = newid; r['generated_frame'] = name; r['native_source_frame'] = name
            r['raw_path'] = copied_path(r['raw_path']); r['clean_path'] = rel(out / 'cleaned' / newid / (name + '.png'))
            r['clean_sha256'] = sha(REPO / r['clean_path']); reg[target] = r
            f = copy.deepcopy(cm['frames'][name]); f['page'] += offset; f['native_source_frame'] = name
            assert f['native_offset'] == m['frames'][name]['native_offset']
            if target != name: f['enhanced_appearance_scope'] = 'fidget; canonical native appearance retained for other actions'
            m['frames'][target] = f
            for palette in m['variants']:
                cp(wo / 'native_variants' / f'{name}_{palette}.png', out / 'native_variants' / f'{target}_{palette}.png')
        if cm.get('recolor_presets'):
            presets = copy.deepcopy(cm['recolor_presets'])
            presets['frames'] = {native_to_alias.get(n,n): p for n,p in presets['frames'].items()}
            if m.get('recolor_presets'):
                m['recolor_presets']['frames'].update(presets['frames'])
                m['recolor_presets']['presets'].update(presets['presets'])
                m['recolor_presets']['reason'] += '\n' + presets['reason']
            else: m['recolor_presets'] = presets
            m['recolor']['preset_selection'] = 'Use frames[frame].recolor_preset when present; otherwise use family vectors.'
            m['recolor']['runtime'] = 'Palette atlases are baked with these presets. Dynamic recoloring requires per-frame preset support; staged only.'
            write(out / 'recolor_presets.json', m['recolor_presets'])
        for actions in [m['animations']] + list(m['animations_by_palette'].values()):
            for steps in actions['fidget']['views'].values():
                for step in steps: step['frame'] = native_to_alias.get(step['frame'], step['frame'])
        m['enhanced_appearance_aliases'] = e['enhanced_aliases']
        m['native_animations_by_palette'] = read(old / 'manifest.json')['animations_by_palette']
        m['generated_detail']['measured_minimum'] = min(min(r['effective_sampling_xy']) for r in reg.values() if not r.get('empty_native_endpoint'))
        record_detail_policy(m, DEFAULT_POLICY, reg)
        m['generated_detail']['fidget_repair_minimum'] = min(min(cr[n]['effective_sampling_xy']) for n in cr)
        m['quality_status'] = 'pending_fidget_visual_acceptance'; m.pop('review_record', None)
        pixels = sum(p['size'][0] * p['size'][1] for p in m['pages'])
        masks = sum(p['size'][0] * p['size'][1] * (4 if p['mask_format'] == 'RGBA8' else 1) for p in m['pages'])
        mem = m['memory_bytes']; mem['enhanced_atlas_base'] = pixels * 4; mem['enhanced_shared_base_and_mask'] = pixels * 4 + masks
        mem['enhanced_atlas_mask_rgba8' if m['pages'][0]['mask_format'] == 'RGBA8' else 'enhanced_atlas_mask_r8'] = masks
        mem['enhanced_tight_base_unique'] = sum(f['atlas_xywh'][2] * f['atlas_xywh'][3] * 4 for f in m['frames'].values())
        mem['preserved_old_atlas_pages_include_superseded_fidget_tiles'] = True
        processing = read(old / 'processing.json'); processing['whole_animation_resolution_policy'] = DEFAULT_POLICY
        policy = remap(read(wo / 'processing.json'))
        processing.setdefault('anatomical_sheet_calibration', {})[newid] = policy['anatomical_sheet_calibration']['fidget_0_sheet']
        for n, row in policy['frame_translation_calibration'].items():
            processing.setdefault('frame_translation_calibration', {})[native_to_alias.get(n, n)] = row
        processing['fidget_repair'] = dict(method=METHOD, enhanced_appearance_aliases=e['enhanced_aliases'],
            common_scale_only=True, complete_pose_translation_only=True, alpha_noise_floor=8,
            source_package=e['source_package'], source_artifact_sha256=e['source_selection']['artifact_sha256'])
        if policy.get('enhanced_material_guides'):
            processing.setdefault('enhanced_material_guides', {}).update({native_to_alias.get(n,n):g for n,g in policy['enhanced_material_guides'].items()})
            module = REPO / e['work_project'] / 'materials.py'
            target = out / 'references/fidget_repair/materials.py'; cp(module, target)
            processing['fidget_repair']['material_coverage_module'] = dict(path=rel(target),sha256=sha(target),reason='Enhanced fidget material coverage only; inherited artwork and material functions unchanged.')
        calibration = read(old / 'calibration.json'); calibration[newid] = remap(read(wo / 'calibration.json')['fidget_0_sheet'])
        generation = read(old / 'generation.json'); cg = read(wo / 'generation.json')['batches']['fidget_0_sheet']
        def asset_record(a):
            source = (wo / a['path']).resolve(); target_path = copied_path(rel(source)); target = REPO / target_path
            assert sha(target) == a['sha256']; return dict(a, path=os.path.relpath(target, out))
        generation['batches'][newid] = dict(raw=asset_record(cg['raw']), prompt=asset_record(cg['prompt']), references=[asset_record(a) for a in cg['references']])
        audit = read(old / 'review/edge_current.json'); ca = read(wo / 'review/edge_current.json')
        for n, row in ca['frames'].items(): audit['frames'][native_to_alias.get(n, n)] = row
        write(out / 'review/edge_current.json', audit)
        preserved = sorted(set(m['frames']) - set(changed))
        for n in preserved:
            assert m['frames'][n] == read(old / 'manifest.json')['frames'][n]
            for folder in ('aligned_2x', 'masks_2x', 'cleaned'):
                assert sha(out / folder / (n + '.png')) == sha(old / folder / (n + '.png')), (e['family'], n, folder)
        for name, digest in e['source_hashes'].items(): assert sha(old / name) == digest, 'Changed source project: ' + name
        original = read(old / 'manifest.json')
        for palette, actions in m['animations_by_palette'].items():
            for action, anim in actions.items():
                if action != 'fidget': assert anim == original['animations_by_palette'][palette][action]
        assert m['native_group_bindings'] == original['native_group_bindings']
        assert not validate_manifest(m, reg)
        assert not validate_animation_bindings(normalized_native(m))
        validate_policy(DEFAULT_POLICY, run, normalized_native(m), reg)
        validation = read(old / 'validation.json'); validation['visual_review_complete'] = False
        validation.update(enhanced_appearance_count=len(m['frames']), native_source_files=len(read(root / 'sources.json')['sources']),
                          out_of_scope_art_and_animations_unchanged=True, enhanced_alias_contract_verified=True,
                          exact_native_anchors_verified=True, complete_fidget_return_verified=True, memory_bytes=mem)
        for filename, data in [('manifest.json',m),('registration.json',reg),('processing.json',processing),('run.json',run),('calibration.json',calibration),('generation.json',generation),('validation.json',validation)]: write(out / filename, data)
        # Root manifest is the expected enhanced representation; untouched native
        # identities are explicit above and in original native_group_bindings.
        write(root / 'manifest.json', m)
        write(out / 'review/fidget_scope.json', dict(action='fidget', changed_enhanced_frames=changed,
            original_native_sequence=e['frames'], enhanced_appearance_aliases=e['enhanced_aliases'],
            preserved_frame_ids=preserved, source_package=e['source_package'], source_hashes=e['source_hashes'],
            source_native_group_bindings_sha256=hashlib.sha256(json.dumps(original['native_group_bindings'],sort_keys=True).encode()).hexdigest(),
            diagnostic_export_alias_never_shipped=True, all_other_actions_and_pixels_verified_unchanged=True))
        contacts(e, out); finished_sheets(e, out)
        print(e['label'], 'assembled pending review;', len(changed), 'enhanced poses;', len(preserved), 'unchanged')


def feature(im, family):
    a = np.asarray(im).astype(float); alpha = a[:,:,3] >= 128
    yy, xx = np.where(alpha); x0,x1,y0,y1 = xx.min(),xx.max(),yy.min(),yy.max()
    height = y1-y0; axis = (x0+x1)/2
    from annotate_packed_body import points
    if family != 'spi1': axis = points(im, 2)['body_cap'][0]
    red, green, blue = [a[:,:,i] for i in range(3)]
    y,x = np.indices(alpha.shape)
    if family == 'mnk1':
        allowed = (np.abs(red-green)<18)&(np.abs(green-blue)<18)&(red>70)&(y>y0+height*.32)&(y<y0+height*.57)
        label = 'rope belt horizontal join'
    elif family == 'mer1':
        allowed = (np.abs(red-green)<9)&(np.abs(green-blue)<9)&(red>40)&(y>y0+height*.46)&(y<y0+height*.60)
        label = 'grey waist belt band'
    elif family == 'arc1':
        allowed = (blue>green*1.18)&(green>red*1.05)&(y>y0+height*.09)&(y<y0+height*.27)
        label = 'blue throat band'
    elif family == 'dwa1':
        allowed = (red>green*1.10)&(green>blue*1.20)&(red>85)&(y>y0+height*.70)&(y<y0+height*.86)&(x<axis-height*.06)&(x>axis-height*.23)
        label = 'left boot cuff'
    elif family == 'cle':
        allowed = (red>green*1.10)&(green>blue*1.20)&(red>85)&(y>y0+height*.36)&(y<y0+height*.66)
        label = 'waist buckle / belt'
    elif family == 'min1':
        eyes = alpha & (red>green*1.8)&(red>blue*2)&(red>60)&(y<y0+height*.23)
        ey,ex=np.where(eyes); assert len(ex), 'Locate actual red eyes independently of axe/horns'
        axis=float(np.median(ex))
        allowed = (blue>red*1.2)&(blue>green*1.05)&(blue>60)&(y>y0+height*.18)&(y<y0+height*.33)&(np.abs(x-axis)<height*.055)
        label = 'blue collar gem'
    elif family == 'wfigt1':
        allowed = (green>red*1.4)&(blue>red*1.3)&(green>55)&(y>y0+height*.1)&(y<y0+height*.38)
        label = 'pendant gem'
    elif family == 'spi1':
        allowed = (red>green*2)&(red>blue*2)&(red>95)
        label = 'red eye cluster'
    else:
        allowed = (y>y0+height*.43)&(y<y0+height*.58)
        label = 'central lumbar / pelvic bridge'
    allowed &= alpha
    if family != 'dwa1': allowed &= np.abs(x-axis)<height*(.08 if family not in ('spi1','ske') else .12)
    fy,fx = np.where(allowed); assert len(fx), (family,label,'no actual feature pixels')
    if family in ('mnk1','mer1','arc1','cle'):
        profile = np.bincount(fy,minlength=im.height); row=int(np.argmax(profile)); close=np.abs(fy-row)<=2
        fy,fx=fy[close],fx[close]
    center=np.array([np.median(fx),np.median(fy)]); idx=int(np.argmin((fx-center[0])**2+(fy-center[1])**2))
    return label,[int(fx[idx]),int(fy[idx])]


def independent_contacts(families):
    for e in entries(families):
        out=REPO/e['project']/'redo_2x';work=REPO/e['work_project'];m=read(out/'manifest.json')
        job=read(work/'redo_2x/run.json')['jobs'][0];crop2=[round(v*2) for v in job['native_crop']];w,h=crop2[2]-crop2[0],crop2[3]-crop2[1]
        contact=Image.new('RGB',(w*3,(h*2+32)*2),(38,45,40));d=ImageDraw.Draw(contact);rows=[]
        steps=m['animations']['fidget']['views']['0']
        for i,(n,step) in enumerate(zip(e['frames'],steps)):
            original=native_image(work,n); restored=aligned_from_atlas(out,m,step['frame']);origin=m['frames'][step['frame']]['aligned_canvas_origin_px']
            label,npnt=feature(original,e['family']);_,rpnt=feature(restored,e['family']);x=i%3*w;y=i//3*(h*2+32)
            ni=original.crop(crop2);container=Image.new('RGBA',original.size);container.paste(restored,tuple(origin));ri=container.crop(crop2)
            for im,point,yoff,color in [(ni,npnt,22,'cyan'),(ri,[rpnt[0]+origin[0],rpnt[1]+origin[1]],h+28,'orange')]:
                contact.paste(im,(x,y+yoff),im);px=x+point[0]-crop2[0];py=y+yoff+point[1]-crop2[1]
                d.ellipse((px-4,py-4,px+4,py+4),outline=color,width=2)
            d.text((x+3,y+3),f'{i+1}: {label}',fill='white')
            residual=[(rpnt[a]+origin[a]-npnt[a])/2 for a in range(2)]
            rows.append(dict(frame=step['frame'],native_source=n,feature=label,native=[v/2 for v in npnt],restored=[(rpnt[a]+origin[a])/2 for a in range(2)],residual_native_px=residual,used_for_transform=False))
        contact.save(out/'review/fidget_independent_features_2x.png')
        scope=read(out/'review/fidget_scope.json');scope['independent_feature_candidates']=rows
        write(out/'review/fidget_scope.json',scope)
        print(e['family'],[(r['frame'],r['residual_native_px']) for r in rows])


def accept(families):
    import freeze_review
    from exact_placement import validate_animation_bindings
    from whole_animation_resolution import validate_policy
    original_bindings,original_policy=freeze_review.validate_animation_bindings,freeze_review.validate_policy
    freeze_review.validate_animation_bindings=lambda m: validate_animation_bindings(normalized_native(m))
    freeze_review.validate_policy=lambda p,r,m,reg: validate_policy(p,r,normalized_native(m),reg)
    try:
        for e in entries(families):
            root=REPO/e['project'];out=root/'redo_2x';m=read(out/'manifest.json');scope=read(out/'review/fidget_scope.json')
            assert scope.get('independent_features_visually_reviewed') is True, 'Inspect the marked actual feature on every pose first'
            evidence={f'review/{f}.png':sha(out/'review'/(f+'.png')) for f in ['fidget_native_restored_2x','fidget_palettes_masks','fidget_detail_edges_100percent','fidget_independent_features_2x']}
            if (out/'review/fidget_palette_detail_100percent.png').exists():
                evidence['review/fidget_palette_detail_100percent.png']=sha(out/'review/fidget_palette_detail_100percent.png')
            evidence['review/fidget_scope.json']=sha(out/'review/fidget_scope.json')
            artifacts={str(p.relative_to(out)):sha(p) for folder in ('aligned_2x','masks_2x','atlas','finished_sheets_2x') for p in (out/folder).glob('*.png')}
            decision=dict(status='accepted_after_visual_review',review_mode='static_contacts',
                method='Reviewed every newly generated fidget pose, actual native-coordinate placement and independently marked anatomical/material feature, generated 100% material crops, light/dark alpha edges, every baked palette and coverage-mask pose. All other artwork and native actions are inherited unchanged from the exact original accepted package; full source hash and pixel/metadata retention checked. Whole complete-sheet generation including shared first poses; no isolated-pose generation or copied limbs. Static contacts only; no claim of watched playback.',
                reviewed_manifest_sha256=sha(out/'manifest.json'),reviewed_frames=sorted(m['frames']),
                newly_reviewed_frames=scope['changed_enhanced_frames'],inherited_review_frames=scope['preserved_frame_ids'],
                checks=dict(faithful_detail=True,poses_and_placement=True,edges_and_alpha=True,masks_and_variants=True),
                whole_animation_resolution_policy=DEFAULT_POLICY,evidence_artifacts=evidence,reviewed_artifact_hashes=artifacts,
                scoped_alias_validator=dict(path=rel(Path(__file__)),sha256=sha(Path(__file__)),contract='Explicit fidget-only enhanced appearances normalize to original source IDs; native groups/timing/mirrors/scales checked by unchanged shared validator. Physical placement checked on actual enhanced frames.'),
                inherited_acceptance=dict(path=rel(REPO/e['source_package']/'review/acceptance.json'),sha256=sha(REPO/e['source_package']/'review/acceptance.json')))
            write(out/'review/decision.json',decision)
            freeze_review.freeze(e['project'])
            record=read(out/'review/acceptance.json')
            for path,digest in record['artifact_hashes'].items():assert sha(out/path)==digest,path
            queue=read(HERE/'repairs.json');entry=next(x for x in queue['families'] if x['family']==e['family']);entry['status']='accepted_staged_fidget_only';entry['fidget_sampling_minimum']=m['generated_detail']['fidget_repair_minimum'];entry['acceptance_sha256']=sha(out/'review/acceptance.json');write(HERE/'repairs.json',queue)
    finally:
        freeze_review.validate_animation_bindings=original_bindings;freeze_review.validate_policy=original_policy


def finished_sheets(e, out):
    m = read(out / 'manifest.json'); names = [s['frame'] for s in m['animations']['fidget']['views']['0']]
    rect = [min(m['frames'][n]['crop_origin_px'][a] for n in names) for a in range(2)]
    rect += [max(m['frames'][n]['crop_origin_px'][a] + m['frames'][n]['atlas_xywh'][a+2] for n in names) for a in range(2)]
    cw, ch = rect[2]-rect[0], rect[3]-rect[1]
    folder = out / 'finished_sheets_2x'; folder.mkdir(exist_ok=True); records = []
    for palette in m['variants']:
        sheet = Image.new('RGBA', (cw * 3, ch * 2))
        for i, n in enumerate(names):
            im = atlas_tile(out, m, n, palette); xy = m['frames'][n]['crop_origin_px']
            sheet.paste(im, (i%3*cw + xy[0]-rect[0], i//3*ch + xy[1]-rect[1]))
        path = folder / f'fidget_0_palette_{palette}.png'; sheet.save(path)
        records.append(dict(path=str(path.relative_to(out)),sha256=sha(path),palette=int(palette),action='fidget',view=0,
                            frames=names,columns=3,rows=2,cell_physical_size=[cw,ch],common_native_crop=[v/2 for v in rect]))
    write(folder / 'fidget_layout.json', dict(pixels_per_logical_pixel=2,sheets=records,native_sequence=e['frames'],native_timing_and_mirrors_preserved=True))


def atomic_json(path, data, expected=None):
    import tempfile
    path=Path(path)
    with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as stream:
        json.dump(data,stream,indent=2,ensure_ascii=False);stream.write('\n');temporary=Path(stream.name)
    if expected is not None and path.read_bytes()!=expected:
        temporary.unlink();return False
    os.replace(temporary,path);return True


def sync_checkpoints(records):
    from datetime import datetime,timezone
    path=COLLECTION/'review_state/frame_fixups.json'
    for attempt in range(10):
        raw=path.read_bytes();state=json.loads(raw);original=copy.deepcopy(state);migrations=[]
        for e,selected in records:
            family=selected['creature'].replace(':','_');versions=state['families'].setdefault(family,{})
            old_digest=e['source_selection']['artifact_sha256'];new_digest=selected['artifact_sha256']
            source=versions.get(old_digest,{'revision':0,'frames':{}})
            if new_digest in versions:
                current=versions[new_digest];migration=current.get('fidget_repair_migration',{})
                if migration.get('source_revision',-1)>=source['revision']:continue
                assert current['revision']==migration.get('created_revision'), 'Concurrent edits on both old and new art require explicit reconciliation'
            target=copy.deepcopy(source);out=REPO/e['project']/'redo_2x';scope=read(out/'review/fidget_scope.json')
            changed=set(scope['changed_enhanced_frames'])
            for key in ('frames','landmarks'):
                target[key]={n:value for n,value in target.get(key,{}).items() if n not in changed}
            target.update(revision=source['revision']+1,updated_at=datetime.now(timezone.utc).isoformat(),
                label=selected['label'],manifest_path=str(out/'manifest.json'),manifest_sha256=selected['manifest_sha256'],
                artifact_sha256=new_digest,pixels_per_logical_pixel=2,
                fidget_repair_migration=dict(source_artifact_sha256=old_digest,source_revision=source['revision'],
                    created_revision=source['revision']+1,reset_only_changed_fidget_appearances=sorted(changed),
                    shared_native_canonical_edits_retained_for_other_actions=True))
            versions[new_digest]=target
            for n,row in source.get('frames',{}).items():
                if n not in changed:assert target['frames'][n]==row
            migrations.append(dict(family=family,source_revision=source['revision'],new_revision=target['revision'],
                retained_frame_proposals=len(target['frames']),reset_changed_fidget_proposals=sorted(set(source.get('frames',{}))&changed)))
        for family,versions in original['families'].items():
            for digest,row in versions.items():assert state['families'][family][digest]==row
        if atomic_json(path,state,raw):
            return migrations
    raise RuntimeError('Review proposals kept changing; no file was overwritten. Retry the scoped publication.')


def publication_records(families):
    sys.path.insert(0,str(REPO/'level_generation/creatures/mm6_remaining/acceptance_viewer'))
    from serve import load_family
    result=[]
    for e in entries(families):
        assert e['status']=='accepted_staged_fidget_only'
        out=REPO/e['project']/'redo_2x';m=read(out/'manifest.json');record=copy.deepcopy(e['source_selection'])
        family=load_family(e['label'],out/'manifest.json','Packed outline','manual_review_pending')
        record.update(manifest=os.path.relpath(out/'manifest.json',COLLECTION),manifest_sha256=family.manifest_sha256,
            artifact_sha256=family.artifact_sha256,frame_count=len(m['frames']),palette_ids=list(m['variants']),
            source='Packed outline',pipeline_status='manual_review_pending',source_pipeline_status='validated',
            minimum_generated_sampling=m['generated_detail']['measured_minimum'],
            aligned_masters_2x=os.path.relpath(out/'aligned_2x',COLLECTION),material_masks_2x=os.path.relpath(out/'masks_2x',COLLECTION))
        assert not record['video_finish'], 'An existing video finish needs a separate declared migration'
        metadata=['sources.json','config.json','recolor_vectors.json','registration.json','processing.json','calibration.json',
            'run.json','generation.json','materials.py','validation.json','review/acceptance.json','review/fidget_scope.json','review/decision.json']
        if (out/'recolor_presets.json').exists():metadata+=['recolor_presets.json','references/fidget_repair/materials.py']
        record['rebuild_metadata']={name:dict(path=os.path.relpath(out/name,COLLECTION),sha256=sha(out/name)) for name in metadata if (out/name).is_file()}
        raw_sheets={}
        for n,row in read(out/'registration.json').items():
            raw_path=(REPO/row['raw_path']).resolve();item=raw_sheets.setdefault(str(raw_path),dict(path=os.path.relpath(raw_path,COLLECTION),
                sha256=sha(raw_path),registered_frames=[]));assert item['sha256']==row['raw_sha256'];item['registered_frames'].append(n)
        record['selected_raw_sheets']=list(raw_sheets.values())
        record['finished_sheets_2x']=[s for s in record.get('finished_sheets_2x',[]) if s.get('action')!='fidget']
        for sheet in read(out/'finished_sheets_2x/fidget_layout.json')['sheets']:
            item=copy.deepcopy(sheet);item['path']=os.path.relpath(out/sheet['path'],COLLECTION);record['finished_sheets_2x'].append(item)
        record['fidget_repair']=dict(action='fidget',native_steps=6,minimum_generated_sampling=m['generated_detail']['fidget_repair_minimum'],
            enhanced_appearance_aliases=m.get('enhanced_appearance_aliases',{}),all_other_actions_and_pixels_unchanged=True)
        result.append((e,record))
    return result


def publish(families, sync_only=False):
    from collections import Counter
    sys.path.insert(0,str(REPO/'level_generation/creatures/mm6_remaining/acceptance_viewer'))
    from landmarks import source_signature,validate_landmarks
    records=publication_records(families)
    if sync_only:
        print(json.dumps(sync_checkpoints(records)));return
    path=COLLECTION/'collection.json';raw=path.read_bytes();collection=json.loads(raw);original=copy.deepcopy(collection)
    replacements={r['creature']:r for _,r in records}
    for e,r in records:
        previous=next(x for x in collection['families'] if x['creature']==r['creature'])
        assert previous==e['source_selection'], 'Another session changed this selected family; reconcile before publishing'
    collection['families']=[replacements.get(r['creature'],r) for r in collection['families']]
    collection['frame_count']=sum(r['frame_count'] for r in collection['families'])
    assert collection['family_count']==len(collection['families'])==60
    for r in original['families']:
        if r['creature'] not in replacements:assert next(x for x in collection['families'] if x['creature']==r['creature'])==r
    write(HERE/'collection_before.json',original)
    migrations=sync_checkpoints(records)
    seeds=read(COLLECTION/'landmarks/seeds.json')
    for e,r in records:
        out=REPO/e['project']/'redo_2x';m=read(out/'manifest.json');scope=read(out/'review/fidget_scope.json')
        target=COLLECTION/'landmarks'/(r['creature'].replace(':','_')+'.json')
        if not target.exists():continue
        cached=read(target);cached['frames']={n:points for n,points in cached['frames'].items() if n not in scope['changed_enhanced_frames']}
        validate_landmarks({n:{side:{kind:p['xy'] for kind,p in points.items()} for side,points in sides.items()}
                           for n,sides in cached['frames'].items()},m)
        counts=Counter(f'{side}:{kind}' for sides in cached['frames'].values() for side,points in sides.items() for kind in points)
        cached.update(artifact_sha256=r['artifact_sha256'],manifest_sha256=r['manifest_sha256'],
            source_signature=source_signature(out,seeds.get(r['creature'],{})),
            coverage=dict(frames_with_points=len(cached['frames']),total_frames=len(m['frames']),points=dict(sorted(counts.items()))))
        atomic_json(target,cached)
    assert atomic_json(path,collection,raw), 'Collection changed during publication; checkpoint history remains preserved'
    write(HERE/'publication.json',dict(status='published_pending_human_review',collection_manifest=rel(path),
        affected_families=[r['creature'] for _,r in records],unchanged_other_family_count=51,
        unchanged_native_source_projects=True,all_other_actions_and_pixels_verified_unchanged=True,
        family_count=60,frame_count=collection['frame_count'],review_checkpoint_migrations=migrations,
        local_acceptance_complete=True,human_review_pending=True))
    print('Published',len(records),'fidget-only repairs;',collection['frame_count'],'enhanced appearances; 51 other families retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['prepare', 'process', 'export', 'assemble', 'features', 'accept', 'publish', 'sync'])
    parser.add_argument('families', nargs='*')
    args = parser.parse_args()
    if args.operation == 'prepare': prepare()
    elif args.operation == 'process': process(args.families)
    elif args.operation == 'export': candidate_export(args.families)
    elif args.operation == 'assemble': assemble(args.families)
    elif args.operation == 'features': independent_contacts(args.families)
    elif args.operation == 'accept': accept(args.families)
    elif args.operation == 'publish': publish(args.families)
    elif args.operation == 'sync': publish(args.families,sync_only=True)
