"""Prepare complete native animations with separate outline-only geometry references; no AI calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1]))
from sheet_checks import OBSERVED_ENVELOPES
from whole_animation_resolution import DEFAULT_POLICY


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def native_2x(source, sources, palette):
    path = REPO / source["path"]
    assert digest(path) == source["sha256"], path
    with Image.open(path) as bmp:
        assert bmp.mode == "P" and list(bmp.size) == source["size"]
        indices = np.array(bmp)
    selected = str(source.get("fixed_palette", palette))
    palette_source = sources["palette_sources"][selected]
    palette_path = REPO / palette_source["path"]
    assert digest(palette_path) == palette_source["sha256"], palette_path
    colors = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
    pixels = np.dstack([colors[indices], (indices != 0).astype(np.uint8) * 255])
    pixels[indices == 0] = 0
    raw = Image.fromarray(pixels)
    canvas = sources["logical_canvas"]
    offset = [(canvas[0] - raw.width) / 2, canvas[1] - raw.height]
    image = Image.new("RGBA", tuple(v * 2 for v in canvas))
    image.paste(raw.resize((raw.width * 2, raw.height * 2), Image.Resampling.NEAREST),
                tuple(round(v * 2) for v in offset))
    assert np.count_nonzero(np.array(image)[:, :, 3]) == np.count_nonzero(indices) * 4
    return image, offset


def best_grid(count, width, height):
    candidates = []
    for columns in range(1, count + 1):
        rows = math.ceil(count / columns)
        for envelope in OBSERVED_ENVELOPES:
            sampling = min(envelope[0] / (columns * width), envelope[1] / (rows * height))
            candidates.append((sampling, -(columns * rows - count), columns, rows, envelope))
    return max(candidates)


def scopes(manifest, sources):
    base = str(sources["base_palette"])
    seen, represented = {}, set()
    for action in ("walk", "standing", "attack", "attack2", "hit", "fidget", "death", "corpse"):
        animation = manifest["animations_by_palette"][base][action]
        for view, steps in animation["views"].items():
            if not steps or any(step["mirrored"] for step in steps):
                continue
            names = [sources["pixel_aliases"].get(step["frame"], step["frame"]) for step in steps]
            signature = tuple(names)
            binding = dict(action=action, view=int(view), native_frames=[step["frame"] for step in steps])
            if signature in seen:
                seen[signature]["bindings"].append(binding)
                continue
            entry = dict(id=f"{action}_{view}_sheet", action=action, view=int(view),
                         frames=names, bindings=[binding], native_sequence=True)
            seen[signature] = entry
            represented.update(names)
    missing = set(sources["sources"]) - represented - set(sources["pixel_aliases"])
    groups = {}
    for name in sorted(missing):
        groups.setdefault(re.sub(r"[a-z][0-4]$", "", name), []).append(name)
    for group, names in groups.items():
        seen[tuple(names)] = dict(id=f"unused_{group}_sheet", action="unused_native", view=0,
                                 frames=names, bindings=[], native_sequence=False)
    return list(seen.values())


def prepare(source_project, destination, padding, allow_resolution_tradeoff=True):
    original, root = REPO / source_project, REPO / destination
    if (root / "redo_2x/run.json").exists():
        run = read(root / "redo_2x/run.json")
        assert run["source_project"] == source_project and run["padding_native_px"] == padding
        for job in run["jobs"]:
            assert all(digest(REPO / asset["path"]) == asset["sha256"]
                       for asset in job["prepared_assets"])
        print(json.dumps(dict(project=destination, jobs=len(run["jobs"]), reused=True)))
        return
    root.mkdir(parents=True, exist_ok=True)
    config, sources, manifest = (read(original / name) for name in ("config.json", "sources.json", "manifest.json"))
    config["inventory_file"] = "inventory.json"
    if config["family"] == "drr1":
        config["regions"] = "Dark green scaled hide, gold underside/spines and pale horns/claws; protect eyes. No wings."
    for name in ("sources.json", "manifest.json", "recolor_vectors.json", "inventory.json"):
        shutil.copy2(original / name, root / name)
    write(root / "config.json", config)
    if config.get("material_module"):
        shutil.copy2(original / config["material_module"], root / config["material_module"])
    out = root / "redo_2x"
    for folder in ("references", "prompts", "raw", "review"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    native = {}
    offsets = {}
    for name, source in sources["sources"].items():
        image, offset = native_2x(source, sources, sources["base_palette"])
        native[name], offsets[name] = image, offset
    jobs = scopes(manifest, sources)
    views = ["front", "front-oblique", "profile", "rear-oblique", "back"]
    for job in jobs:
        images = [native[name] for name in job["frames"]]
        boxes = [image.getbbox() for image in images]
        assert all(boxes), "Native empty endpoint needs explicit empty-frame handling"
        crop_2x = [min(box[0] for box in boxes) - padding * 2,
                   min(box[1] for box in boxes) - padding * 2,
                   max(box[2] for box in boxes) + padding * 2,
                   max(box[3] for box in boxes) + padding * 2]
        crop = [value / 2 for value in crop_2x]
        cell = [(crop_2x[2] - crop_2x[0]) // 2, (crop_2x[3] - crop_2x[1]) // 2]
        budget, _, columns, rows, envelope = best_grid(len(images), *cell)
        sheet = Image.new("RGBA", (columns * cell[0] * 2, rows * cell[1] * 2))
        outline_sheet = Image.new("RGB", sheet.size, "white")
        for i, image in enumerate(images):
            cropped = image.crop(crop_2x)
            restored = Image.new("RGBA", image.size)
            restored.paste(cropped, tuple(crop_2x[:2]))
            assert np.array_equal(np.array(image.convert("RGBa")), np.array(restored.convert("RGBa")))
            offset = (i % columns * cropped.width, i // columns * cropped.height)
            sheet.paste(cropped, offset)
            # Extract native-scale geometry before enlarging its one-native-pixel boundary.
            inside = np.array(cropped.getchannel("A"))[::2, ::2] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[boundary] = 0
            outline_sheet.paste(Image.fromarray(guide).resize(cropped.size, Image.Resampling.NEAREST), offset)
        native_path = out / "references" / (job["id"] + "_native.png")
        outline_path = out / "references" / (job["id"] + "_outline.png")
        sheet.save(native_path)
        outline_sheet.save(outline_path)
        identity_name = job["frames"][0]
        prior = original / "redo_2x/cleaned" / (identity_name + ".png")
        if not prior.exists():
            prior = original / "cleaned" / (identity_name + ".png")
        assert prior.exists(), prior
        identity_path = out / "references" / (job["id"] + "_detail.png")
        identity = Image.open(prior).convert("RGBA")
        identity_pixels = np.array(identity)
        identity_pixels[identity_pixels[:, :, 3] == 0] = 0
        identity = Image.fromarray(identity_pixels)
        bounds = identity.getbbox()
        assert bounds, prior
        identity.crop((max(0, bounds[0] - 6), max(0, bounds[1] - 6),
                       min(identity.width, bounds[2] + 6), min(identity.height, bounds[3] + 6))).save(identity_path)
        reference_paths = [str(path.relative_to(REPO)) for path in (native_path, outline_path, identity_path)]
        repeats = [name for i, name in enumerate(job["frames"]) if name in job["frames"][:i]]
        anatomy = ("Keep both hip/knee/ankle/toe and shoulder/elbow/wrist/finger chains, near/far ownership, "
                   "joint bends, lengths, thicknesses, planted/raised feet, torso lean and head bob.")
        if config["family"] == "wdm":
            anatomy += " Keep the exact wing-root/arm relationship, bat-wing joints/folds/sweep and long thin claw fingers."
        elif config["family"] == "drr1":
            anatomy = ("Keep all FOUR original leg chains and their near/far ownership, exact foot contacts/lifts, "
                       "long slender curved neck, small head, tail curl, spine/horn positions and body bob. No wings.")
        elif config["family"] == "cle":
            anatomy += " Preserve staff hand/grip/angle and small finial, cloak folds and full native cloak length."
        elif config["family"] == "arc1":
            anatomy += " Preserve bow ownership/grip, bow-string, arrow direction, quiver and straps."
        elif config["family"] == "rat":
            anatomy = "Keep all FOUR leg chains, near/far ownership, planted/lifted paws, spine arch, snout, ears and long tail; preserve each original gait step."
        elif config["family"] == "spi1":
            anatomy = "Keep all EIGHT spider leg chains, each joint bend, near/far ownership and ground contact, original cephalothorax/abdomen proportions, fangs and body bob; never substitute a six-legged gait."
        elif config["family"] == "cob":
            anatomy = "Keep the exact original snake head, hood width, long articulated neck, coil and tail curvature in every step and unusual stored orientation. Preserve hood markings, jaws and fang ownership. No arms, legs, human joints or new tail coils."
        elif config["family"] == "bh":
            anatomy = "Keep the original floating head proportions, both curved horn loops and tips, one central eye, original pupil/eyelid changes, jaw and tooth ownership, pointed chin and original hover motion. No limbs, eye stalks, additional eyes or new appendages."
        elif config["family"] == "gar":
            anatomy += " Preserve both wing roots, ribs, membrane openings, original wing sweep/fold, digitigrade ankle bends, splayed claws, muzzle and horns. Death changes the whole creature into original separate rock fragments and rubble, never a flesh corpse."
        elif config["family"] == "min1":
            anatomy += " Preserve bull muzzle, horn roots and curves, cloven hooves, the enormous double axe, both hands' original grip and exact blade/shaft orientation."
        elif config["family"] in ("ert", "fie1", "djn"):
            anatomy = "Preserve the original visible limb chains, their ownership and bends, body proportions and exact silhouette/effect changes. Keep the original rocky, fiery or floating lower-body structure; do not invent feet or a humanoid gait where none is present."
        target = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
        title = "Original " + config["title"]
        prompt = f"""TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration of an EXISTING Might and Magic VI (MM6) fantasy role-playing game sprite asset, using the supplied original animation bitmaps. Restore the existing fantasy-game character and its original animation; preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.

Use case: style-transfer. High-detail {title} restoration. Output EXACTLY {len(images)} sprites in ONE image: {columns} columns, {rows} rows, chronological row-major order. This is the COMPLETE native {job['action']} animation for stored view {job['view']} ({views[job['view']]}). The original contains precisely {len(images)} bitmap steps. Do not add poses, interpolation, repeated subjects, a longer cycle or extra panels.
Image 1 is the untouched original complete native colour animation. Sole authority for each step's pose, proportions, camera, silhouette, limb ownership, equipment coverage, native position/scale and base material colours.
Image 2 is the separate matching OUTLINE-ONLY animation sheet. One-native-pixel silhouette contours and transparent limb gaps guide GEOMETRY AND ANIMATION ONLY. Black lines and white interior/exterior convey no lighting, shading or texture and must not appear in the result. No internal contrast guides.
Image 3 is previous detailed enhanced artwork for APPEARANCE AND MATERIAL FINISH ONLY. Preserve its reconstructed fine facial/material detail, skin wrinkles or fine scales, hair/cloth or wing-membrane texture, leather grain, seams, rivets, metal variation and wear where present. Never copy its pose, altered anatomy, muscle bulk or invented equipment. Images 1 and 2 remain anatomy authority.
Character: {config['description']}
Anatomy fidelity is mandatory in EVERY cell: {anatomy} No fused/swapped/extra limbs, disconnected joints, duplicated or changed animation steps, broad muscles, enlarged hands, added equipment or new gait. All anatomy and motion extremes must match the native references. Keep natural foreshortening; do not normalize crouched/prone pose heights.
Preserve rich fine detail and natural contrast with coherent soft native baked lighting across every frame. Reconstruct continuous contours and shading rather than enlarged pixel blocks, pixel art, dithering or interpolated detail. Avoid ONLY artificial large blotchy shading bands, exaggerated black muscle grooves and copied outline strokes. Do not flatten contrast, smooth away detail, remove wrinkles/texture, blur the interior, create waxy/plastic skin, sharpen halos or add noisy pseudo-detail.
Palette/material separation: Generate ONLY the native base appearance, palette {sources['base_palette']}, shown in Image 1 and described above. Preserve those exact material colours and their separation. Do not generate other palette variants or borrow another variant's colours from an appearance reference.
Layout: chronological row-major order {', '.join(job['frames'])}. Common native crop {crop} (exclusive right/bottom), padded cell {cell}, original actor canvas {sources['logical_canvas']} and pivot {sources['logical_pivot']}. Exactly the same crop/scale/position for every step: no independent centering, zoom or silhouette fit. Retain the {padding}-native-pixel transparent safety border, full thin tips and planned aspect {columns * cell[0]}:{rows * cell[1]}. Fill occupied cells without extra exterior whitespace; leave unused cells empty.
Request a LARGE {target[0]}x{target[1]} master or greater with at least 2.5 actual generated pixels per native pixel in both axes. Detail must be generated, not produced by enlargement. Exactly one RGBA image with genuine transparent background and gaps. No grid lines, labels, text, paper, painted checkerboard, background gradient, floor or cast shadows.
"""
        if repeats:
            prompt += f"Native held/repeated artwork: {', '.join(repeats)}. Repeated source steps must have identical appearance/pose; preserve the hold rather than invent a new pose.\n"
        if job["action"] in ("death", "corpse"):
            prompt += "Follow the native non-graphic falling/resting or dissipating effect sequence exactly; add no blood/injury detail. Preserve complete native effects and their colours rather than replacing them with another body pose.\n"
            prompt += "The living character description applies only where its body remains visible in Image 1. Reproduce each native fading/effect/residue stage, including disconnected particles; never invent a complete body in an effect or residue cell.\n"
        if not job["native_sequence"]:
            prompt += "These are preserved unreferenced native assets, not a new runtime animation; do not invent playback bindings.\n"
        if allow_resolution_tradeoff:
            prompt += "The one COMPLETE animation/view sheet is the main requirement. The requested sampling is a detail target: if the tool's output budget is smaller, retain ALL ordered original steps on one returned sheet. Never split the animation or enlarge an earlier return to claim extra generated detail.\n"
        if len(images) == 1:
            prompt += "FINAL FRAME COUNT: ONE SINGLE SPRITE. This one bitmap is the entire native animation. Match its one pose and one outline exactly; no storyboard, walk cycle, variations, repeated character or extra panels. Use the whole image for that single original pose with transparent safety padding.\n"
        prompt_path = out / "prompts" / (job["id"] + "_v1.txt")
        prompt_path.write_text(prompt)
        job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows,
                   observed_envelope=list(envelope), planned_sampling=budget, requested_master=target,
                   references=reference_paths, reference_roles=["untouched_native_complete_animation",
                   "outline_only_geometry_no_shading", "previous_detailed_material_appearance_not_pose"],
                   appearance_source=dict(path=str(prior.relative_to(REPO)), sha256=digest(prior)),
                   prompt=str(prompt_path.relative_to(REPO)), status="pending", attempts=[],
                   prepared_assets=[dict(path=str(path.relative_to(REPO)), sha256=digest(path))
                                    for path in (native_path, outline_path, identity_path, prompt_path)])
    write(out / "run.json", dict(project=destination, source_project=source_project,
          method="packed_complete_animation_outline_only_detailed_appearance",
          status="prepared", target_sampling=2.5,
          padding_native_px=padding, reference_enlargement=2,
          source_metadata=[dict(path=str((original / name).relative_to(REPO)), sha256=digest(original / name))
                           for name in ("sources.json", "manifest.json", "config.json")],
          native_offsets=offsets, jobs=jobs))
    processing = dict(preserve_matte_hued_materials=True, supplied_alpha_noise_floor=0,
          reason="Preserve delivered alpha initially; cleanup thresholds require inspection of actual returns.")
    if allow_resolution_tradeoff:
        processing['whole_animation_resolution_policy'] = DEFAULT_POLICY
    write(out / "processing.json", processing)
    print(json.dumps(dict(project=destination, jobs=len(jobs), source_frames=len(sources["sources"]),
                         smallest_planned_sampling=min(job["planned_sampling"] for job in jobs))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_project")
    parser.add_argument("destination")
    parser.add_argument("--padding", type=int, default=2)
    parser.add_argument("--strict-minimum", action="store_true", help="Use only for an explicitly requested strict detail gate")
    args = parser.parse_args()
    assert args.padding >= 1
    prepare(args.source_project, args.destination, args.padding, not args.strict_minimum)
