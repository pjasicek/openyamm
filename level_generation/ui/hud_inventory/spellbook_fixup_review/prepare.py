"""Assemble a review-only spellbook from retained artwork and the live UI layout.

No generation, acceptance, installation, or modification of the source artwork.
The proposed icon states intentionally share the highlighted state's canvas. They
are review derivatives for a future single-texture colour treatment, not exports
that replace the differently sized legacy normal-state contracts.
"""

import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from palette import apply_palette, learn_palette
from bookmarks import RECIPE as BOOKMARK_RECIPE, comparison_sheet, make_bookmarks
from air_opacity import RECIPE as AIR_OPACITY_RECIPE, comparison_sheet as air_comparison_sheet, make_trial


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAYOUT = ROOT / "assets_dev/engine/ui/gameplay/spellbook.yml"
ICONS = ROOT / "assets_dev/engine/icons_x2"
SPELLS = ROOT / "assets_dev/engine/data_tables/spells.txt"
LABEL_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")
UI_FONT = ROOT / "assets_dev/engine/fonts/truetype/openyamm_lucida_faithful.ttf"
SCHOOL_NAMES = {"DarkElf": "Dark Elf"}
CONTROL_NAMES = {
    "SpellbookCloseButton": "Close spellbook",
    "SpellbookQuickCastButton": "Set quick spell",
    "SpellbookAttackCastButton": "Set attack spell",
}
RECIPE = {
    "version": 4,
    "base": "sbf000",
    "circle_center": [225, 190],
    "circle_radius": 90,
    "source_circle_center": [225, 190],
    "source_circle_radius": 88,
    "plaque_inner_radius": 90,
    "plaque_outer_radius": 113,
    "plaque_half_angle_degrees": 36,
    "label_font_size": 22,
    "normal_colour": "per-spell installed-default palette and contrast",
    "palette_quantiles": [0.001, 0.999, 257],
    "palette_colour_smoothing_sigma": 3,
    "palette_alpha_weight_exponent": 2,
    "glyph_search_margin": 12,
    "glyph_preservation": "green chroma inside the native sepia glyph neighborhood",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image, relative):
    path = HERE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    path.chmod(0o644)
    return {"path": relative, "sha256": digest(path), "size": list(image.size)}


def copy_source(path, relative, dependencies):
    destination = HERE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, destination)
    destination.chmod(0o644)
    dependencies[str(path.relative_to(ROOT))] = digest(path)
    return {"path": relative, "sha256": digest(destination)}


def resolve_rectangle(element, width, height):
    anchors = {
        "top_left": (0, 0), "top_center": (.5, 0), "top_right": (1, 0),
        "left": (0, .5), "center": (.5, .5), "right": (1, .5),
        "bottom_left": (0, 1), "bottom_center": (.5, 1), "bottom_right": (1, 1),
    }
    ax, ay = anchors[element["anchor"]]
    w, h = element["width"], element["height"]
    return {"x": (width - w) * ax + element.get("offset_x", 0),
            "y": (height - h) * ay + element.get("offset_y", 0),
            "width": w, "height": h}


def disk_mask(size, center, radius):
    # Analytic coverage avoids differing outline rasterization between schools.
    yy, xx = np.mgrid[:size[1], :size[0]]
    distance = np.hypot(xx - center[0], yy - center[1])
    return Image.fromarray(np.uint8(np.clip(radius + .5 - distance, 0, 1) * 255))


def plaque_shape(size):
    scale = 4
    mask = Image.new("L", (size[0] * scale, size[1] * scale))
    cx, cy = RECIPE["circle_center"]
    angle = RECIPE["plaque_half_angle_degrees"]
    middle = (RECIPE["plaque_inner_radius"] + RECIPE["plaque_outer_radius"]) / 2
    thickness = RECIPE["plaque_outer_radius"] - RECIPE["plaque_inner_radius"]
    points = []
    for radius, angles in [(RECIPE["plaque_outer_radius"], np.linspace(-angle, angle, 181)),
                           (RECIPE["plaque_inner_radius"], np.linspace(angle, -angle, 181))]:
        points.extend(((cx + radius * math.sin(math.radians(degrees))) * scale,
                       (cy - radius * math.cos(math.radians(degrees))) * scale) for degrees in angles)
    painter = ImageDraw.Draw(mask)
    painter.polygon(points, fill=255)
    cap = thickness * scale / 2
    for degrees in [-angle, angle]:
        x = (cx + middle * math.sin(math.radians(degrees))) * scale
        y = (cy - middle * math.cos(math.radians(degrees))) * scale
        painter.ellipse((x - cap, y - cap, x + cap, y + cap), fill=255)
    outline = Image.new("RGBA", mask.size)
    coverage = np.asarray(mask) > 0
    edge = coverage & ~ndimage.binary_erosion(coverage, iterations=5)
    rgba = np.zeros((mask.height, mask.width, 4), dtype=np.uint8)
    rgba[edge] = (112, 73, 29, 255)
    outline = Image.fromarray(rgba)
    return (mask.resize(size, Image.Resampling.LANCZOS),
            outline.resize(size, Image.Resampling.LANCZOS))


def curved_label(text, size):
    scale = 4
    font = ImageFont.truetype(str(LABEL_FONT), RECIPE["label_font_size"] * scale)
    layer = Image.new("RGBA", (size[0] * scale, size[1] * scale))
    spacing = 1.0 * scale
    advances = [font.getlength(letter) + spacing for letter in text]
    cursor = -sum(advances) / 2
    cx, cy = RECIPE["circle_center"]
    radius = 101
    for letter, advance in zip(text, advances):
        theta = (cursor + advance / 2) / (radius * scale)
        cursor += advance
        if letter == " ":
            continue
        box = font.getbbox(letter)
        glyph = Image.new("RGBA", (box[2] - box[0] + 24, box[3] - box[1] + 24))
        ImageDraw.Draw(glyph).text((12 - box[0], 12 - box[1]), letter, font=font, fill=(55, 29, 9, 255))
        glyph = glyph.rotate(-math.degrees(theta), Image.Resampling.BICUBIC, expand=True)
        x = (cx + radius * math.sin(theta)) * scale - glyph.width / 2
        y = (cy - radius * math.cos(theta)) * scale - glyph.height / 2
        layer.alpha_composite(glyph, (round(x), round(y)))
    return layer.resize(size, Image.Resampling.LANCZOS)


def make_pages(schools):
    base = Image.open(ICONS / (RECIPE["base"] + ".png")).convert("RGBA")
    size = base.size
    circle = disk_mask(size, RECIPE["circle_center"], RECIPE["circle_radius"])
    # Sample clean paper from this same page, beside the original medallion.
    paper = base.transform(size, Image.Transform.AFFINE, (1, 0, 260, 0, 1, 0))
    base.paste(paper, (0, 0), circle)
    plaque, outline = plaque_shape(size)
    base.paste(paper, (0, 0), plaque)
    base.alpha_composite(outline)
    common = save(base, "layers/common_book.png")
    save(circle, "layers/symbol_mask.png")
    save(plaque, "layers/name_mask.png")
    variable = Image.fromarray(np.maximum(np.asarray(circle), np.asarray(plaque)))
    # Text and antialiasing are constrained to the same variable region.
    save(variable, "layers/variable_mask.png")
    outside = np.asarray(variable) == 0
    for school in schools:
        source = Image.open(HERE / school["installed"]["path"]).convert("RGBA")
        ratio = RECIPE["source_circle_radius"] / RECIPE["circle_radius"]
        sx, sy = RECIPE["source_circle_center"]
        cx, cy = RECIPE["circle_center"]
        symbol = source.transform(size, Image.Transform.AFFINE,
                                  (ratio, 0, sx - ratio * cx, 0, ratio, sy - ratio * cy),
                                  Image.Resampling.BICUBIC)
        page = base.copy()
        page.paste(symbol, (0, 0), circle)
        # The common plaque occludes the symbol at the top of every medallion.
        page.paste(base, (0, 0), plaque)
        page.alpha_composite(outline)
        label = curved_label(school["name"].upper(), size)
        label.putalpha(Image.fromarray(np.minimum(np.asarray(label.getchannel("A")), np.asarray(plaque))))
        page.alpha_composite(label)
        # Rounded edges of the common plaque remain exactly the common pixels.
        pixels = np.asarray(page).copy()
        pixels[outside] = np.asarray(base)[outside]
        page = Image.fromarray(pixels)
        school["proposed"] = save(page, "pages/" + school["key"].lower() + ".png")
        assert np.array_equal(np.asarray(page)[outside], np.asarray(base)[outside])
    return common


def make_icon(normal, colour, name):
    pixels = np.asarray(colour).copy()
    rgb = pixels[:, :, :3].astype(np.float32)
    native = np.asarray(normal.resize(colour.size, Image.Resampling.BILINEAR)).astype(np.float32)

    def green(values):
        r, g, b, a = [values[:, :, i] for i in range(4)]
        return (g > r * 1.08 + 3) & (g > b * 1.12 + 3) & (g > 30) & (a > 20)

    # Native sepia-state green locates glyphs, avoiding green spell illustrations.
    reference = green(native)
    nearby = ndimage.binary_dilation(reference, iterations=RECIPE["glyph_search_margin"])
    r, g, b = [rgb[:, :, index] for index in range(3)]
    # Never protect rectangular patches: they can retain coloured flames beside
    # a glyph and create an obvious square seam through the sepia illustration.
    protected = (np.clip((g - r - 2) / 22, 0, 1) * np.clip((g - b - 2) / 22, 0, 1)
                 * nearby.astype(np.float32))
    palette = learn_palette(normal, colour, protected)
    output = Image.fromarray(apply_palette(colour, palette, protected))
    assert output.getchannel("A").tobytes() == colour.getchannel("A").tobytes()
    assert output.size == colour.size
    mask = save(Image.fromarray(np.uint8(np.rint(protected * 255))), "masks/" + name + ".png")
    lookup = save(Image.fromarray(palette[np.newaxis, :, :]), "palettes/" + name + ".png")
    return save(output, "icons/" + name + "-sepia.png"), mask, lookup


def spell_names():
    names = {}
    for line in SPELLS.read_text(encoding="cp1252").splitlines():
        columns = line.split("\t")
        if len(columns) > 3 and columns[0].isdigit():
            name = columns[2].strip().strip('"')
            normalized = "".join(c for c in name.lower() if c.isalnum())
            names[normalized] = name
    return names


def main():
    if (HERE / "acceptance.json").exists():
        raise SystemExit("This browser revision is accepted and installed. Preserve it and create a new review revision.")
    document = yaml.safe_load(LAYOUT.read_text())
    root = document["elements"][0]
    elements = root["children"]
    by_id = {element["id"]: element for element in elements}
    dimensions = (root["width"], root["height"])
    dependencies = {str(LAYOUT.relative_to(ROOT)): digest(LAYOUT), str(SPELLS.relative_to(ROOT)): digest(SPELLS)}
    sources = {}

    def source(name):
        name = name.lower()
        if name not in sources:
            sources[name] = copy_source(ICONS / (name + ".png"), "installed/" + name + ".png", dependencies)
        return sources[name]

    def layout(element):
        return {"id": element["id"], "rect": resolve_rectangle(element, *dimensions),
                "z": element.get("z_index", 0), "anchor": element["anchor"],
                "offset": [element.get("offset_x", 0), element.get("offset_y", 0)]}

    def button(element):
        return {**layout(element), "states": {key: source(value) for key, value in element["asset"].items()}}

    names = spell_names()
    schools = []
    mismatches = []
    for page in elements:
        if not page["id"].startswith("SpellbookPage") or "interactive" in page:
            continue
        key = page["id"].removeprefix("SpellbookPage")
        school = {**layout(page), "key": key, "name": SCHOOL_NAMES.get(key, key),
                  "installed": source(page["asset"]["default"]),
                  "button": button(by_id["SpellbookSchoolButton" + key]), "spells": []}
        prefix = page["id"] + "Spell"
        for element in elements:
            if not element["id"].startswith(prefix):
                continue
            spell = button(element)
            suffix = element["id"].removeprefix(prefix)
            spelling = "".join(c for c in suffix.lower() if c.isalnum())
            if spelling not in names:
                raise ValueError("Spell name missing from the shared table: " + suffix)
            spell["name"] = names[spelling]
            pair = element["asset"]["highlighted"].lower()[:-1]
            normal = Image.open(HERE / spell["states"]["default"]["path"]).convert("RGBA")
            colour = Image.open(HERE / spell["states"]["highlighted"]["path"]).convert("RGBA")
            spell["proposedNormal"], spell["glyphMask"], spell["normalPalette"] = make_icon(normal, colour, pair)
            spell["canonical"] = spell["states"]["highlighted"]
            spell["canonicalSize"] = list(colour.size)
            spell["originalNormalSize"] = list(normal.size)
            if normal.size != colour.size:
                mismatches.append({"id": spell["id"], "normal": list(normal.size), "canonical": list(colour.size)})
            school["spells"].append(spell)
        schools.append(school)

    common = make_pages(schools)
    bookmarks = make_bookmarks(schools, HERE, save)
    controls = [{**button(by_id[key]), "name": name} for key, name in CONTROL_NAMES.items()]
    labels = [{**layout(by_id[key]), "text": by_id[key]["text"]}
              for key in ["SpellbookSelectLabel", "SpellbookCasterName"]]
    font = copy_source(UI_FONT, "fonts/lucida.ttf", dependencies)
    recipe = {**RECIPE, "label_font": str(LABEL_FONT), "label_font_sha256": digest(LABEL_FONT),
              "bookmarks": BOOKMARK_RECIPE, "air_opacity": AIR_OPACITY_RECIPE}
    approval_path = HERE / "approved_pages_and_spells.json"
    approval = json.loads(approval_path.read_text())
    approved_targets = approval["artwork"]
    for school in schools:
        assert school["proposed"] == approved_targets[school["id"]]["proposed"], "Approved page changed"
        for spell in school["spells"]:
            for key, artifact in approved_targets[spell["id"]].items():
                if key != "kind":
                    assert spell[key] == artifact, "Approved spell changed: " + spell["id"]
    reopened = make_trial(schools, HERE, ROOT, save, digest, dependencies)
    manifest = {"schema": 1, "status": "candidate_for_review", "installed": False,
                "logicalSize": list(dimensions), "schools": schools, "controls": controls,
                "labels": labels, "common": common, "bookmarks": bookmarks, "font": font, "recipe": recipe,
                "sourceLayout": str(LAYOUT.relative_to(ROOT)), "sources": dependencies,
                "differentNativeCanvases": mismatches,
                "previousPreview": "revisions/5d48e77d7231f60b/index.html?school=Air",
                "approval": {"path": approval_path.name, "sha256": digest(approval_path),
                             "revision": approval["revision"], "date": approval["date"],
                             "targets": [key for key in approved_targets if key not in reopened],
                             "reopenedTargets": reopened},
                "checks": {"schools": len(schools), "spellPairs": sum(len(s["spells"]) for s in schools),
                           "allProposedIconAlphaIdentical": True, "allProposedIconCanvasesIdentical": True,
                           "pagePixelsIdenticalOutsideSymbolAndName": True,
                           "bookmarkStates": len(schools) * 2, "allBookmarkAlphaIdentical": True,
                           "bookmarkPixelsIdenticalOutsideEmblem": True, "approvedArtworkUnchanged": True,
                           "airOpacityPairs": len(reopened), "airTrialRGBAndGeometryUnchanged": True}}
    manifest["revision"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:16]
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (HERE / "data.js").write_text("window.SPELLBOOK_REVIEW_DATA = " + json.dumps(manifest) + ";\n")
    comparison_sheet(schools, HERE)
    air_comparison_sheet(schools, HERE)
    print(json.dumps({"revision": manifest["revision"], **manifest["checks"],
                      "differentNativeCanvases": len(mismatches)}, indent=2))


if __name__ == "__main__":
    main()
