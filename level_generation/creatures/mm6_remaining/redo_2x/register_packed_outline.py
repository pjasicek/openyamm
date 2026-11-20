"""Register complete-sheet returns in their saved native coordinates; anatomical review remains separate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

from prepare_packed_outline import REPO, native_2x

sys.path.insert(0, str(REPO / "level_generation/creatures/mm6_peasants"))
import process_family


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register(project):
    root = REPO / project
    out = root / "redo_2x"
    run, config, sources = (read(path) for path in (out / "run.json", root / "config.json", root / "sources.json"))
    materials = process_family.module("packed_materials", root / config["material_module"]) if config.get("material_module") else None
    for folder in ("aligned_2x", "masks_2x"):
        (out / folder).mkdir(exist_ok=True)
    records, calibration = {}, {}
    policy = read(out / "processing.json")
    for job in run["jobs"]:
        report_path = out / "review" / (job["id"] + "_extraction.json")
        if not report_path.exists() or not job.get("selected_raw"):
            continue
        report = read(report_path)
        assert report["raw"] == job["selected_raw"]
        raw = REPO / report["raw"]
        assert digest(raw) == report["raw_sha256"]
        width, height = report["raw_size"]
        cw, ch = job["cell_native_size"]
        sampling = min(width / (job["columns"] * cw), height / (job["rows"] * ch))
        factor = 2 / sampling
        anatomy = policy.get('anatomical_sheet_calibration', {}).get(job['id'])
        body_review = anatomy or policy.get('anatomical_sheet_review', {}).get(job['id'])
        if body_review:
            assert body_review['raw_sha256'] == report['raw_sha256']
            reference = next(frame for frame in report['frames'] if frame['frame'] == body_review['frame'])
            assert digest(REPO / reference['clean_path']) == body_review['clean_sha256']
            assert body_review['method'] and body_review['landmarks']
        if anatomy:
            points = anatomy['landmarks']
            first, second = (points[label] for label in anatomy['scale_pair'])
            axes = anatomy['axes']
            assert axes in ([0], [1], [0, 1])
            sampling = np.linalg.norm((np.array(second['clean']) - first['clean'])[axes]) / np.linalg.norm(
                (np.array(second['native']) - first['native'])[axes])
            factor = 2 / sampling
            anchor = points[anatomy['anchor']]
            reference_index = report['frames'].index(reference)
            reference_cell = [reference_index % job['columns'] * width / job['columns'],
                              reference_index // job['columns'] * height / job['rows']]
            cell_anchor = np.array(reference['raw_rect'][:2]) - reference_cell + anchor['clean']
        calibration[job['id']] = dict(raw=report['raw'], raw_sha256=report['raw_sha256'],
            native_crop=job['native_crop'], delivered_size=report['raw_size'],
            nominal_grid_sampling_xy=[width / (job['columns'] * cw), height / (job['rows'] * ch)],
            uniform_scale=factor, method='Shared native sheet mapping; independent anatomical calibration pending.')
        if anatomy:
            calibration[job['id']].update(generated_sampling=float(sampling), anatomical_reference=anatomy,
                method=anatomy['method'])
        elif body_review:
            calibration[job['id']].update(independent_anatomical_review=body_review, method=body_review['method'])
        for index, frame in enumerate(report["frames"]):
            name = frame["frame"]
            if name in records:
                # One canonical bitmap also supplies held steps and shared frames in other actions.
                records[name].setdefault("reused_in_jobs", []).append(dict(job=job["id"], cell=index))
                continue
            path = REPO / frame["clean_path"]
            clean = Image.open(path).convert("RGBA")
            alpha = np.array(clean.getchannel("A"))
            x0, y0, x1, y1 = frame["raw_rect"]
            raw_clip = bool((x0 == 0 and (alpha[:, 0] > 64).any()) or
                            (y0 == 0 and (alpha[0, :] > 64).any()) or
                            (x1 == width and (alpha[:, -1] > 64).any()) or
                            (y1 == height and (alpha[-1, :] > 64).any()))
            boundary_review = policy.get("reviewed_complete_boundary_tips", {}).get(name)
            if raw_clip and boundary_review:
                assert boundary_review["raw_sha256"] == report["raw_sha256"]
                assert boundary_review["reason"]
                assert 64 < boundary_review["maximum_alpha"] < 128
                assert 0 < boundary_review["maximum_pixels_above_64"] <= 4
                touched = np.concatenate([alpha[:, 0] if x0 == 0 else np.array([], np.uint8),
                    alpha[0, :] if y0 == 0 else np.array([], np.uint8),
                    alpha[:, -1] if x1 == width else np.array([], np.uint8),
                    alpha[-1, :] if y1 == height else np.array([], np.uint8)])
                assert int(touched.max()) <= boundary_review["maximum_alpha"]
                assert int((touched > 64).sum()) <= boundary_review["maximum_pixels_above_64"]
                raw_clip = False
            size = [max(1, round(value * factor)) for value in clean.size]
            scaled = clean.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")
            cell_origin = [index % job["columns"] * width / job["columns"],
                           index // job["columns"] * height / job["rows"]]
            translation = np.round(np.array(job["native_crop"][:2]) * 2 +
                                   factor * (np.array(frame["raw_rect"][:2]) - cell_origin)).astype(int)
            if anatomy:
                translation = np.round(np.array(anchor['native']) * 2 + factor * (
                    np.array(frame['raw_rect'][:2]) - cell_origin - cell_anchor)).astype(int)
            position = policy.get('frame_translation_calibration', {}).get(name)
            if position:
                assert position['raw_sha256'] == report['raw_sha256']
                assert position['clean_sha256'] == digest(path)
                assert position['axes'] in ([0], [1], [0, 1])
                assert position['method'] and position['landmark']
                effective = np.array(size) / clean.size
                for axis in position['axes']:
                    translation[axis] = round(position['native'][axis] * 2 -
                                              position['clean'][axis] * effective[axis])
            bounds = scaled.getbbox()
            assert bounds, name
            origin = np.minimum([0, 0], translation + bounds[:2] - 4)
            end = np.maximum(np.array(sources["logical_canvas"]) * 2, translation + bounds[2:] + 4)
            aligned = Image.new("RGBA", tuple(end - origin))
            aligned.paste(scaled, tuple(translation - origin))
            aligned.save(out / "aligned_2x" / (name + ".png"))
            material_guide = policy.get('enhanced_material_guides', {}).get(name)
            if material_guide:
                assert materials and material_guide['clean_sha256'] == digest(path)
                assert material_guide['reason']
                mask = materials.coverage(clean, name=name, guides=material_guide['regions'])
            else:
                mask = materials.coverage(clean) if materials else process_family.mask(clean, config)
            resized = Image.merge(mask.mode, [band.resize(size, Image.Resampling.LANCZOS)
                                             for band in mask.split()])
            weights = np.array(resized)
            if weights.ndim == 3:
                total = weights.astype(float).sum(axis=2, keepdims=True)
                weights = np.floor(weights / np.maximum(1, total / 255)).astype(np.uint8)
            weights[np.array(scaled.getchannel("A")) == 0] = 0
            if "fixed_palette" in sources["sources"][name]:
                weights[:] = 0
            resized = Image.fromarray(weights, mode=mask.mode)
            placed = Image.new(mask.mode, aligned.size)
            placed.paste(resized, tuple(translation - origin))
            protected = policy.get('protected_material_axes', {}).get(name)
            if protected:
                assert protected['aligned_sha256'] == digest(out / 'aligned_2x' / (name + '.png'))
                assert protected['reason'] and mask.mode == 'RGBA'
                yy, xx = np.indices((aligned.height, aligned.width))
                footprint = np.zeros((aligned.height, aligned.width), dtype=bool)
                for segment in protected.get('segments', [protected['points']]):
                    start, end_point = np.array(segment, dtype=float).reshape(2, 2)
                    vector = end_point - start
                    length = np.linalg.norm(vector)
                    assert length > 0 and 0 < protected['radius'] <= 32
                    vector /= length
                    dx, dy = xx - start[0], yy - start[1]
                    along = dx * vector[0] + dy * vector[1]
                    distance = abs(dx * vector[1] - dy * vector[0])
                    footprint |= ((along >= -2) & (along <= length + 2) & (distance <= protected['radius']))
                weights = np.array(placed)
                weights[footprint, protected['channel']] = 0
                placed = Image.fromarray(weights, 'RGBA')
            placed.save(out / "masks_2x" / (name + ".png"))
            records[name] = dict(batch=job["id"], raw_path=report["raw"], raw_sha256=report["raw_sha256"],
                raw_size=report["raw_size"], raw_rect=frame["raw_rect"], clean_path=frame["clean_path"],
                clean_sha256=digest(path), native_crop=job["native_crop"], native_bounds=frame["native_bounds"],
                scale=factor, effective_sampling_xy=[2 * clean.width / size[0], 2 * clean.height / size[1]],
                translate=translation.tolist(), canvas_origin_px=origin.tolist(),
                raw_clip=raw_clip, extraction_cell=index, matte=frame["matte"],
                registration="Uniform native sheet mapping; no independent pose fit.",
                review_status="pending_independent_anatomy_and_placement_review")
            if boundary_review:
                records[name]["reviewed_complete_boundary_tip"] = boundary_review
            if position:
                records[name]['translation_calibration'] = position
                records[name].setdefault('review_landmarks', {})[position['landmark']] = dict(
                    native=position['native'],
                    restored_before_translation=(np.array(position['clean']) * effective).tolist())
                records[name]['registration'] += ' ' + position['method']
            if body_review:
                records[name]['registration'] = body_review['method']
                if position:
                    records[name]['registration'] += ' ' + position['method']
                if name == body_review['frame']:
                    effective = np.array(size) / clean.size
                    records[name]['review_landmarks'] = {label: dict(native=point['native'],
                        restored_before_translation=(np.array(point['clean']) * effective).tolist())
                        for label, point in body_review['landmarks'].items()}
                    records[name]['independent_residual_logical'] = {label:
                        ((np.array(point['clean']) * effective + translation) / 2 - point['native']).tolist()
                        for label, point in body_review['landmarks'].items()
                        if not anatomy or (label not in anatomy['scale_pair'] and label != anatomy['anchor'])}
        jobs_contact = [name for name in dict.fromkeys(job["frames"]) if name in records]
        canvas = sources["logical_canvas"]
        restored_height = max([canvas[1]] + [
            int(np.ceil((records[name]["canvas_origin_px"][1] +
                         Image.open(out / "aligned_2x" / (name + ".png")).height) / 2))
            for name in jobs_contact])
        contact = Image.new("RGB", (canvas[0] * len(jobs_contact), canvas[1] + restored_height + 44), (42, 45, 42))
        draw = ImageDraw.Draw(contact)
        for i, name in enumerate(jobs_contact):
            original, _ = native_2x(sources["sources"][name], sources, sources["base_palette"])
            original = original.resize(tuple(canvas), Image.Resampling.NEAREST)
            contact.paste(original, (i * canvas[0], 25), original)
            enhanced = Image.open(out / "aligned_2x" / (name + ".png")).convert("RGBA")
            enhanced = enhanced.convert("RGBa").resize((round(enhanced.width / 2), round(enhanced.height / 2)),
                                                      Image.Resampling.LANCZOS).convert("RGBA")
            origin = records[name]["canvas_origin_px"]
            contact.paste(enhanced, (i * canvas[0] + round(origin[0] / 2),
                                    canvas[1] + 30 + round(origin[1] / 2)), enhanced)
            draw.text((i * canvas[0] + 5, 5), name, fill="white")
        contact.save(out / "review" / (job["id"] + "_registered.png"))
    for alias, canonical in sources["pixel_aliases"].items():
        if canonical not in records:
            continue
        records[alias] = dict(records[canonical], generated_frame=canonical, pixel_alias=canonical)
        for folder in ("aligned_2x", "masks_2x"):
            Image.open(out / folder / (canonical + ".png")).save(out / folder / (alias + ".png"))
    (out / "registration.json").write_text(json.dumps(records, indent=2) + "\n")
    (out / "calibration.json").write_text(json.dumps(calibration, indent=2) + "\n")
    missing = sorted(set(sources["sources"]) - set(records))
    print(json.dumps(dict(project=project, registered=len(records), missing=len(missing),
                         measured_minimum=min(min(record["effective_sampling_xy"]) for record in records.values())
                         if records else None, anatomical_acceptance="pending")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    register(parser.parse_args().project)
