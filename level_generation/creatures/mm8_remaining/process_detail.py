"""Extract true-alpha MM8 replacement sheets and render native-coordinate placement candidates."""
import argparse
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from prepare_detail import CREATURES, REPO, native_queue, read, save, sha

sys.path.insert(0, str(CREATURES / 'mm6_peasants'))
from process_family import gutters


def composite(image, color):
    result = Image.new('RGBA', image.size, (*color, 255))
    result.alpha_composite(image)
    return result.convert('RGB')


def edge_candidates(image):
    pixels = np.array(image)
    alpha = pixels[:, :, 3]
    rgb = pixels[:, :, :3].astype(float)
    distance = ndimage.distance_transform_edt(alpha >= 250)
    core = distance > 3
    if not core.any():
        return np.zeros(alpha.shape), None
    _, nearest = ndimage.distance_transform_edt(~core, return_indices=True)
    reference = rgb[nearest[0], nearest[1]]
    chroma = rgb - rgb.mean(axis=2, keepdims=True)
    local_chroma = reference - reference.mean(axis=2, keepdims=True)
    band = (alpha > 0) & (distance <= 3)
    score = np.max(np.abs(chroma - local_chroma), axis=2) * alpha / 255 * band
    return score, reference


def upright_landmarks(image):
    """Unarmed clothed upright poses only; markers must still be visually checked."""
    pixels = np.asarray(image)
    alpha = pixels[:, :, 3] > 128
    rgb = pixels[:, :, :3].astype(int)
    ys, xs = np.where(alpha)
    bottom = int(ys.max()) + 1
    foot_x = np.where(alpha[max(0, bottom - 2):bottom])[1]
    green = alpha & (rgb[:, :, 1] > rgb[:, :, 0] * 1.1) & (rgb[:, :, 1] > rgb[:, :, 2] * 1.1)
    height = bottom - ys.min()
    yy = np.indices(alpha.shape)[0]
    green &= (yy > ys.min() + height * .20) & (yy < ys.min() + height * .75)
    labels, _ = ndimage.label(ndimage.binary_closing(green, iterations=max(1, round(height / 200))))
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    assert sizes.max(), 'No garment landmark; choose another anatomical check'
    sy, sx = np.where(green & (sizes[labels] >= sizes.max() * .1))
    return dict(foot_contact=[float(np.median(foot_x)), bottom],
                garment_center=[float(np.mean(sx)), float(np.mean(sy))])


def run(project, job_ids):
    root = REPO / project
    out = root / 'redo_2x'
    run_record = read(out / 'run.json')
    policy = read(out / 'processing.json') if (out / 'processing.json').exists() else {}
    registration_path = out / 'registration.json'
    registration = read(registration_path) if registration_path.exists() else {}
    for folder in ['cleaned', 'aligned_2x', 'review']:
        (out / folder).mkdir(exist_ok=True)
    for job in run_record['jobs']:
        if job['id'] not in job_ids or not job.get('selected_raw'):
            continue
        raw_path = REPO / job['selected_raw']
        raw = Image.open(raw_path).convert('RGBA')
        pixels = np.asarray(raw)
        foreground = pixels[:, :, 3] > 4
        assert foreground.any() and (~foreground).any(), 'Real alpha required'
        columns, rows = job['columns'], job['rows']
        correction = policy.get('jobs', {}).get(job['id'], {})
        components = None
        if correction.get('connected_body_extraction'):
            specification = correction['connected_body_extraction']
            assert specification['raw_sha256'] == sha(raw_path) and specification['reason']
            sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
            from extract_run import connected_cells
            components = connected_cells(raw, job, seed_alpha_threshold=specification.get('seed_alpha_threshold', 0))
        else:
            ycuts = gutters(foreground.any(axis=1), rows)
        native_width, native_height = job['cell_native_size']
        sampling_xy = [raw.width / columns / native_width, raw.height / rows / native_height]
        if abs(sampling_xy[0] / sampling_xy[1] - 1) >= .025:
            aspect_review = correction.get('aspect_review', {})
            assert aspect_review.get('raw_sha256') == sha(raw_path), 'Changed sheet aspect requires review'
            assert aspect_review.get('sampling_xy') == sampling_xy and aspect_review.get('reason')
        scale = 2 / np.mean(sampling_xy)
        scale *= correction.get('uniform_scale', 1)
        assert 2 / scale >= 2, 'Insufficient measured sampling'
        canvas = job['logical_canvas']
        review_padding = policy.get('review_padding', 0)
        review_width = canvas[0] + review_padding * 2
        review_height = canvas[1] + review_padding * 2 + 24
        contact = Image.new('RGB', (review_width * 4, review_height * 2 * ((len(job['frames']) + 3) // 4)),
                            (42, 42, 42))
        draw = ImageDraw.Draw(contact)
        edge_rows = []
        for index, name in enumerate(job['frames']):
            row, col = divmod(index, columns)
            if components:
                rect, clean = components[index]
            else:
                xcuts = gutters(foreground[ycuts[row]:ycuts[row + 1]].any(axis=0), columns)
                rect = [xcuts[col], ycuts[row], xcuts[col + 1], ycuts[row + 1]]
                clean = raw.crop(rect)
            warm_cast = policy.get('warm_cast_correction')
            if warm_cast:
                assert warm_cast['reason']
                values = np.array(clean)
                rgb = values[:, :, :3].astype(float)
                weight = np.clip((rgb[:, :, 0] - rgb[:, :, 2]) / warm_cast['red_blue_span'], 0, 1)
                weight *= np.clip((rgb[:, :, 0] - rgb[:, :, 1]) / warm_cast['red_green_span'], 0, 1)
                luminance = rgb @ np.array([.2126, .7152, .0722])
                neutral = luminance[:, :, None] * np.array(warm_cast['neutral_rgb_ratio'])
                values[:, :, :3] = np.round(rgb * (1 - weight[:, :, None])
                                            + neutral * weight[:, :, None]).clip(0, 255).astype(np.uint8)
                clean = Image.fromarray(values)
            if 'exposure_multiplier' in policy:
                values = np.array(clean)
                values[:, :, :3] = np.round(values[:, :, :3] * policy['exposure_multiplier']).clip(0, 255)
                clean = Image.fromarray(values)
            score, local_rgb = edge_candidates(clean)
            before = clean.copy()
            edge_policy = policy.get('local_edge_rgb', {})
            if edge_policy:
                assert edge_policy['reason'] and edge_policy['raw_sha256'].get(job['id']) == sha(raw_path)
                affected = score > edge_policy['threshold']
                values = np.array(clean)
                if 'minimum_chroma' in edge_policy:
                    rgb = values[:, :, :3].astype(int)
                    affected &= rgb.max(axis=2) - rgb.min(axis=2) >= edge_policy['minimum_chroma']
                values[:, :, :3][affected] = np.round(local_rgb[affected]).clip(0, 255).astype(np.uint8)
                clean = Image.fromarray(values)
                assert np.array_equal(np.asarray(clean)[:, :, 3], np.asarray(before)[:, :, 3])
            clean_path = out / 'cleaned' / job['id'] / (name + '.png')
            clean_path.parent.mkdir(exist_ok=True)
            clean.save(clean_path)
            resized = clean.convert('RGBa').resize((round(clean.width * scale), round(clean.height * scale)),
                                                   Image.Resampling.LANCZOS).convert('RGBA')
            # The full raw-to-canvas transform includes the crop and fractional nominal cell origin.
            shift = correction.get('translations_2x', {}).get(name, [0, 0])
            offset = [round(job['native_crop'][0] * 2 + (rect[0] - col * raw.width / columns) * scale) + shift[0],
                      round(job['native_crop'][1] * 2 + (rect[1] - row * raw.height / rows) * scale) + shift[1]]
            bounds = resized.getbbox()
            origin = [min(-32, offset[k] + bounds[k] - 4) for k in (0, 1)]
            size = [max(canvas[k] * 2 + 32, offset[k] + bounds[k + 2] + 4) - origin[k] for k in (0, 1)]
            aligned = Image.new('RGBA', size)
            aligned.paste(resized, (offset[0] - origin[0], offset[1] - origin[1]))
            aligned_path = out / 'aligned_2x' / (name + '.png')
            aligned.save(aligned_path)
            native = native_queue.native(root, name)
            native_offset = [(canvas[0] - native.width) / 2, canvas[1] - native.height]
            landmarks = None
            if correction.get('upright_foot_y'):
                assert name[4] not in ('d', 'x'), 'Falling poses need their own anatomical review'
                native_points = upright_landmarks(native)
                restored_points = upright_landmarks(aligned)
                dy = round((native_points['foot_contact'][1] + native_offset[1]) * 2
                           - restored_points['foot_contact'][1] - origin[1])
                # Move the logical canvas origin rather than resampling or clipping artwork.
                origin[1] += dy
                offset[1] += dy
                landmarks = {key: dict(native=[native_points[key][axis] + native_offset[axis]
                                               for axis in (0, 1)],
                                       restored=[(restored_points[key][axis] + origin[axis]) / 2
                                                 for axis in (0, 1)]) for key in native_points}
            manual = correction.get('manual_landmarks', {}).get(name)
            if manual:
                assert manual['raw_sha256'] == sha(raw_path), 'Landmarks refer to another raw sheet'
                anchor = manual['points'][manual['translation_anchor']]
                shift = [round(2 * (anchor['native'][k] - anchor['restored'][k])) for k in (0, 1)]
                origin = [origin[k] + shift[k] for k in (0, 1)]
                offset = [offset[k] + shift[k] for k in (0, 1)]
                landmarks = {key: dict(native=point['native'],
                                       restored=[point['restored'][k] + shift[k] / 2 for k in (0, 1)])
                             for key, point in manual['points'].items()}
            record = dict(batch=job['id'], raw=job['selected_raw'], raw_sha256=sha(raw_path), raw_rect=rect,
                          scale_to_2x=scale, sampling=2 / scale, translation_px=offset,
                          canvas_origin_px=origin, aligned_size_px=size, logical_size=canvas,
                          native_offset=native_offset, path=str(aligned_path.relative_to(out)),
                          cleaned_path=str(clean_path.relative_to(out)), status='placement_review_required')
            if landmarks:
                record['review_landmarks'] = landmarks
                record['translation_anchor'] = manual['translation_anchor'] if manual else 'foot_contact Y only'
            registration[name] = record
            # Native and restored are displayed at native logical scale, in shared coordinates.
            for tier, im in enumerate([native, aligned]):
                cell_x = index % 4 * review_width + review_padding
                cell_y = index // 4 * review_height * 2 + tier * review_height + review_padding
                if tier:
                    im = im.convert('RGBa').resize((round(im.width / 2), round(im.height / 2)),
                                                  Image.Resampling.LANCZOS).convert('RGBA')
                    position = [cell_x + origin[0] // 2, cell_y + 24 + origin[1] // 2]
                else:
                    position = [cell_x + round(native_offset[0]), cell_y + 24 + round(native_offset[1])]
                contact.paste(im, position, im)
                draw.text((cell_x + 4, cell_y + 4), name + (' restored' if tier else ' native'), fill='white')
                if landmarks:
                    for point_index, key in enumerate(landmarks):
                        color = ['#ffdc00', '#ff66ff'][point_index % 2]
                        point = landmarks[key]['restored' if tier else 'native']
                        px, py = cell_x + point[0], cell_y + 24 + point[1]
                        draw.line((px - 4, py, px + 4, py), fill=color)
                        draw.line((px, py - 4, px, py + 4), fill=color)
            y, x = np.unravel_index(np.argmax(score), score.shape)
            patch = (x - 14, y - 14, x + 14, y + 14)
            edge_rows.append((name, before.crop(patch), clean.crop(patch), float(score.max())))
        contact.save(out / 'review' / (job['id'] + '_placement.png'))
        edge_contact = Image.new('RGB', (224 * 4, 248 * len(edge_rows)), (42, 42, 42))
        edge_draw = ImageDraw.Draw(edge_contact)
        for row, (name, before, after, score) in enumerate(edge_rows):
            edge_draw.text((4, row * 248 + 4), f'{name}: candidate score {score:.1f}; before/after dark/light', fill='white')
            for col, (im, bg) in enumerate([(before, (30, 30, 30)), (before, (238, 238, 238)),
                                             (after, (30, 30, 30)), (after, (238, 238, 238))]):
                edge_contact.paste(composite(im, bg).resize((224, 224), Image.Resampling.NEAREST),
                                   (col * 224, row * 248 + 24))
        edge_contact.save(out / 'review' / (job['id'] + '_edges.png'))
        save(registration_path, registration)
        print(job['id'], len(job['frames']), 'extracted;', round(2 / scale, 3), 'sampling; placement review required')
    save(registration_path, registration)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--jobs', nargs='+', required=True)
    args = parser.parse_args()
    run(args.project, args.jobs)
