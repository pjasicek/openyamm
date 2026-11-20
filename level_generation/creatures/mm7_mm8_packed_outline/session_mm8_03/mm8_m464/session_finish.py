"""Compose existing MM8 export tools with packed-sheet checkpoints; never certify visual acceptance."""
import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree

from session_prepare import REPO, CREATURES, STAGE, STEMS, read, save, native_2x

sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from extract_run import extract
from annotate_packed_body import annotate
from register_packed_outline import register


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_and_cloth(image, native_scale=1):
    pixels = np.array(image)
    rgb = pixels[:, :, :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    solid = pixels[:, :, 3] >= 128
    warm = solid & (r > g * 1.38) & (r - b > 25) & (g > b * 1.6)
    labels, count = ndimage.label(ndimage.binary_closing(warm, iterations=max(1, round(native_scale / 2))))
    if not count:
        return None
    sizes = np.bincount(labels.ravel()); sizes[0] = 0
    head = warm & (labels == sizes.argmax())
    cloth = solid & (g > np.maximum(r, b) * 1.1)
    if not head.any() or not cloth.any():
        return None
    return {key: [float(xs.mean()), float(ys.mean())]
            for key, mask in [('head_material_center', head), ('garment_center', cloth)]
            for ys, xs in [np.where(mask)]}


def fall_calibration(root, jobs):
    """MM8 m464's separated warm hair and green clothing supply visible fall landmarks."""
    out = root / 'redo_2x'; sources = read(root / 'sources.json'); p = read(out / 'processing.json')
    owners = {}
    for job in jobs:
        for name in job['frames']:
            owners.setdefault(name, job['id'])
    for job in jobs:
        if not (job['action'] in ['death', 'corpse'] or job['id'].startswith('unused_d_')):
            continue
        report = read(out / 'review' / (job['id'] + '_extraction.json'))
        first = report['frames'][0]; points = {}
        for side in ['native', 'clean']:
            image = (native_2x(sources['sources'][first['frame']], sources, sources['base_palette'])[0]
                     if side == 'native' else Image.open(REPO / first['clean_path']).convert('RGBA'))
            found = head_and_cloth(image, 2 if side == 'native' else 3)
            if not found:
                break
            for label, point in found.items():
                points.setdefault(label, {})[side] = [v / 2 for v in point] if side == 'native' else point
        if not points or any(set(pair) != {'native', 'clean'} for pair in points.values()):
            continue
        p.setdefault('anatomical_sheet_calibration', {})[job['id']] = dict(
            frame=first['frame'], raw_sha256=report['raw_sha256'],
            clean_sha256=sha(REPO / first['clean_path']), landmarks=points,
            scale_pair=['head_material_center', 'garment_center'], axes=[0, 1], anchor='head_material_center',
            method='Candidate corresponding warm head/hair and green garment material centers set one common scale for the complete fall sheet. Every marked feature and independent limb/prop placement still require visual review.')
        for frame in report['frames']:
            name = frame['frame']; clean_path = REPO / frame['clean_path']
            if owners[name] != job['id']:
                continue
            native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
            clean = Image.open(clean_path).convert('RGBA')
            npnt, cpnt = head_and_cloth(native, 2), head_and_cloth(clean, 3)
            if npnt and cpnt:
                p.setdefault('frame_translation_calibration', {})[name] = dict(
                    raw_sha256=report['raw_sha256'], clean_sha256=sha(clean_path), axes=[0, 1],
                    landmark='candidate_head_material_center',
                    native=[v / 2 for v in npnt['head_material_center']], clean=cpnt['head_material_center'],
                    method='Candidate whole-pose translation from the corresponding head/hair material center in native coordinates; the complete animation retains one uniform scale. Independent garment, hand, foot and equipment features remain pending visual review.')
    for job in jobs:
        override = p.get('anatomical_sheet_calibration_overrides', {}).get(job['id'])
        if override:
            p['anatomical_sheet_calibration'][job['id']] = override
            anchor = override['landmarks'][override['anchor']]
            p['frame_translation_calibration'][override['frame']] = dict(
                raw_sha256=override['raw_sha256'], clean_sha256=override['clean_sha256'],
                axes=[0, 1], landmark=override['anchor'], native=anchor['native'], clean=anchor['clean'],
                method=override['method'])
    save(out / 'processing.json', p)


def process(stem):
    root = STAGE / f'mm8_m{stem}'; out = root / 'redo_2x'; run = read(out / 'run.json')
    jobs = [j for j in run['jobs'] if j.get('selected_raw')]
    p = read(out / 'processing.json'); correction = STAGE / 'mm8_m464/session_edge_rgb.py'
    eligible = [j['id'] for j in jobs if not (stem == 472 and j['action'] in ['attack', 'fidget'])
                and not (stem == 492 and j['action'] == 'attack')]
    p['base_color_correction'] = dict(module=str(correction.relative_to(root)) if stem == 464 else
        '../mm8_m464/session_edge_rgb.py', sha256=sha(correction), jobs=eligible,
        reason='Reviewed 100% light-background before/after contacts: only alpha 1–96 fringe RGB within four raw pixels of alpha>=128 is corrected when chroma differs by >70 and saturation spans >=80. Alpha and every opaque material pixel stay exact. Native spell/effect jobs are excluded.')
    failures = {}
    for job in jobs:
        attempt = next(a for a in job['attempts'] if a.get('raw') == job['selected_raw'])
        refs = attempt['actual_tool_arguments']['referenced_image_paths']
        assert len(refs) >= 2 and '_outline' in Path(refs[1]).name
        assert [r['path'] for r in attempt['references']] == refs
        assert all(sha(Path(r['path'])) == r['sha256'] for r in attempt['references'])
        raw = REPO / job['selected_raw']; assert sha(raw) == attempt['sha256']
        a = np.array(Image.open(raw).convert('RGBA').getchannel('A'))
        threshold = 4
        for candidate in [4, 8, 16, 32, 64]:
            sizes = np.bincount(ndimage.label(a > candidate)[0].ravel()); sizes[0] = 0
            major = int((sizes > sizes.max() * .1).sum())
            if major == len(job['frames']):
                threshold = candidate
                break
        key = 'connected_body_extraction_jobs' if major == len(job['frames']) else 'component_grid_extraction_jobs'
        for other in ['connected_body_extraction_jobs', 'component_grid_extraction_jobs']:
            p[other] = [x for x in p.get(other, []) if x != job['id']]
        p[key].append(job['id'])
        p.setdefault('component_seed_alpha_threshold_by_job', {})[job['id']] = dict(
            threshold=threshold, raw_sha256=sha(raw), reason='The lowest tested seed threshold yielding one substantial connected body per requested pose separates faint bridges only for ownership. All delivered alpha, effects and thin foreground pixels are retained exactly once; actual pose separation remains visually reviewable.')
    save(out / 'processing.json', p)
    for job in jobs:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                extract(str(root.relative_to(REPO)), [job['id']])
        except Exception as e:
            failures[job['id']] = f'{type(e).__name__}: {e}'
    good = [j for j in jobs if j['id'] not in failures]
    with contextlib.redirect_stdout(io.StringIO()):
        annotate(str(root.relative_to(REPO)), True, [j['id'] for j in good])
    if stem == 464:
        fall_calibration(root, good)
    with contextlib.redirect_stdout(io.StringIO()):
        register(str(root.relative_to(REPO)))
    # Reused canonical bitmaps must not hide a later returned pose from visual review.
    records = read(out / 'registration.json'); p = read(out / 'processing.json')
    candidates = []
    for job in good:
        if not any(records[n]['raw_path'] != job['selected_raw'] for n in job['frames']):
            continue
        with tempfile.TemporaryDirectory(prefix='.pose_review_', dir=root) as directory:
            temp = Path(directory); redo = temp / 'redo_2x'; (redo / 'review').mkdir(parents=True)
            for name in ['sources.json', 'config.json']:
                shutil.copy2(root / name, temp / name)
            save(redo / 'run.json', dict(run, jobs=[job])); save(redo / 'processing.json', p)
            shutil.copy2(out / 'review' / (job['id'] + '_extraction.json'), redo / 'review')
            with contextlib.redirect_stdout(io.StringIO()):
                annotate(str(temp.relative_to(REPO)), True, [job['id']])
                if stem == 464:
                    fall_calibration(temp, [job])
                register(str(temp.relative_to(REPO)))
            source = redo / 'review' / (job['id'] + '_registered.png')
            shutil.copy2(source, out / 'review' / (job['id'] + '_actual_return_registered.png'))
            candidates.append(job['id'])
    p['extraction_failures'] = failures
    save(out / 'processing.json', p)
    # Compact contacts preserve native logical pixel size and show every currently extracted pose.
    contacts = []
    for job in good:
        suffix = '_actual_return_registered.png' if job['id'] in candidates else '_registered.png'
        image = Image.open(out / 'review' / (job['id'] + suffix)).convert('RGB')
        panel = Image.new('RGB', (image.width, image.height + 24), '#292d2e')
        ImageDraw.Draw(panel).text((4, 4), f'{stem}: {job["id"]}; NATIVE / ACTUAL RETURN, candidate placement', fill='white')
        panel.paste(image, (0, 24)); contacts.append(panel)
    for start in range(0, len(contacts), 4):
        group = contacts[start:start + 4]
        page = Image.new('RGB', (max(im.width for im in group), sum(im.height for im in group)), '#292d2e')
        y = 0
        for image in group:
            page.paste(image, (0, y)); y += image.height
        page.save(out / 'review' / f'complete_pose_candidates_{start//4:02d}.png')
    print(json.dumps(dict(stem=stem, extracted_jobs=len(good), frames=len(records),
                         missing=len(read(root/'sources.json')['sources'])-len(records),
                         failures=failures, actual_return_contacts=candidates,
                         review_pages=(len(contacts)+3)//4, acceptance='pending_visual_review')))


def export_candidate(stem):
    sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
    sys.path.insert(0, str(CREATURES))
    import native_materials as materials
    import native_package as package
    from exact_placement import native_offset, export_placement, validate_manifest
    root = STAGE / f'mm8_m{stem}'; out = root / 'redo_2x'
    sources = read(root / 'sources.json'); records = read(out / 'registration.json')
    assert set(records) <= set(sources['sources']), 'Unknown registered native frame'
    available = set(records)
    missing = sorted(set(sources['sources']) - available)
    p = read(out / 'processing.json')
    previous = CREATURES / f'mm8_m{stem}/redo_2x/processing.json'
    policies = read(previous).get('materials') if previous.exists() else None
    defaults = {
        484: dict(regions=['native palette-dependent woven skirt'],
                  protected='Red-brown fur, horn roots/tips, eyes, silver/red axe blades, shaft, brass fittings, leather harness and cuffs.',
                  support={}),
        488: dict(regions=['green wrap skirt'],
                  protected='Black/white pelt, skin, face, horns, hooves, rope belt and wrist wraps.',
                  support=dict(green_excess=[0, 8])),
        492: dict(regions=[], protected='One native palette: the complete dragon is fixed colour.', support={})}
    p['materials'] = policies or defaults[stem]; save(out / 'processing.json', p)
    shutil.copy2(root / 'sources.json', out / 'sources.json')
    materials.ROOT = out; materials.PALETTES = list(map(int, sources['palette_sources']))
    config = materials.settings()
    if stem == 464:
        config['warm_component'].update(red_green_ratio=1.38, green_blue_ratio=1.60,
            red_blue_minimum=15, maximum_hole_area=16,
            region='Enhanced brown hair within a coarse native head-region box; RGB classification supplies coverage, never resized native indices.')
        config['enhanced_mask_refinement'] = 'Select enhanced brown hair with the pale-skin-protecting warm classifier inside a coarse native head-region box with three logical pixels of margin. Fill enclosed coverage gaps up to 512 physical pixels at threshold .25, confined to opaque enhanced hair. Native indices supply only a bounding region; enhanced RGB supplies coverage. Separate boot/garment fasteners stay protected. All hair variants require visual review.'
    if stem == 472:
        config['enhanced_mask_refinement'] = 'Classify enhanced green robe symbols within the opaque body and map their painted luma to native garment palette RGB per base luma. Protect the coarse native invariant neon-effect bounding region in attack/fidget poses, enlarged by twelve logical pixels; no native pixel mask transfer. Original generated RGB and alpha remain unchanged; all palette poses require review.'
    if stem in [472, 488]:
        native_palettes = {key: np.frombuffer((REPO / value['path']).read_bytes()[:768], np.uint8).reshape(256, 3).astype(float)
                           for key, value in sources['palette_sources'].items()}
        base = native_palettes[str(sources['base_palette'])]
        cloth_indices = np.where((base[:, 1] > np.maximum(base[:, 0], base[:, 2])*1.4) &
                                 (np.array([False]+config['changed_samples']) > 0))[0]
        luma = base[cloth_indices] @ np.array([.2126, .7152, .0722])
        config['garment_rgb_per_base_luma'] = {key: np.median(value[cloth_indices] / np.maximum(luma[:, None], 1), axis=0).tolist()
                                             for key, value in native_palettes.items()}
    if stem == 488:
        config['enhanced_mask_refinement'] = 'Classify green and cyan painted wrap-skirt shades in a coarse native garment bounding region, using enhanced RGB for every mask value. Recolour that material using the native skirt palette RGB per base luma; retain painted shading and weave. Protect grayscale pelt, horns, hooves, skin and brown rope. No native spatial mask transfer.'
        native_palettes = {key: np.frombuffer((REPO / value['path']).read_bytes()[:768], np.uint8).reshape(256, 3).astype(float)
                           for key, value in sources['palette_sources'].items()}
        base = native_palettes[str(sources['base_palette'])]
        cloth_indices = np.where((base[:, 1] > np.maximum(base[:, 0], base[:, 2])*1.4) &
                                 (np.array([False]+config['changed_samples']) > 0))[0]
        luma = base[cloth_indices] @ np.array([.2126, .7152, .0722])
        config['garment_rgb_per_base_luma'] = {key: np.median(value[cloth_indices] / np.maximum(luma[:, None], 1), axis=0).tolist()
                                             for key, value in native_palettes.items()}
    if stem == 480:
        native_palettes = {key: np.frombuffer((REPO / value['path']).read_bytes()[:768], np.uint8).reshape(256, 3).astype(float)
                           for key, value in sources['palette_sources'].items()}
        base = native_palettes[str(sources['base_palette'])][1:]
        base_luma = base @ np.array([.2126, .7152, .0722])
        def chroma_features(rgb):
            luma = np.maximum(rgb @ np.array([.2126, .7152, .0722]), 5)
            return np.stack(((rgb[..., 0]-rgb[..., 1])/luma,
                             (rgb[..., 2]-rgb[..., 1])/luma, .035*np.log(luma)), axis=-1)
        chroma_tree = cKDTree(chroma_features(base))
        hair_indices = np.arange(139, 156)
        hair_base_luma = native_palettes[str(sources['base_palette'])][hair_indices] @ np.array([.2126, .7152, .0722])
        config['hair_rgb_per_base_luma'] = {key: np.median(value[hair_indices] / np.maximum(hair_base_luma[:, None], 1), axis=0).tolist()
                                           for key, value in native_palettes.items()}
        config['enhanced_mask_refinement'] = 'Native palette chromaticity neighbors supply material colours and coverage; painted luma supplies fine shading. Hair receives its native grey/black mapping within a coarse bounding box of the largest connected native hair-colour region, with two logical pixels of margin; enhanced warm RGB with a red/green upper bound of 2.05 supplies every coverage value. A soft coarse native head-skin ellipse protects the bald forehead inside short hair boxes. Red bone club, ivory tips and claws stay protected. No native spatial mask transfer. All poses require visual review.'
        config['chroma_features'] = ['(R-G)/max(luma,5)', '(B-G)/max(luma,5)', '.035*log(max(luma,5))']
        config['chroma_distance_floor'] = .015
        config['hair_indices_for_coarse_region'] = hair_indices.tolist()
    if stem == 484:
        config['enhanced_mask_refinement'] = 'Retain the largest connected skirt colour region and its three-pixel soft transition; separate similarly coloured axe fittings are protected. Every pose remains pending material-mask review.'
    save(out / 'material_settings.json', config)
    for folder in ['toned_2x', 'masks_2x', 'previews', 'native_variants', 'palettes']:
        (out / folder).mkdir(exist_ok=True)
    unique = {name: record for name, record in records.items() if name not in sources['pixel_aliases']}
    original_warm_coverage = materials.warm_coverage
    for name, record in unique.items():
        image = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
        if stem == 464:
            indexed = np.asarray(Image.open(REPO / sources['sources'][name]['path']))
            yy, xx = np.where(np.isin(indexed, config['warm_component']['palette_indices']))
            origin = record['canvas_origin_px']
            box = ([int(2*(xx.min()-3)-origin[0]), int(2*(yy.min()-3)-origin[1]),
                    int(2*(xx.max()+4)-origin[0]), int(2*(yy.max()+4)-origin[1])]
                   if len(xx) else [0, 0, 0, 0])
            def head_warm_coverage(pixels, settings, box=box):
                selected = pixels.copy()
                selected[:, :, 3] = 0
                x0, y0 = max(0, box[0]), max(0, box[1])
                x1, y1 = min(pixels.shape[1], box[2]), min(pixels.shape[0], box[3])
                selected[y0:y1, x0:x1, 3] = pixels[y0:y1, x0:x1, 3]
                coverage = original_warm_coverage(selected, settings)
                filled = ndimage.binary_fill_holes(coverage > .25)
                labels, count = ndimage.label(filled & (coverage <= .25))
                sizes = np.bincount(labels.ravel())
                enclosed = (labels > 0) & (sizes[labels] <= 512) & (selected[:, :, 3] > 128)
                return np.maximum(coverage, ndimage.gaussian_filter(enclosed.astype(float), .45))
            materials.warm_coverage = head_warm_coverage
        weights = materials.masks(image, config)
        if stem == 472:
            pixels = np.asarray(image); rgb = pixels[:, :, :3].astype(float)
            body = ndimage.binary_opening(pixels[:, :, 3] >= 240, iterations=3)
            labels, count = ndimage.label(body)
            if count:
                sizes = np.bincount(labels.ravel()); sizes[0] = 0
                body = ndimage.binary_dilation(ndimage.binary_fill_holes(labels == sizes.argmax()), iterations=1)
            strength = np.clip((rgb[:, :, 1]-np.maximum(rgb[:, :, 0], rgb[:, :, 2]))/8, 0, 1)*body
            weights = np.round(ndimage.gaussian_filter(strength, .45)*255).astype(np.uint8)
        if stem == 472 and record['batch'].split('_')[0] in ['attack', 'fidget']:
            rgb = np.asarray(image)[:, :, :3].astype(float)
            green = rgb[:, :, 1]
            emission_guard = np.minimum(np.clip((190-green)/50, 0, 1),
                np.clip((.55-rgb[:, :, 2]/np.maximum(green, 1))/.20, 0, 1))
            logical_y = (np.arange(rgb.shape[0]) + record['canvas_origin_px'][1]) / 2
            emission_guard[logical_y >= 180] = 1
            indexed = np.asarray(Image.open(REPO / sources['sources'][name]['path']))
            invariant = np.all(np.stack(list(native_palettes.values())) == base, axis=(0, 2))
            neon = (((base[:, 1] > 120) & (base[:, 1] > base[:, 0]*1.3)) |
                    ((base[:, 2] > 140) & (base[:, 2] > base[:, 0]*1.5))) & invariant
            neon[0] = False
            yy, xx = np.where(neon[indexed])
            if len(xx):
                origin = record['canvas_origin_px']
                x0, y0 = max(0, int(2*(xx.min()-12)-origin[0])), max(0, int(2*(yy.min()-12)-origin[1]))
                x1, y1 = min(weights.shape[1], int(2*(xx.max()+13)-origin[0])), min(weights.shape[0], int(2*(yy.max()+13)-origin[1]))
                emission_guard[y0:y1, x0:x1] = 0
            weights = np.round(weights * emission_guard).astype(np.uint8)
        if stem == 488:
            indexed = np.asarray(Image.open(REPO / sources['sources'][name]['path']))
            yy, xx = np.where(np.isin(indexed, cloth_indices))
            origin = record['canvas_origin_px']
            support = np.zeros(weights.shape, bool)
            if len(xx):
                x0, y0 = max(0, int(2*(xx.min()-24)-origin[0])), max(0, int(2*(yy.min()-24)-origin[1]))
                x1, y1 = min(weights.shape[1], int(2*(xx.max()+25)-origin[0])), min(weights.shape[0], int(2*(yy.max()+25)-origin[1]))
                support[y0:y1, x0:x1] = True
            rgb = np.asarray(image)[:, :, :3].astype(float)
            red, green, blue = np.moveaxis(rgb, -1, 0)
            strength = np.minimum(np.clip((green-red-3)/5, 0, 1), np.clip((green-blue+45)/10, 0, 1)) * support
            strength[np.asarray(image)[:, :, 3] == 0] = 0
            weights = np.round(ndimage.gaussian_filter(strength, .45)*255).astype(np.uint8)
        if stem == 480:
            pixels = np.asarray(image); rgb = pixels[:, :, :3].astype(float)
            distances, neighbors = chroma_tree.query(chroma_features(rgb).reshape(-1, 3), k=8)
            neighbor_weights = 1/np.maximum(distances, .015)**4
            neighbor_weights /= neighbor_weights.sum(axis=1, keepdims=True)
            selected = neighbor_weights*np.array(config['changed_samples'])[neighbors]
            coverage = selected.sum(axis=1).reshape(rgb.shape[:2])
            indexed = np.asarray(Image.open(REPO / sources['sources'][name]['path']))
            labels, count = ndimage.label(ndimage.binary_closing(np.isin(indexed, hair_indices), iterations=1))
            hair = np.zeros(coverage.shape)
            if count:
                sizes = np.bincount(labels.ravel()); sizes[0] = 0
                yy, xx = np.where(labels == sizes.argmax()); origin = record['canvas_origin_px']
                x0, y0 = max(0, int(2*(xx.min()-2)-origin[0])), max(0, int(2*(yy.min()-2)-origin[1]))
                x1, y1 = min(hair.shape[1], int(2*(xx.max()+3)-origin[0])), min(hair.shape[0], int(2*(yy.max()+3)-origin[1]))
                support = np.zeros(hair.shape); support[y0:y1, x0:x1] = 1
                # A coarse head-skin ellipse protects the bald forehead inside the hair box.
                # Native pixels locate only the region; no indexed spatial mask is transferred.
                if yy.max()-yy.min() < 40:
                    native_rgb = native_palettes[str(sources['base_palette'])][indexed]
                    bare = (indexed < 139) & (indexed > 0) & (native_rgb[:, :, 0] > native_rgb[:, :, 1]*1.35)
                    bounded = np.zeros(bare.shape, bool)
                    bounded[yy.min():yy.max()+1, xx.min():xx.max()+1] = True
                    skin_labels, skin_count = ndimage.label(bare & bounded)
                    if skin_count:
                        skin_sizes = np.bincount(skin_labels.ravel()); skin_sizes[0] = 0
                        if skin_sizes.max() >= 20:
                            sy, sx = np.where(skin_labels == skin_sizes.argmax())
                            cy, cx = (sy.min()+sy.max())/2, (sx.min()+sx.max())/2
                            ry, rx = (sy.max()-sy.min()+4)/2, (sx.max()-sx.min()+3)/2
                            py, px = np.indices(support.shape)
                            ellipse = ((px+origin[0])/2-cx)**2/rx**2 + ((py+origin[1])/2-cy)**2/ry**2
                            support *= np.clip((ellipse-1)*4, 0, 1)
                red, green, blue = np.moveaxis(rgb, -1, 0)
                hair = np.minimum(np.clip((red-green-5)/10, 0, 1), np.clip((green-blue-5)/10, 0, 1))*np.clip((2.05-red/np.maximum(green, 1))/.10, 0, 1)*support
                hair[pixels[:, :, 3] == 0] = 0
                hair = ndimage.gaussian_filter(hair, .45)
            coverage[pixels[:, :, 3] == 0] = 0
            weights = np.round(np.maximum(coverage, hair)*255).astype(np.uint8)
        if stem == 484:
            seeds = ndimage.binary_closing(weights >= 64, iterations=2)
            labels, count = ndimage.label(seeds)
            if count:
                sizes = np.bincount(labels.ravel()); sizes[0] = 0
                support = ndimage.binary_dilation(labels == sizes.argmax(), iterations=3)
                weights[~support] = 0
        image.save(out / 'toned_2x' / (name + '.png'))
        mask = Image.fromarray(weights); mask.save(out / 'masks_2x' / (name + '.png'))
        for palette in materials.PALETTES:
            variant = materials.recolor(image, mask, palette, config)
            if stem == 480 and palette != sources['base_palette']:
                pixels = np.array(image); rgb = pixels[:, :, :3].astype(float)
                luma = rgb @ np.array([.2126, .7152, .0722])
                ratios = native_palettes[str(palette)][1:]/np.maximum(base_luma[:, None], 1)
                target = (ratios[neighbors]*selected[:, :, None]).sum(axis=1)/np.maximum(selected.sum(axis=1)[:, None], 1e-9)
                target = target.reshape(rgb.shape)*luma[:, :, None]
                result = rgb*(1-coverage[:, :, None])+target*coverage[:, :, None]
                result = result*(1-hair[:, :, None])+luma[:, :, None]*np.array(config['hair_rgb_per_base_luma'][str(palette)])*hair[:, :, None]
                pixels[:, :, :3] = np.round(result).clip(0, 255)
                variant = Image.fromarray(pixels)
            if stem in [472, 488] and palette != sources['base_palette']:
                pixels = np.array(image); rgb = pixels[:, :, :3].astype(float)
                luma = rgb @ np.array([.2126, .7152, .0722])
                target = luma[:, :, None] * np.array(config['garment_rgb_per_base_luma'][str(palette)])
                coverage = weights[:, :, None] / 255
                pixels[:, :, :3] = np.round(rgb*(1-coverage)+target*coverage).clip(0, 255)
                variant = Image.fromarray(pixels)
            assert np.array_equal(np.asarray(variant)[:, :, 3], np.asarray(image)[:, :, 3])
            if palette == sources['base_palette']:
                assert np.array_equal(variant, image)
            variant.save(out / 'previews' / f'{name}_{palette}.png')
            materials.queue.native(out, name, palette).save(out / 'native_variants' / f'{name}_{palette}.png')
        record.update(aligned_size_px=list(image.size), logical_size=sources['logical_canvas'],
                      native_offset=native_offset(sources['logical_canvas'], sources['sources'][name]['size']))
    materials.warm_coverage = original_warm_coverage
    save(out / 'registration.json', unique)
    package.ROOT = out
    if missing:
        packing_sources = copy.deepcopy(sources)
        packing_sources['sources'] = {n:s for n,s in sources['sources'].items() if n in available}
        packing_sources['pixel_aliases'] = {n:c for n,c in sources['pixel_aliases'].items() if n in available and c in available}
        packing_sources['bindings'] = {}
        save(out / 'sources.json', packing_sources)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            package.run()
    finally:
        save(out / 'sources.json', sources)
    manifest = read(out / 'draft_manifest.json'); canvas = sources['logical_canvas']
    manifest.update(logical_canvas=canvas, logical_pivot=sources['logical_pivot'], anchor='bottom-center',
                    method=read(out / 'run.json')['method'], acceptance='pending_visual_review')
    expanded = {}
    for name, frame in manifest['frames'].items():
        canonical = frame.get('pixel_alias_of', name); record = unique[canonical]; expanded[name] = record
        exact, origin, _ = export_placement(canvas, frame['source_canvas'], record['native_offset'], record['canvas_origin_px'])
        frame.update(native_offset=exact, registration_native_offset=record['native_offset'],
                     aligned_canvas_origin_px=origin,
                     crop_origin_px=[origin[i]+frame['crop_in_aligned_px'][i] for i in [0,1]])
    assert not validate_manifest(manifest, expanded)
    manifest['animations'] = sources['bindings']
    assert manifest['animations'] == sources['bindings']
    manifest['missing_frames'] = missing
    manifest['full_coverage'] = not missing
    manifest['native_source_files'] = len(sources['sources'])
    manifest['pixel_aliases'] = sources['pixel_aliases']
    if missing:
        manifest['status'] = 'partial_export_pending_visual_review'
        manifest['coverage_note'] = 'Available restored images packed with the shared exporter using an explicit available-frame inventory. Original complete native animation metadata is retained verbatim; missing references remain explicit and must not be played from this partial package.'
    checks = read(out / 'review/export_checks.json')
    checks.update(source_files=len(sources['sources']), exported_native_files=len(manifest['frames']),
                  full_coverage=not missing, missing_frames=missing, native_animation_metadata_preserved=True)
    save(out / 'review/export_checks.json', checks)
    manifest['native_palettes'] = {}
    for palette, source in sources['palette_sources'].items():
        path = out / 'palettes' / f'palette_{palette}.act'; shutil.copy2(REPO / source['path'], path)
        assert sha(path) == source['sha256']
        manifest['native_palettes'][palette] = dict(path=str(path.relative_to(out)), sha256=sha(path), source=source)
    manifest['generated_detail_measurements'] = read(out / 'calibration.json')
    manifest['driver_acceptance'] = False; manifest['installed'] = False
    save(out / 'draft_manifest.json', manifest)
    print(json.dumps(dict(stem=stem, masters=len(unique), native_files=len(manifest['frames']),
                         atlas_pairs=len(manifest['pages']), native_palettes=list(manifest['native_palettes']),
                         exact_native_anchors=True, full_native_animation_metadata=True,
                         status='exported_review_candidate_not_accepted')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stems', nargs='+', type=int)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    for stem in args.stems:
        assert stem in STEMS
        try:
            export_candidate(stem) if args.export else process(stem)
        except Exception as e:
            print(json.dumps(dict(stem=stem, processing_failure=f'{type(e).__name__}: {e}', acceptance='incomplete')))
