"""Undo the recorded global Air ink fade, retaining RGB, geometry and soft edges."""

import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont


PROCESSING = {
    "sba01": "wizard_eye_fitted_v1",
    "sba02": "layout_air_v1/feather",
    "sba03": "layout_air_v1/air_resistance",
    "sba05": "jump_final_review",
    "sba06": "shield_native_assessment_v1",
    "sba07": "lightning_assessment_v1",
    "sba08": "invisibility_final_review",
    "sba09": "layout_air_v1/implosion",
    "sba10": "layout_air_v1/fly",
}
RECIPE = {
    "operation": "alpha = round(min(255, previous_alpha / recorded_ink_opacity)); RGB unchanged",
    "source": "level_generation/ui/hud_inventory/pilots/air_spells",
    "processing_directories": PROCESSING,
    "baseline_revision": "5d48e77d7231f60b",
    "scope": "Nine attenuated Air pairs; Sparks and Starburst retain their existing alpha",
}


def make_trial(schools, directory, root, save, digest, dependencies):
    changed = []
    school = next(school for school in schools if school["key"] == "Air")
    for spell in school["spells"]:
        pair = spell["canonical"]["path"].split("/")[-1][:-5]
        if pair not in PROCESSING:
            continue
        source_directory = root / RECIPE["source"] / PROCESSING[pair]
        record = source_directory / "processing.json"
        ink = source_directory / (pair + "a-ink.png")
        assert digest(ink) == spell["canonical"]["sha256"], "Air ink source changed: " + pair
        factor = json.loads(record.read_text())["ink_opacity"]
        assert factor == (.85 if pair == "sba03" else .75), pair
        for path in [record, ink]:
            dependencies[str(path.relative_to(root))] = digest(path)
        trial = {"previousOpacity": factor, "processingRecord": str(record.relative_to(root)),
                 "processingRecordSha256": digest(record)}
        for state, key in [("normal", "proposedNormal"), ("highlighted", "canonical")]:
            image = Image.open(directory / spell[key]["path"]).convert("RGBA")
            pixels = np.asarray(image).copy()
            assert int(pixels[:, :, 3].max()) == round(255 * factor), pair
            pixels[:, :, 3] = np.uint8(np.rint(np.minimum(255, pixels[:, :, 3].astype(np.float64) / factor)))
            trial[state] = save(Image.fromarray(pixels), "air_opacity/" + pair + "-" + state + ".png")
        spell["opacityTrial"] = trial
        changed.append(spell["id"])
    assert len(changed) == 9
    return changed


def comparison_sheet(schools, directory):
    spells = next(school for school in schools if school["key"] == "Air")["spells"]
    spells = [spell for spell in spells if "opacityTrial" in spell]
    sheet = Image.new("RGB", (1740, 1080), (32, 32, 29))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(directory / "fonts/lucida.ttf"), 18)
    small = ImageFont.truetype(str(directory / "fonts/lucida.ttf"), 14)
    draw.text((20, 12), "Air magic — previous / restored strength", font=font, fill="#f1dfbd")
    draw.text((20, 41), "Same drawings and colours; the old overall fade is removed in both game states.",
              font=small, fill="#c8baa0")
    paper = Image.open(directory / "layers/common_book.png").convert("RGBA").crop((850, 360, 1122, 642))
    for index, spell in enumerate(spells):
        x, y = index % 3 * 580 + 10, index // 3 * 334 + 70
        draw.text((x + 5, y), spell["name"], font=font, fill="#f1dfbd")
        for column, (label, artifact) in enumerate([("Previous", spell["proposedNormal"]),
                                                   ("Restored", spell["opacityTrial"]["normal"])]):
            image = Image.open(directory / artifact["path"]).convert("RGBA")
            image.thumbnail((264, 274), Image.Resampling.LANCZOS)
            cell = paper.copy()
            cell.alpha_composite(image, ((272 - image.width) // 2, (282 - image.height) // 2))
            sheet.paste(cell.convert("RGB"), (x + column * 285, y + 24))
            draw.text((x + column * 285 + 6, y + 308), label, font=small, fill="#c8baa0")
    sheet.save(directory / "evidence/air_strength_comparison.png")
