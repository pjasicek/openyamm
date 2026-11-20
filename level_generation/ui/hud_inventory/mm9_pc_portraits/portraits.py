"""MM9 PC portraits as MM6-MM8 portrait families: references, Codex briefs, extraction, verification, sheets.

Follows PLAYBOOK.md. Image generation itself is done by Codex (`codex exec`); this script never edits generated
pixels except registration resampling, and never installs runtime assets.

    python3 portraits.py survey PC05
    python3 portraits.py prepare PC05
    python3 portraits.py extract PC05
    <venv>/bin/python portraits.py measure --model face_landmarker.task PC05
    python3 portraits.py verify PC05          # or a family, e.g. pc34, to find template outlier slots
    python3 portraits.py repair PC05 6 44 47 --families pc02,7pc05,pc33 --frontal 44
    python3 portraits.py sheet PC05
"""

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from extract_transparent_portraits import sheet_geometry  # noqa: E402

ICONS = ROOT / "assets_dev/engine/icons_x2"
MM9 = ROOT / "mm9/extracted/ART/ART/PCPORTRAITS"
MM9_NPC = ROOT / "mm9/extracted/ART/ART/NPCPORTRAITS"
SIZE = (118, 158)
SLOT = (156, 182)
INSET = (19, 12)
SHEET = (1092, 728)
SHEETS = (("A", 1), ("B", 29))
PARTIAL = {35, 36}
# Least crown drop below frame 01 for the dodge slots: the lower quartile of the 59 native 56-frame families
# (medians 35 and 64 px). A template that only tips its head forward still gets a visible duck.
MIN_DODGE_DROP = {35: 27, 36: 55}
DEFAULT_HEAD_FIT = 0.96
FAMILY_MEASUREMENTS = HERE / "measurements_families.json"
MIN_DETECTED = 48


# ---------------------------------------------------------------- data

def characters():
    return json.loads((HERE / "characters.json").read_text())["characters"]


def character(cid):
    table = characters()
    if cid not in table:
        raise SystemExit(f"Unknown character {cid}; see characters.json")
    return table[cid]


def workspace(cid):
    folder = HERE / cid.lower()
    folder.mkdir(exist_ok=True)
    return folder


def own_mapping(cid):
    """The character's editable mapping, <workspace>/mapping.json, copied from mappings/<name>.json once."""
    own = workspace(cid) / "mapping.json"
    if not own.exists():
        shared = HERE / "mappings" / f"{character(cid)['mapping']}.json"
        if not shared.exists():
            raise SystemExit(f"Missing shared mapping {shared}")
        own.write_text(shared.read_text())
    return own


def mapping(cid):
    return {int(k): v for k, v in json.loads(own_mapping(cid).read_text())["slots"].items()}


def template_family(info, number):
    return info.get("template_overrides", {}).get(str(number), info["template"])


def template_frame(info, number):
    return ICONS / f"{template_family(info, number)}-{number:02d}.png"


def native_dir(cid):
    """PCnn sets are player characters; NPCnn sets are MM9's hirelings (18 or 19 frames, a subset of the PC numbers)."""
    return MM9_NPC / cid if cid.startswith("NPC") else MM9 / cid


def native_frame(cid, number):
    kind, number_text = ("NPC", cid[3:]) if cid.startswith("NPC") else ("PC", cid[2:])
    return native_dir(cid) / f"{kind}-{number_text}-{number:02d}.pcx"


def body_box(alpha):
    labels, _ = ndimage.label(alpha >= 128, structure=np.ones((3, 3)))
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    ys, xs = np.where(labels == sizes.argmax())
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def place(sheet, image, slot):
    sheet.alpha_composite(image, (slot % 7 * SLOT[0] + INSET[0], slot // 7 * SLOT[1] + INSET[1]))


def native_x2(path):
    # 60x80 -> 120x160 nearest; drop one column/row each side to sit in the 118x158 window.
    image = Image.open(path).convert("RGBA")
    return image.resize((120, 160), Image.Resampling.NEAREST).crop((1, 1, 119, 159))


def tile(path, size, background=(62, 62, 66)):
    image = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    result = Image.new("RGBA", size, background + (255,))
    result.alpha_composite(image)
    return result.convert("RGB")


# ---------------------------------------------------------------- survey

def survey(cid):
    """Contact sheets for choosing the template and reviewing the character's frame mapping."""
    info, folder = character(cid), workspace(cid)
    own_mapping(cid)
    frames = sorted(int(p.stem.split("-")[-1]) for p in native_dir(cid).glob("*.pcx"))
    cw, ch, cols = 120, 160, 14
    image = Image.new("RGB", (cols * cw, math.ceil(len(frames) / cols) * (ch + 14)), (25, 25, 25))
    draw = ImageDraw.Draw(image)
    for k, number in enumerate(frames):
        x, y = k % cols * cw, k // cols * (ch + 14)
        image.paste(Image.open(native_frame(cid, number)).convert("RGB").resize((cw, ch)), (x, y + 14))
        draw.text((x + 3, y + 1), str(number), fill=(255, 220, 0))
    image.save(folder / "survey_native.png")

    # Template candidates: the proposed one first, then every 56-frame family of the same row of MM6-MM8.
    families = sorted(p.name[:-len("-56.png")] for p in ICONS.glob("*-56.png"))
    candidates = [info["template"]] + [f for f in families if f != info["template"]]
    cw, ch, cols = 88, 118, 12
    rows = math.ceil((len(candidates) + 1) / cols)
    image = Image.new("RGB", (cols * cw, rows * (ch + 14)), (60, 60, 64))
    draw = ImageDraw.Draw(image)
    image.paste(Image.open(native_frame(cid, 1)).convert("RGB").resize((cw, ch)), (0, 14))
    draw.text((3, 1), cid, fill=(255, 255, 255))
    for k, family in enumerate(candidates, start=1):
        x, y = k % cols * cw, k // cols * (ch + 14)
        image.paste(tile(ICONS / f"{family}-01.png", (cw, ch)), (x, y + 14))
        draw.text((x + 3, y + 1), family + (" (proposed)" if k == 1 else ""), fill=(255, 220, 0))
    image.save(folder / "survey_templates.png")

    # Mapping review: per slot, meaning, the MM9 source frame and the template frame.
    slots = mapping(cid)
    cw, ch, label = 90, 120, 230
    image = Image.new("RGB", (2 * (label + 2 * cw + 20), 28 * (ch + 4)), (24, 22, 28))
    draw = ImageDraw.Draw(image)
    for number in range(1, 57):
        column, row = divmod(number - 1, 28)
        x, y = column * (label + 2 * cw + 20), row * (ch + 4)
        slot = slots[number]
        source = native_frame(cid, slot["mm9_frame"])
        draw.text((x + 4, y + 4), f"{number:02d} {slot['meaning'][:30]}", fill=(240, 240, 240))
        draw.text((x + 4, y + 20), f"mm9 {slot['mm9_frame']}, state from {slot['state_from']}", fill=(160, 160, 170))
        if source.exists():
            image.paste(Image.open(source).convert("RGB").resize((cw, ch)), (x + label, y))
        else:
            draw.text((x + label + 4, y + 50), "MISSING", fill=(255, 100, 90))
        image.paste(tile(template_frame(info, number), (cw, ch)), (x + label + cw + 4, y))
    image.save(folder / "survey_mapping.png")
    print(f"Wrote survey_native.png, survey_templates.png, survey_mapping.png in {folder}")


# ---------------------------------------------------------------- prepare

BRIEF = """# Codex brief: MM9 {cid} as an MM6-MM8 player portrait sheet, sheet {letter}

Scope: image generation only, with your built-in image generation tool. Write only into
`{folder}`. No builds, no other edits, no scripts that alter pixels.

Sheet {letter} holds portrait slots {first:02d}-{last:02d}.

## Inputs (attached in this order)

1. `template_{letter}.png`: LAYOUT, FRAMING AND STYLE TARGET. 28 transparent portraits of existing game characters
   (not the new character) in 7 columns x 4 rows, read left to right then top to bottom. Sheet 1092x728,
   slots 156x182, each portrait window 118x158 at inset (19,12). For every slot it defines the head size and
   position inside its window, the head angle and tilt, how much of the head is visible (partial heads stay
   partial), the clean cut-out with only a short neck stub and no shoulders, the bright warm pre-rendered
   lighting, and the state treatment (tints, stone, closed eyes, bruises).
2. `source_{letter}.png`: IDENTITY AND EXPRESSION SOURCE. The same layout filled with low-resolution frames of
   the NEW character from another game, one chosen frame per slot. Busts on a coloured background with clothing;
   background, clothing and shoulders are NOT wanted.
3. `identity.png`: the new character's neutral face, larger.{identity_master}

## What to produce

One image: the NEW character ({description}) drawn into the 28 slots of input 1, so the result can replace the
template characters in the same game without looking out of place.

- Identity, hair shape and colour, horns, ears, beard, skin colour and face proportions come from inputs 2
  and 3{master_clause}. Do not copy the template's face, hair, skin colour or accessories.
- Framing comes from input 1: same head height in its window, same horizontal centre, same lower cut-off with
  only a short neck stub, same head angle, tilt and gaze direction, same partial/low position for ducking slots.
  No shoulders, collar, armour or clothing. Keep hair, horns and ears as close to the head as the native frames
  allow, so the head is no wider than the template's head plus its hair.
- Expression: copy the mouth, eyes and brows of the input 2 frame in the same slot, adjusted to the template's
  head angle. Where input 1 shows a state the source frame does not (sickly green poisoned skin, pustules, grey
  stone, red straining face, closed eyes, bruise, sleeping tilt, head turns and nods, glances), apply the
  template's state to the new character.
- Injury slots (sheet B slots 37-39, the 9th-11th portraits): intact skin with faint bruising and a pained or
  dazed expression. No blood, cuts or open wounds.
- Style: finely detailed pre-rendered fantasy-game portrait matching input 1's lighting and colour (warm, evenly
  lit, natural saturation), not the dark coloured rim lighting of input 2. Fresh high-resolution reconstruction
  with real fine detail; no pixel-art enlargement, blur-only smoothing or square texels.

## Transparency and layout

- Genuinely transparent RGBA background (alpha 0) outside each head. No checkerboard, painted backdrop,
  shadow or halo. Clean thin antialiased edges. Transparency can look brown or grey in a preview: check the
  alpha channel before rejecting a result for its background.
- EXACTLY 7 columns x 4 rows, 28 separate portraits in reading order, generous uniform transparent gutters so
  no two portraits touch. Landscape around 1536x1024. No text, labels, borders, rings or guide marks.

## Records

- Copy the exact generated file, unmodified, to `raw_{letter}.png`. If the result has a wrong grid count,
  touching portraits, no real transparency or the template's face instead of the new one, do ONE corrective
  regeneration and keep the first as `raw_{letter}_rejected.png`.
- Write `generation_{letter}.json`: exact prompt(s), input paths with sha256, output path, sha256, size, mode,
  and a one-paragraph self-check against this brief.
"""

MASTER_INPUT = """
4. `raw_A.png`: the ACCEPTED sheet A of this same character (transparent; view it over a solid colour). It is the
   identity master for this sheet: the same hair (volume, length, wave, parting, colour; not bigger or curlier),
   skin tone, face shape, lighting and rendering as sheet A, and the same head size: a frontal head in this sheet
   fills its window exactly as much as a frontal head in sheet A (an earlier character's sheet B came out 12 %
   larger, so the head jumped in size between frames)."""


def codex_command(folder, letter, inputs):
    relative = folder.relative_to(ROOT)
    brief = relative / f"brief_{letter}.md"
    attached = " ".join(str(relative / name) for name in inputs)
    return (f'codex exec "Follow the brief in {brief} exactly. The attached images are its inputs in order. '
            f'Produce the sheet with your built-in image generation tool and save it as specified." '
            f'-c model_reasoning_effort=medium -C {ROOT} -s workspace-write --add-dir ~/.codex/generated_images '
            f'-o {relative}/codex_last_message_{letter}.md -i {attached} '
            f'< /dev/null > {relative}/codex_run_{letter}.log 2>&1')


RUNNER = """#!/bin/bash
# Written by portraits.py: one Codex image job, retried on transient Codex failures (model at capacity, rate limits,
# dropped connections), which parallel runs hit often. Run it in the background; it exits 0 once {output} exists.
cd {root} || exit 1
for attempt in 1 2 3 4 5 6; do
  {command}
  [ -f {output} ] && exit 0
  if ! grep -qE "{transient}" {log}; then
    echo "Codex failed without output; see {log}"; exit 1
  fi
  cp {log} {log}.retry_$attempt
  sleep $((60 * attempt))
done
echo "Codex still failing after 6 attempts"; exit 1
"""


TRANSIENT = "at capacity|Reconnecting|stream disconnected|error sending request|429|Too Many Requests|rate limit"


def write_runner(path, command, output, log):
    path.write_text(RUNNER.format(root=ROOT, command=command, output=output, log=log, transient=TRANSIENT))
    path.chmod(0o755)
    return path.relative_to(ROOT)


def prepare(cid):
    info, folder = character(cid), workspace(cid)
    if not info["description"]:
        raise SystemExit(f"Write {cid}'s identity description in characters.json first (PLAYBOOK step 2)")
    own = own_mapping(cid)
    slots = mapping(cid)
    for letter, first in SHEETS:
        template = Image.new("RGBA", SHEET)
        source = Image.new("RGBA", SHEET)
        for slot in range(28):
            number = first + slot
            frame = Image.open(template_frame(info, number)).convert("RGBA")
            assert frame.size == SIZE, template_frame(info, number)
            place(template, frame, slot)
            mm9 = native_frame(cid, slots[number]["mm9_frame"])
            if not mm9.exists():
                raise SystemExit(f"Slot {number}: {mm9.name} does not exist; fix {own}")
            place(source, native_x2(mm9), slot)
        template.save(folder / f"template_{letter}.png")
        source.save(folder / f"source_{letter}.png")
        relative = folder.relative_to(ROOT)
        text = BRIEF.format(cid=cid, letter=letter, folder=relative, first=first, last=first + 27,
                            description=info["description"],
                            identity_master=MASTER_INPUT if letter == "B" else "",
                            master_clause=" and the sheet A identity master" if letter == "B" else "")
        (folder / f"brief_{letter}.md").write_text(text)
    Image.open(native_frame(cid, 1)).convert("RGB").resize((240, 320), Image.Resampling.LANCZOS).save(
        folder / "identity.png")
    relative = folder.relative_to(ROOT)
    runners = [write_runner(folder / f"run_{letter}.sh", codex_command(folder, letter, inputs),
                            relative / f"raw_{letter}.png", relative / f"codex_run_{letter}.log")
               for letter, inputs in (("A", ["template_A.png", "source_A.png", "identity.png"]),
                                      ("B", ["template_B.png", "source_B.png", "identity.png", "raw_A.png"]))]
    print("References and briefs written. From the repository root run sheet A, review raw_A.png, then sheet B:")
    print("\n".join(f"  {runner}" for runner in runners))


# ---------------------------------------------------------------- extract

def resample(cell, scale, offset):
    border = max(cell.size)
    padded = Image.new("RGBA", (cell.width + 2 * border, cell.height + 2 * border))
    padded.paste(cell, (border, border))
    x, y = offset
    window = (border - x / scale, border - y / scale,
              border + (SIZE[0] - x) / scale, border + (SIZE[1] - y) / scale)
    return padded.convert("RGBa").resize(SIZE, Image.Resampling.LANCZOS, box=window).convert("RGBA")


def repair_cells(folder, info):
    """Targeted regenerations: <folder>/repair_*/raw.png with slots.json {"slots": [left, right], "frontal": n}."""
    found = []
    for repair in sorted(folder.glob("repair_*")):
        raw_path, spec_path = repair / "raw.png", repair / "slots.json"
        if not raw_path.exists() or not spec_path.exists():
            continue
        spec = json.loads(spec_path.read_text())
        raw = Image.open(raw_path).convert("RGBA")
        occupancy = (np.asarray(raw.getchannel("A")) > 8).sum(axis=0)
        bounds = np.linspace(0, raw.width, len(spec["slots"]) + 1).astype(int)
        # Split at the emptiest column around each nominal boundary.
        cuts = [0]
        for boundary in bounds[1:-1]:
            span = raw.width // (2 * len(spec["slots"]))
            cuts.append(boundary - span + int(np.argmin(occupancy[boundary - span:boundary + span])))
        cuts.append(raw.width)
        cells = []
        for number, left, right in zip(spec["slots"], cuts, cuts[1:]):
            cell = raw.crop((left, 0, right, raw.height))
            target = body_box(np.asarray(Image.open(template_frame(info, number)).convert("RGBA").getchannel("A")))
            cells.append((repair.name, number, cell, body_box(np.asarray(cell.getchannel("A"))), target, None))
        found.append((spec["frontal"], cells))
    return found


def extract(cid):
    info, folder = character(cid), workspace(cid)
    slots = mapping(cid)
    prefix = info["prefix"]
    (folder / "frames").mkdir(exist_ok=True)
    report, cells = {}, []
    for letter, first in SHEETS:
        raw = Image.open(folder / f"raw_{letter}.png")
        report[letter] = {"raw_size": list(raw.size), "raw_mode": raw.mode}
        raw = raw.convert("RGBA")
        columns, rows, issues = sheet_geometry(raw)
        report[letter]["grid_issues"] = issues
        for slot in range(28):
            number = first + slot
            cell = raw.crop([columns[slot % 7], rows[slot // 7], columns[slot % 7 + 1], rows[slot // 7 + 1]])
            master = body_box(np.asarray(cell.getchannel("A")))
            target = body_box(np.asarray(Image.open(template_frame(info, number)).convert("RGBA").getchannel("A")))
            cells.append((letter, number, cell, master, target, (target[3] - target[1]) / (master[3] - master[1])))
    # One head size for the whole character, so the head never pulses between frames.
    head_fit = info.get("head_fit", DEFAULT_HEAD_FIT)
    scale = head_fit * float(np.median([c[5] for c in cells if c[1] not in PARTIAL]))
    neutral = next(c for c in cells if c[1] == 1)
    scales = {}
    for frontal, repaired in repair_cells(folder, info):
        reference = next(c for c in repaired if c[1] == frontal)
        for item in repaired:
            # A repair has its own resolution: its frontal head gets frame 01's output height.
            scales[item[1]] = scale * (neutral[3][3] - neutral[3][1]) / (reference[3][3] - reference[3][1])
        replaced = {item[1] for item in repaired}
        cells = [c for c in cells if c[1] not in replaced] + repaired
    first = next(c for c in cells if c[1] == 1)
    first_scale = scales.get(1, scale)
    neutral_crown = first[4][3] - first_scale * (first[3][3] - first[3][1])
    for group, number, cell, master, target, fit in sorted(cells, key=lambda c: c[1]):
        used = scales.get(number, scale)
        width = used * (master[2] - master[0])
        left = (target[0] + target[2]) / 2 - width / 2
        # Shift inward to keep a one-pixel margin; a head wider than the canvas is centred and clipped evenly.
        left = (SIZE[0] - width) / 2 if width > SIZE[0] - 2 else min(max(left, 1), SIZE[0] - 1 - width)
        # Ducking dodge frames match the template's crown and sink out of the frame; others sit on its bottom.
        if number in PARTIAL:
            crown = max(target[1], neutral_crown + MIN_DODGE_DROP[number])
            top = crown - used * master[1]
        else:
            top = target[3] - used * master[3]
        frame = resample(cell, used, (left - used * master[0], top))
        frame.save(folder / "frames" / f"{prefix}{number:02d}.png")
        report.setdefault(group, {})[f"{number:02d}"] = {
            "meaning": slots[number]["meaning"], "master_box": master, "template_box": target,
            "output_box": body_box(np.asarray(frame.getchannel("A"))), "scale": round(used, 4),
            "clipped_px": round(max(0.0, width - SIZE[0]), 1), "master_px_per_native": round(2 / used, 2)}
    (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    clipped = {k: v["clipped_px"] for g in report.values() for k, v in g.items()
               if isinstance(v, dict) and v.get("clipped_px", 0) > 0}
    sampling = min(v["master_px_per_native"] for g in report.values() for v in g.values()
                   if isinstance(v, dict) and "master_px_per_native" in v)
    print(f"Extracted 56 frames; grid issues A {report['A']['grid_issues']} B {report['B']['grid_issues']}; "
          f"lowest sampling {sampling} px/native (gate > 2); clipped {clipped or 'none'}")
    # Codex sometimes draws sheet B's heads larger than sheet A's; one scale for 56 frames then makes the head
    # jump in size between frames. Compare each sheet's own height fit to the template (dodge slots excluded).
    fits = {letter: float(np.median([(c[4][3] - c[4][1]) / (c[3][3] - c[3][1]) for c in cells
                                     if c[0] == letter and c[1] not in PARTIAL])) for letter, _ in SHEETS}
    ratio = fits["A"] / fits["B"]
    report["sheet_head_ratio_b_to_a"] = round(ratio, 3)
    (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if abs(ratio - 1) > .05:
        print(f"WARNING: sheet B heads are {ratio:.2f}x sheet A's; regenerate sheet B (PLAYBOOK step 4)")
    comparison(cid)


def comparison(cid):
    """Per slot: MM9 source, template, new frame on grey, new frame on the dark HUD tone."""
    info, folder = character(cid), workspace(cid)
    slots = mapping(cid)
    cw, ch, cols = SIZE[0], SIZE[1], 7
    for letter, first in SHEETS:
        image = Image.new("RGB", (cols * (4 * cw + 12), 4 * (ch + 18)), (24, 24, 24))
        draw = ImageDraw.Draw(image)
        for slot in range(28):
            number = first + slot
            x0, y0 = slot % cols * (4 * cw + 12), slot // cols * (ch + 18)
            image.paste(native_x2(native_frame(cid, slots[number]["mm9_frame"])).convert("RGB"), (x0, y0 + 18))
            new = folder / "frames" / f"{info['prefix']}{number:02d}.png"
            for k, (path, background) in enumerate(((template_frame(info, number), (90, 90, 90)),
                                                    (new, (90, 90, 90)), (new, (20, 18, 24)))):
                image.paste(tile(path, (cw, ch), background), (x0 + (k + 1) * cw, y0 + 18))
            draw.text((x0 + 2, y0 + 3), f"{number:02d} {slots[number]['meaning'][:44]}", fill=(255, 220, 0))
        image.save(folder / f"comparison_{letter}.png")


# ---------------------------------------------------------------- measure (needs mediapipe)

SHAPES = ["eyeBlinkLeft", "eyeBlinkRight", "eyeLookUpLeft", "eyeLookUpRight", "eyeLookDownLeft", "eyeLookDownRight",
          "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight", "eyeWideLeft", "eyeWideRight",
          "eyeSquintLeft", "eyeSquintRight", "jawOpen", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft",
          "mouthFrownRight", "mouthPucker", "mouthFunnel", "browInnerUp", "browDownLeft", "browDownRight"]


def measure_frames(landmarker, paths):
    import mediapipe as mp
    rows = {}
    for number, path in paths.items():
        rgba = Image.open(path).convert("RGBA")
        canvas = Image.new("RGBA", (rgba.width + 60, rgba.height + 60), (128, 128, 128, 255))
        canvas.alpha_composite(rgba, (30, 30))
        big = canvas.convert("RGB").resize((canvas.width * 4, canvas.height * 4), Image.Resampling.LANCZOS)
        alpha = np.asarray(rgba.getchannel("A")) > 128
        ys = np.where(alpha.any(axis=1))[0]
        pixels = np.asarray(rgba).astype(float)
        rgb = pixels[..., :3][pixels[..., 3] > 250]
        row = {"head_height": int(ys.max() - ys.min() + 1) if len(ys) else 0,
               "chroma": [float(v) for v in (rgb / (rgb.sum(axis=1, keepdims=True) + 1e-6)).mean(axis=0)],
               "saturation": float(np.std(rgb, axis=1).mean())}
        detection = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB,
                                               data=np.ascontiguousarray(np.asarray(big))))
        if detection.face_blendshapes:
            shapes = {c.category_name: c.score for c in detection.face_blendshapes[0]}
            row["shapes"] = {name: round(shapes[name], 3) for name in SHAPES}
            r = np.asarray(detection.facial_transformation_matrixes[0])[:3, :3]
            row["yaw"] = round(math.degrees(math.atan2(-r[2, 0], math.hypot(r[0, 0], r[1, 0]))), 1)
            row["pitch"] = round(math.degrees(math.atan2(r[2, 1], r[2, 2])), 1)
            row["roll"] = round(math.degrees(math.atan2(r[1, 0], r[0, 0])), 1)
        rows[f"{number:02d}"] = row
    return rows


def measure(model, cids):
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision
    options = vision.FaceLandmarkerOptions(base_options=mp_tasks.BaseOptions(model_asset_path=model),
                                           output_face_blendshapes=True,
                                           output_facial_transformation_matrixes=True, num_faces=1,
                                           min_face_detection_confidence=0.2, min_face_presence_confidence=0.2)
    with vision.FaceLandmarker.create_from_options(options) as landmarker:
        if not FAMILY_MEASUREMENTS.exists():
            families = {}
            for path in sorted(ICONS.glob("*-56.png")):
                family = path.name[:-len("-56.png")]
                families[family] = measure_frames(
                    landmarker, {n: ICONS / f"{family}-{n:02d}.png" for n in range(1, 57)})
                print(family, sum("shapes" in r for r in families[family].values()), "/ 56 faces", flush=True)
            FAMILY_MEASUREMENTS.write_text(json.dumps(families) + "\n")
        for cid in cids:
            info, folder = character(cid), workspace(cid)
            rows = measure_frames(landmarker, {n: folder / "frames" / f"{info['prefix']}{n:02d}.png"
                                               for n in range(1, 57)})
            (folder / "measurements.json").write_text(json.dumps(rows) + "\n")
            print(cid, sum("shapes" in r for r in rows.values()), "/ 56 faces")


# ---------------------------------------------------------------- verify

FEATURES = {  # name: (floor, label for a positive change, label for a negative change)
    "eyes_closed": (0.15, "eyes close", "eyes open wider"),
    "eye_wide": (0.15, "eyes widen", "eyes less wide"),
    "squint": (0.15, "squint", "less squint"),
    "gaze_up": (0.15, "gaze up", "gaze down"),
    "gaze_left": (0.15, "gaze to its own left", "gaze to its own right"),
    "jaw_open": (0.12, "mouth opens", "mouth closes"),
    "smile": (0.15, "smile", "less smile"),
    "frown": (0.10, "mouth corners down", "corners up"),
    "pucker": (0.15, "lips pucker/funnel", "lips relax"),
    "brow_up": (0.15, "inner brows up", "brows lower"),
    "brow_down": (0.15, "brows down (anger)", "brows relax"),
    "yaw": (6.0, "head turns (+yaw)", "head turns (-yaw)"),
    "pitch": (6.0, "head pitches (+)", "head pitches (-)"),
    "roll": (6.0, "head rolls (+)", "head rolls (-)"),
    "height": (0.08, "taller", "head lower/partly out of frame"),
    "green": (0.012, "greener skin", "less green"),
    "red": (0.015, "redder skin", "less red"),
    "saturation": (0.30, "more saturated", "desaturated (grey/stone)"),
}


def features(row, base):
    out = {"height": row["head_height"] / base["head_height"] - 1 if base["head_height"] else 0.0,
           "green": row["chroma"][1] - base["chroma"][1], "red": row["chroma"][0] - base["chroma"][0],
           "saturation": row["saturation"] / max(base["saturation"], 1e-6) - 1}
    if "shapes" not in row or "shapes" not in base:
        return out
    s, b = row["shapes"], base["shapes"]

    def mean(shape, *names):
        return float(np.mean([shape[n] for n in names]))

    def gaze_left(shape):
        return (shape["eyeLookOutLeft"] + shape["eyeLookInRight"] - shape["eyeLookInLeft"]
                - shape["eyeLookOutRight"]) / 2

    def gaze_up(shape):
        return mean(shape, "eyeLookUpLeft", "eyeLookUpRight") - mean(shape, "eyeLookDownLeft", "eyeLookDownRight")

    pairs = {"eyes_closed": ("eyeBlinkLeft", "eyeBlinkRight"), "eye_wide": ("eyeWideLeft", "eyeWideRight"),
             "squint": ("eyeSquintLeft", "eyeSquintRight"), "jaw_open": ("jawOpen",),
             "smile": ("mouthSmileLeft", "mouthSmileRight"), "frown": ("mouthFrownLeft", "mouthFrownRight"),
             "pucker": ("mouthPucker", "mouthFunnel"), "brow_up": ("browInnerUp",),
             "brow_down": ("browDownLeft", "browDownRight")}
    for name, keys in pairs.items():
        out[name] = mean(s, *keys) - mean(b, *keys)
    out["gaze_up"] = gaze_up(s) - gaze_up(b)
    out["gaze_left"] = gaze_left(s) - gaze_left(b)
    for name in ("yaw", "pitch", "roll"):
        out[name] = row[name] - base[name]
    return out


def slot_usage():
    """Slot -> what shows it, from the frame table, face animations and the idle picker."""
    enum_text = (ROOT / "game/tables/PortraitEnums.h").read_text()
    block = enum_text[enum_text.index("enum class PortraitId"):]
    names = {int(v): k for k, v in re.findall(r"(\w+)\s*=\s*(\d+)", block[:block.index("};")])}
    by_portrait, current = defaultdict(list), None
    for line in (ROOT / "assets_dev/engine/data_tables/portrait_frame_data.txt").read_text().splitlines()[3:]:
        cells = line.split("\t")
        if len(cells) >= 5 and cells[0].strip().isdigit():
            current = int(cells[0]) or current
            by_portrait[current].append(int(cells[1]))
    events = defaultdict(list)
    for line in (ROOT / "assets_dev/engine/data_tables/face_animations.txt").read_text().splitlines()[1:]:
        cells = line.split("\t")
        if len(cells) >= 3:
            for expression in cells[2].split(","):
                events[expression.strip()].append(cells[1])
    idle_text = (ROOT / "game/gameplay/GameplayScreenRuntime.cpp").read_text()
    idle_block = idle_text[idle_text.index("PortraitId pickIdlePortrait"):]
    idle = set(re.findall(r"PortraitId::(\w+)", idle_block[:idle_block.index("\n}\n")]))
    usage = defaultdict(list)
    for portrait, textures in by_portrait.items():
        name = names.get(portrait, str(portrait))
        role = name + (" (animation " + ",".join(map(str, textures)) + ")" if len(set(textures)) > 1 else "")
        tags = (["idle"] if name in idle else []) + events.get(name, [])
        role += ": " + ", ".join(tags) if tags else ""
        for texture in sorted(set(textures)):
            usage[texture].append(role)
    return usage


def verify(target):
    """Compare a character (or a family, to find its outlier slots) with the MM6-MM8 human consensus."""
    families = json.loads(FAMILY_MEASUREMENTS.read_text())
    is_character = target in characters()
    if is_character:
        info, folder = character(target), workspace(target)
        rows = json.loads((folder / "measurements.json").read_text())
        meanings = {n: s["meaning"] for n, s in mapping(target).items()}
    else:
        info, folder, rows = None, None, families[target]
        meanings = {n: s["meaning"] for n, s in
                    ((int(k), v) for k, v in json.loads((HERE / "mappings/human.json").read_text())["slots"].items())}
    references = [f for f, r in families.items()
                  if f != target and sum("shapes" in x for x in r.values()) >= MIN_DETECTED]
    usage = slot_usage()
    report = {"target": target, "reference_families": references, "slots": {}}
    for number in range(1, 57):
        key = f"{number:02d}"
        reference = defaultdict(list)
        for family in references:
            for name, value in features(families[family][key], families[family]["01"]).items():
                reference[name].append(value)
        own = features(rows[key], rows["01"])
        template_name = template_family(info, number) if is_character else None
        template = features(families[template_name][key], families[template_name]["01"]) if template_name else {}
        defining, extras, closed_eyes = [], [], False
        for name, (floor, positive, negative) in FEATURES.items():
            values = np.array(reference.get(name, []))
            if len(values) < 10:
                continue
            median = float(np.median(values))
            agree = float(np.mean(np.sign(values) == np.sign(median))) if median else 0.0
            strong = abs(median) > floor and float(np.mean(np.abs(values) > floor)) >= .5 and agree >= .7
            if strong and name == "squint" and closed_eyes:
                continue  # the model reads closed lids as squint
            value = own.get(name)
            if strong:
                closed_eyes = closed_eyes or (name == "eyes_closed" and median > 0)

                def shows(v):
                    return v is not None and np.sign(v) == np.sign(median) and abs(v) >= .35 * abs(median)

                defining.append({"feature": name, "label": positive if median > 0 else negative,
                                 "consensus": round(median, 3), "agreement": round(agree, 2),
                                 "value": None if value is None else round(value, 3), "ok": bool(shows(value)),
                                 "template_ok": bool(shows(template.get(name))) if template_name else None})
            elif value is not None and abs(value) > 2.5 * floor and abs(value) > abs(median) + 2 * floor:
                extras.append({"feature": name, "label": positive if value > 0 else negative,
                               "value": round(value, 3), "consensus": round(median, 3)})
        missing = [d for d in defining if not d["ok"]]
        status = ("no-face" if "shapes" not in rows[key] and number != 1 else
                  "pass" if not missing and not extras else
                  "check" if not missing else
                  "template" if template_name and all(not d["template_ok"] for d in missing) else "mismatch")
        report["slots"][key] = {"meaning": meanings[number], "used_for": usage.get(number, []), "status": status,
                                "defining": defining, "extras": extras}
        if status != "pass":
            line = f"{key} {status:8} {meanings[number][:34]:34} | wants: "
            line += ", ".join(d["label"] for d in defining) or "-"
            line += (" | MISSING: " + ", ".join(d["label"] for d in missing)) if missing else ""
            line += (" | EXTRA: " + ", ".join(e["label"] for e in extras)) if extras else ""
            print(line)
    counts = defaultdict(int)
    for slot in report["slots"].values():
        counts[slot["status"]] += 1
    print(dict(counts), f"against {len(references)} families")
    out = folder if folder else HERE / "template_checks"
    out.mkdir(exist_ok=True)
    (out / ("verification.json" if folder else f"{target}.json")).write_text(json.dumps(report, indent=1) + "\n")
    if is_character:
        verification_sheets(target, report)


def verification_sheets(cid, report):
    info, folder = character(cid), workspace(cid)
    families = ["pc02", "pc05", "pc12", "pc33", "7pc05", "7pc13"]
    colour = {"pass": (120, 220, 120), "check": (230, 210, 90), "template": (120, 180, 255),
              "mismatch": (255, 110, 90), "no-face": (170, 170, 170)}
    w, h, label = 73, 98, 300
    for part in range(4):
        image = Image.new("RGB", (label + (len(families) + 2) * (w + 3) + 10, 24 + 14 * (h + 4)), (24, 22, 28))
        draw = ImageDraw.Draw(image)
        for j, name in enumerate(families + ["template", "MM9 new"]):
            draw.text((label + j * (w + 3) + (10 if j > len(families) else 0), 6), name, fill=(255, 220, 0))
        for i, number in enumerate(range(part * 14 + 1, part * 14 + 15)):
            key, y = f"{number:02d}", 24 + i * (h + 4)
            slot = report["slots"][key]
            draw.text((6, y + 4), f"{key} {slot['meaning'][:40]}", fill=(240, 240, 240))
            draw.text((6, y + 20), slot["status"].upper(), fill=colour[slot["status"]])
            used = "; ".join(slot["used_for"])
            for line_no in range(3):
                draw.text((6, y + 36 + line_no * 13), used[line_no * 46:(line_no + 1) * 46], fill=(160, 160, 170))
            paths = [ICONS / f"{f}-{key}.png" for f in families]
            paths += [template_frame(info, number), folder / "frames" / f"{info['prefix']}{key}.png"]
            for j, path in enumerate(paths):
                image.paste(tile(path, (w, h)), (label + j * (w + 3) + (10 if j > len(families) else 0), y))
        image.save(folder / f"verification_{part + 1}.png")


# ---------------------------------------------------------------- repair

REPAIR_BRIEF = """# Codex brief: repair slots {slot_list} of MM9 {cid}

Scope: image generation only, built-in image generation tool. Write only into `{folder}`. No pixel edits, no builds.

## Inputs (attached in this order)

1. `template.png`: framing target, {count} windows of 118x158 in 156x182 slots, left to right = slots {slot_list}
   of an existing game character (not the new one). Copy head size, position, angle and crop (short neck stub, no
   shoulders) from it.
2. `consensus.png`: the wanted look, one row per slot in the same order as input 1, each row showing that slot
   in existing families ({families}):
{consensus_rows}
3. `../raw_A.png` and 4. `../raw_B.png`: the accepted sheets of the NEW character
   (transparent; view over a solid colour). They are the identity master: same face, hair, horns, ears, beard,
   skin, lighting and rendering. The result must be indistinguishable in identity and style from these sheets.

## Produce

One image with exactly {count} portraits of the new character side by side, left to right in the order above, on a
genuinely transparent RGBA background (alpha 0 outside the heads), with wide transparent gaps between them, no
text or borders, around {width}x1024 or larger:

{wanted}

The character: {description}. Keep eye colour, hair colour and every feature exactly as in the identity master.
Hair, horns and ears keep exactly the size, length and shape they have in the identity master: do not shrink
long ears or horns, and do not let hair grow wider than in the master.

## Records

Copy the exact generated file to `raw.png`; write `generation.json` (prompt, inputs with sha256, output sha256,
size, mode, self-check). One corrective regeneration at most; keep a rejected first result as `raw_rejected.png`.
Transparency can look brown or grey in a preview: check the alpha channel before rejecting for background.
"""


def repair(cid, slots, families, frontal):
    """Prepare a targeted regeneration of a few slots (PLAYBOOK step 8)."""
    info, folder = character(cid), workspace(cid)
    meanings = mapping(cid)
    target = folder / ("repair_" + "_".join(f"{s:02d}" for s in slots))
    target.mkdir(exist_ok=True)

    def strip(paths, out):
        image = Image.new("RGBA", (SLOT[0] * len(paths), SLOT[1]))
        for k, path in enumerate(paths):
            image.alpha_composite(Image.open(path).convert("RGBA"), (k * SLOT[0] + INSET[0], INSET[1]))
        image.save(out)

    strip([template_frame(info, s) for s in slots], target / "template.png")
    # Codex's image tool takes at most five reference images, so all consensus rows share one image.
    consensus = Image.new("RGBA", (SLOT[0] * len(families), SLOT[1] * len(slots)))
    for row, slot in enumerate(slots):
        for k, family in enumerate(families):
            frame = Image.open(ICONS / f"{family}-{slot:02d}.png").convert("RGBA")
            consensus.alpha_composite(frame, (k * SLOT[0] + INSET[0], row * SLOT[1] + INSET[1]))
    consensus.save(target / "consensus.png")
    attached = ["template.png", "consensus.png"]
    rows = "\n".join(f"   - row {k + 1}: slot {s} ({meanings[s]['meaning']})" for k, s in enumerate(slots))
    wanted = "\n".join(f"- slot {s}: {meanings[s]['meaning']}, as in row {k + 1} of `consensus.png`, with the head as "
                       f"in input 1's window {k + 1}." for k, s in enumerate(slots))
    relative = target.relative_to(ROOT)
    (target / "CODEX_BRIEF.md").write_text(REPAIR_BRIEF.format(
        cid=cid, folder=relative, slot_list=", ".join(map(str, slots)), count=len(slots),
        families=", ".join(families), consensus_rows=rows, width=max(1024, 512 * len(slots)), wanted=wanted,
        description=info["description"]))
    (target / "slots.json").write_text(json.dumps({"slots": slots, "frontal": frontal}) + "\n")
    attached = " ".join(str(relative / a) for a in attached)
    attached += f" {folder.relative_to(ROOT)}/raw_A.png {folder.relative_to(ROOT)}/raw_B.png"
    command = (f'codex exec "Follow the brief in {relative}/CODEX_BRIEF.md exactly. The attached images are its '
               f'inputs in order. Produce the image with your built-in image generation tool and save it as '
               f'specified." -c model_reasoning_effort=medium -C {ROOT} -s workspace-write '
               f'--add-dir ~/.codex/generated_images -o {relative}/codex_last_message.md -i {attached} '
               f'< /dev/null > {relative}/codex_run.log 2>&1')
    runner = write_runner(target / "run.sh", command, relative / "raw.png", relative / "codex_run.log")
    print(f"Repair prepared. From the repository root run: {runner}")


# ---------------------------------------------------------------- sheet

def sheet(cid):
    info, folder = character(cid), workspace(cid)
    frames = [folder / "frames" / f"{info['prefix']}{n:02d}.png" for n in range(1, 57)]
    result = Image.new("RGBA", (7 * SIZE[0], 8 * SIZE[1]))
    for k, path in enumerate(frames):
        result.alpha_composite(Image.open(path).convert("RGBA"), (k % 7 * SIZE[0], k // 7 * SIZE[1]))
    result.save(folder / f"{info['prefix'].rstrip('-')}_spritesheet.png")
    preview = Image.new("RGBA", result.size, (60, 60, 64, 255))
    preview.alpha_composite(result)
    preview.convert("RGB").save(folder / f"{info['prefix'].rstrip('-')}_spritesheet_preview.png")
    # Lineup beside existing families for a style check.
    lineup = ["pc01", "pc04", info["template"], "pc34"]
    numbers = [1, 8, 12, 23, 40, 54]
    image = Image.new("RGB", (80 + 5 * (SIZE[0] + 16), 24 + len(numbers) * (SIZE[1] + 10)), (22, 20, 26))
    draw = ImageDraw.Draw(image)
    for j, name in enumerate(lineup[:2] + [cid] + lineup[2:]):
        draw.text((80 + j * (SIZE[0] + 16) + 4, 6), name, fill=(255, 220, 0))
        for i, number in enumerate(numbers):
            path = (folder / "frames" / f"{info['prefix']}{number:02d}.png" if name == cid
                    else ICONS / f"{name}-{number:02d}.png")
            frame = Image.open(path).convert("RGBA")
            image.paste(frame, (80 + j * (SIZE[0] + 16), 24 + i * (SIZE[1] + 10)), frame)
    for i, number in enumerate(numbers):
        draw.text((6, 24 + i * (SIZE[1] + 10) + 70), f"frame {number}", fill=(200, 200, 200))
    image.save(folder / "lineup.png")
    print(f"Wrote spritesheet, preview and lineup.png in {folder}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("survey", "prepare", "extract", "sheet"):
        commands.add_parser(name).add_argument("character")
    commands.add_parser("verify").add_argument("target", help="character id, or a family to find outlier slots")
    repair_parser = commands.add_parser("repair", help="prepare a targeted regeneration of a few slots")
    repair_parser.add_argument("character")
    repair_parser.add_argument("slots", type=int, nargs="+")
    repair_parser.add_argument("--families", required=True, help="comma-separated families showing the wanted look")
    repair_parser.add_argument("--frontal", type=int, required=True, help="a frontal-head slot among them (scale)")
    measure_parser = commands.add_parser("measure")
    measure_parser.add_argument("--model", required=True, help="MediaPipe face_landmarker.task")
    measure_parser.add_argument("characters", nargs="*")
    args = parser.parse_args()
    if args.command == "measure":
        measure(args.model, args.characters)
    elif args.command == "verify":
        verify(args.target)
    elif args.command == "repair":
        repair(args.character, args.slots, args.families.split(","), args.frontal)
    else:
        {"survey": survey, "prepare": prepare, "extract": extract, "sheet": sheet}[args.command](args.character)


if __name__ == "__main__":
    main()
