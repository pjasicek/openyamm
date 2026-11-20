"""Builds the class spellbook mockup: page art (original page, new medallion scene and banner name), spell pictures in
their normal (sepia, derived) and highlighted (painted) states, school tabs, and pages.json for index.html.

Run from anywhere: python3 -I build_mockup.py. Inputs: masters/ (Codex), the original x2 spellbook art.
Outputs: mockup/ (web assets) and previews/ (static composites).
"""
import json
import math
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
ICONS = ROOT / "assets_dev/engine/icons_x2"
MASTERS = STUDY / "masters"
OUT = STUDY / "mockup"
PREVIEWS = STUDY / "previews"
# Lossless runtime art at x2 under the names the game binds (scripts/install_runtime.py copies it into the engine).
RUNTIME = STUDY / "runtime_x2"
RUNTIME_PREFIX = {"death_knight": "dk", "assassin": "as"}
SCHOOL_FIRST_SPELL = {"Fire Magic": 1, "Air Magic": 12, "Water Magic": 23, "Earth Magic": 34, "Body Magic": 67,
                      "Dark Magic": 89}
FONT_BANNER = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
LAYOUT = yaml.safe_load((ROOT / "assets_dev/engine/ui/gameplay/spellbook.yml").read_text())

# x2 page geometry (1280 x 960), measured from the original pages: the medallion scene disc and the banner arc.
DISC_CENTRE = (225, 190)
DISC_RADIUS = 91
BANNER_ARC_CENTRE = (225, 186)
BANNER_TOP_RADIUS = 105
BANNER_MAX_WIDTH = 118

ORIGINAL_PAGES = ["sbf000", "sba000", "sbw000", "sbe000", "sbs000", "sbm000", "sbb000", "sbl000", "sbdk000",
                  "sbde000", "sbv000", "sbd000"]
SCHOOL_PAGES = ["Fire", "Air", "Water", "Earth", "Spirit", "Mind", "Body", "Light", "Dark"]

# Slots in 640 x 480 book units: centre x, centre y, box width, box height. Reading order follows mastery.
SLOTS = {
    4: [(212, 180, 165, 140), (165, 352, 215, 180), (470, 150, 220, 180), (470, 352, 220, 180)],
    5: [(212, 180, 165, 140), (165, 355, 205, 165), (470, 105, 200, 132), (462, 245, 200, 132), (470, 385, 200, 132)],
    6: [(215, 175, 160, 125), (110, 302, 150, 118), (215, 405, 175, 118), (470, 105, 200, 132),
        (462, 245, 200, 132), (470, 385, 200, 132)],
}

MASTERY = ["Unskilled", "Novice", "Expert", "Master", "Grandmaster"]

# Spells per page, in mastery order: (spell id, name, mastery index 0-4, art source, MAW name if renamed, note).
# Art source "new:<master stem>" is a Codex picture; "orig:<id>" the original picture of that spell.
BOOKS = {
    "death_knight": {
        "title": "Death Knight",
        "caster": "Morwen, Death Knight",
        "today_tabs": ["Water", "Body", "Dark"],
        "pages": [
            {"school": "Frost", "skill": "Water Magic", "medallion": "med_frost", "tab": "tab_frost", "spells": [
                (26, "Icy Touch", 1, "new:dk_26_icy_touch", None,
                 "Deals a share of your weapon damage to one target; from Expert it slows."),
                (27, "Water Walk", 2, "new:dk_27_water_walk", None, "The ordinary Water Walk."),
                (29, "Frostbite", 3, "new:dk_29_frostbite", None,
                 "The Death Knight's strongest single-target strike: 150-200 % of weapon damage."),
                (32, "Ice Bomb", 4, "new:dk_32_ice_bomb", None,
                 "An ice bomb that shatters on impact; each shard deals 75 % of weapon damage."),
            ]},
            {"school": "Blood", "skill": "Body Magic", "medallion": "med_blood", "tab": "tab_blood", "spells": [
                (68, "Blood Leech", 1, "new:dk_68_blood_leech", None,
                 "A switch: while on, every blow leeches life for 6 spell points."),
                (71, "Regeneration", 2, "new:dk_71_regeneration", None, "The ordinary Regeneration aura."),
                (76, "Asphyxiate", 3, "new:dk_76_asphyxiate", None,
                 "Weapon damage and the target cannot act for a moment."),
                (74, "Superior Blood Leech", 4, "new:dk_74_superior_blood_leech", None,
                 "A switch: twice Blood Leech's life per blow, for 12 spell points."),
            ]},
            {"school": "Unholy", "skill": "Dark Magic", "medallion": "med_unholy", "tab": "tab_unholy", "spells": [
                (91, "Vampiric Aura", 1, "new:dk_91_vampiric_aura", None, "MAW's Vampiric Aura: blows leech life."),
                (90, "Death Coil", 2, "new:dk_90_death_coil", None,
                 "A bolt of weapon damage that heals you by a share of what it deals."),
                (96, "Death Grasp", 3, "new:dk_96_death_grasp", None,
                 "A switch: while on, every blow weakens its target, for 15 spell points."),
                (97, "Death Breath", 4, "new:dk_97_death_breath", None,
                 "A blast dealing 60 % of weapon damage to every monster in the area."),
            ]},
        ],
    },
    "assassin": {
        "title": "Assassin",
        "caster": "Sable, Assassin",
        "today_tabs": ["Fire", "Air", "Water", "Earth"],
        "pages": [
            {"school": "Combat", "skill": "Fire Magic", "medallion": "med_combat", "tab": "tab_combat", "spells": [
                (1, "Torch Light", 0, "orig:1", None, "The ordinary Torch Light."),
                (4, "Fire Aura", 1, "orig:4", None, "The ordinary Fire Aura."),
                (5, "Haste", 2, "orig:5", None, "The ordinary Haste."),
                (6, "Firebomb", 3, "new:as_06_firebomb", "Fireball",
                 "5 combo points: a bomb that bursts for a melee blow's damage around its target."),
                (7, "Blasting Trap", 4, "new:as_07_blasting_trap", "Fire Spike",
                 "3 combo points: a trap that waits and explodes for 250 % of a melee blow."),
            ]},
            {"school": "Subtlety", "skill": "Air Magic", "medallion": "med_subtlety", "tab": "tab_subtlety", "spells": [
                (12, "Wizard Eye", 0, "orig:12", None, "The ordinary Wizard Eye."),
                (17, "Shield", 0, "orig:17", None, "The ordinary Shield."),
                (16, "Jump", 1, "orig:16", None, "The ordinary Jump."),
                (18, "Ricochet Blade", 2, "new:as_18_ricochet_blade", "Chain Lightning",
                 "5 combo points: 150 % of a melee blow, leaping to 2-4 targets."),
                (21, "Fly", 3, "orig:21", None, "The ordinary Fly."),
                (19, "Invisibility", 4, "orig:19", None, "The ordinary Invisibility."),
            ]},
            {"school": "Poisons", "skill": "Water Magic", "medallion": "med_poisons", "tab": "tab_poisons", "spells": [
                (24, "Poison Darts", 0, "new:as_24_poison_darts", "Poison Spray",
                 "3 combo points: a spread of darts, each 75 % of a melee blow."),
                (27, "Water Walk", 1, "orig:27", None, "The ordinary Water Walk."),
                (29, "Acid Flask", 2, "new:as_29_acid_flask", "Acid Burst",
                 "3 combo points: a flask of acid for 300 % of a melee blow."),
                (31, "Town Portal", 3, "orig:31", None, "The ordinary Town Portal."),
                (33, "Lloyd's Beacon", 4, "orig:33", None, "The ordinary Lloyd's Beacon."),
            ]},
            {"school": "Assassination", "skill": "Earth Magic", "medallion": "med_assassination",
             "tab": "tab_assassination", "spells": [
                (34, "Sap", 0, "new:as_34_sap", "Stun", "3 combo points: 150 % of a melee blow and a stun."),
                (38, "Stone Skin", 1, "orig:38", None, "The ordinary Stone Skin."),
                (39, "Throwing Blades", 2, "new:as_39_throwing_blades", "Blades",
                 "3 combo points: 300 % of a melee blow as physical damage."),
                (42, "Telekinesis", 3, "orig:42", None, "The ordinary Telekinesis."),
                (44, "Death Mark", 4, "new:as_44_death_mark", "Mass Distortion",
                 "4 combo points: 400 % of a melee blow, crushing the target."),
            ]},
        ],
    },
}


def layout_elements():
    out = {}

    def walk(items):
        for element in items:
            out[element["id"]] = element
            walk(element.get("children", []))

    walk(LAYOUT["elements"])
    return out


ELEMENTS = layout_elements()


def original_spell_element(spell_id):
    school = SCHOOL_PAGES[(spell_id - 1) // 11]
    ordinal = (spell_id - 1) % 11
    prefix = f"SpellbookPage{school}Spell"
    return [element for key, element in ELEMENTS.items() if key.startswith(prefix)][ordinal]


def load_icon(name):
    return Image.open(ICONS / f"{name.lower()}.png").convert("RGBA")


def clean_page():
    """The Water page with its banner word removed (the lightest pixel of the twelve original pages)."""
    stack = np.stack([np.asarray(load_icon(page)) for page in ORIGINAL_PAGES]).astype(np.int32)
    lightest = stack[..., :3].sum(axis=3).argmax(axis=0)
    clean = np.take_along_axis(stack, lightest[None, ..., None].repeat(4, axis=3), axis=0)[0]
    page = np.asarray(load_icon("sbw000")).copy()
    page[60:118, 140:310] = clean[60:118, 140:310]
    return Image.fromarray(page.astype(np.uint8)), stack


def tone_ramp(pixels):
    """Colour by luminance (256 entries) from a set of RGB pixels: the median colour of each luminance band."""
    lum = pixels @ np.array([0.299, 0.587, 0.114])
    ramp = np.zeros((256, 3))
    order = np.argsort(lum)
    sorted_pixels = pixels[order]
    sorted_lum = lum[order]
    for level in range(256):
        lo, hi = np.searchsorted(sorted_lum, [level - 6, level + 6])
        if hi > lo:
            ramp[level] = np.median(sorted_pixels[lo:hi], axis=0)
        else:
            ramp[level] = np.nan
    valid = ~np.isnan(ramp[:, 0])
    for channel in range(3):
        ramp[:, channel] = np.interp(np.arange(256), np.nonzero(valid)[0], ramp[valid, channel])
    return ramp


def match_tones(image, reference_pixels):
    """Maps an image's luminance quantiles onto the tones of reference pixels (keeps alpha)."""
    rgba = np.asarray(image.convert("RGBA")).astype(np.float64)
    lum = rgba[..., :3] @ np.array([0.299, 0.587, 0.114])
    ref_lum = np.sort(reference_pixels @ np.array([0.299, 0.587, 0.114]))
    visible = rgba[..., 3] > 8
    ranks = np.searchsorted(np.sort(lum[visible]), lum) / max(1, visible.sum())
    target_lum = np.interp(ranks, np.linspace(0, 1, len(ref_lum)), ref_lum)
    ramp = tone_ramp(reference_pixels)
    out = ramp[np.clip(target_lum, 0, 255).astype(int)]
    rgba[..., :3] = out
    return Image.fromarray(rgba.astype(np.uint8))


def sepia_state(highlighted, ramp):
    """The normal (sepia) state of a painted picture: its luminance on the originals' sepia ramp; the large green
    rune keeps its colour, as the originals' does."""
    rgba = np.asarray(highlighted).astype(np.float64)
    rgb = rgba[..., :3]
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    toned = ramp[np.clip(lum, 0, 255).astype(int)]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # The rune ink is a cool green (blue near red); necrotic or poison glows are yellow-green and get toned.
    green_rune = (g > r * 1.15) & (g > b * 1.05) & (b > r * 0.75) & (g - np.minimum(r, b) < 55) & (lum < 150) & (lum > 25)
    toned[green_rune] = rgb[green_rune]
    rgba[..., :3] = toned
    return Image.fromarray(rgba.astype(np.uint8))


def original_sepia_ramp():
    pixels = []
    for name in ["sbw04b", "sbdk08b", "sbb03b", "sbf06b", "sbde04b", "sbv01b"]:
        array = np.asarray(load_icon(name)).reshape(-1, 4)
        pixels.append(array[array[:, 3] > 200][:, :3])
    pixels = np.concatenate(pixels).astype(np.float64)
    r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
    not_green = ~((g > r * 1.15) & (g > b * 1.05))
    return tone_ramp(pixels[not_green])


def banner_text(page, word):
    """Draws the school name along the banner arc in dark brown capitals."""
    word = word.upper()
    size = 29
    while True:
        font = ImageFont.truetype(FONT_BANNER, size)
        spacing = 1.0
        widths = [font.getlength(ch) for ch in word]
        total = sum(widths) + spacing * (len(word) - 1)
        if total <= BANNER_MAX_WIDTH or size <= 12:
            break
        size -= 1
    radius = BANNER_TOP_RADIUS
    angle = -total / 2 / radius
    cx, cy = BANNER_ARC_CENTRE
    # The cap box of the font ('H'): each glyph is cut to it, so its centre is half a cap height below the arc.
    _, cap_top, _, cap_bottom = font.getbbox("H")
    cap_height = cap_bottom - cap_top
    for ch, width in zip(word, widths):
        mid = angle + width / 2 / radius
        glyph = Image.new("RGBA", (int(width) + 8, cap_bottom + 8), (0, 0, 0, 0))
        ImageDraw.Draw(glyph).text((4, 0), ch, font=font, fill=(46, 28, 16, 255))
        glyph = glyph.crop((0, cap_top - 2, glyph.width, cap_bottom + 2))
        rotated = glyph.rotate(-math.degrees(mid), resample=Image.BICUBIC, expand=True)
        centre_radius = radius - cap_height / 2
        gx = cx + centre_radius * math.sin(mid)
        gy = cy - centre_radius * math.cos(mid)
        page.alpha_composite(rotated, (int(round(gx - rotated.width / 2)), int(round(gy - rotated.height / 2))))
        angle += (width + spacing) / radius


def medallion_page(base, scene_stem, word, disc_pixels):
    page = base.copy()
    scene_path = MASTERS / f"{scene_stem}.png"
    size = DISC_RADIUS * 2 + 4
    if scene_path.exists():
        scene = Image.open(scene_path).convert("RGBA").resize((size, size), Image.LANCZOS)
        scene = match_tones(scene, disc_pixels)
    else:
        scene = Image.new("RGBA", (size, size), (120, 90, 60, 255))
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((8, 8, size * 4 - 8, size * 4 - 8), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    scene.putalpha(mask)
    page.alpha_composite(scene, (DISC_CENTRE[0] - size // 2, DISC_CENTRE[1] - size // 2))
    # The ring's inner edge draws over the scene again, as on the originals.
    ring = base
    ring_mask = Image.new("L", ring.size, 0)
    ImageDraw.Draw(ring_mask).ellipse((DISC_CENTRE[0] - 98, DISC_CENTRE[1] - 98, DISC_CENTRE[0] + 98,
                                       DISC_CENTRE[1] + 98), fill=255)
    ImageDraw.Draw(ring_mask).ellipse((DISC_CENTRE[0] - DISC_RADIUS + 2, DISC_CENTRE[1] - DISC_RADIUS + 2,
                                       DISC_CENTRE[0] + DISC_RADIUS - 2, DISC_CENTRE[1] + DISC_RADIUS - 2), fill=0)
    page.paste(ring, (0, 0), ring_mask)
    banner_text(page, word)
    return page


def disc_tone_pixels(stack):
    pixels = []
    yy, xx = np.mgrid[0:960, 0:1280]
    inside = (xx - DISC_CENTRE[0]) ** 2 + (yy - DISC_CENTRE[1]) ** 2 < (DISC_RADIUS - 6) ** 2
    for page in stack[:9]:
        pixels.append(page[inside][:, :3])
    return np.concatenate(pixels).astype(np.float64)[::7]


def tab_images():
    """Tab frames: the idle and selected originals with their emblem discs measured, to paste new emblems into."""
    idle = [np.asarray(load_icon(n)).astype(np.int32) for n in ["stfd", "stad", "stwd", "sted", "stsd", "stmd",
                                                                   "stbd", "stld", "stdd"]]
    stack = np.stack(idle)
    lightest = stack[..., :3].sum(axis=3).argmax(axis=0)
    clean_idle = np.take_along_axis(stack, lightest[None, ..., None].repeat(4, axis=3), axis=0)[0]
    return Image.fromarray(clean_idle.astype(np.uint8)), load_icon("stwu")


def tab_disc(frame):
    """The emblem disc of a tab (x2): centre and radius from the selected Water tab's painted disc."""
    array = np.asarray(frame).astype(np.int32)
    r, g, b = array[..., 0], array[..., 1], array[..., 2]
    blue = (b > r + 25) & (array[..., 3] > 200)
    ys, xs = np.nonzero(blue)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    radius = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2
    return cx, cy, radius


def build_tab(stem, clean_idle, selected_frame, disc):
    cx, cy, radius = disc
    results = {}
    for state, frame in (("d", clean_idle), ("u", selected_frame)):
        tab = frame.copy()
        path = MASTERS / f"{stem}_{state}.png"
        if path.exists():
            emblem = Image.open(path).convert("RGBA")
            diameter = int(round(radius * 2 + (7 if state == "u" else -6)))
            emblem = emblem.resize((diameter, diameter), Image.LANCZOS)
            if state == "u":
                mask = Image.new("L", (diameter * 4, diameter * 4), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, diameter * 4, diameter * 4), fill=255)
                mask = mask.resize((diameter, diameter), Image.LANCZOS)
                alpha = Image.fromarray(np.minimum(np.asarray(emblem.getchannel("A")), np.asarray(mask)))
                emblem.putalpha(alpha)
            tab.alpha_composite(emblem, (int(round(cx - diameter / 2)), int(round(cy - diameter / 2))))
        results[state] = tab
    return results


def fit(image, box_w, box_h):
    scale = min(box_w / image.width, box_h / image.height)
    return image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)


def main():
    OUT.mkdir(exist_ok=True)
    PREVIEWS.mkdir(exist_ok=True)
    RUNTIME.mkdir(exist_ok=True)
    runtime_skin = {}
    base, stack = clean_page()
    disc_pixels = disc_tone_pixels(stack)
    ramp = original_sepia_ramp()
    clean_idle, selected_frame = tab_images()
    disc = tab_disc(selected_frame)
    data = {"books": []}

    for book_id, book in BOOKS.items():
        book_out = {"id": book_id, "title": book["title"], "caster": book["caster"], "pages": [], "today": []}
        prefix = RUNTIME_PREFIX[book_id]
        runtime_skin[book_id] = []
        for page_def in book["pages"]:
            school = page_def["school"]
            page_image = medallion_page(base, page_def["medallion"], school, disc_pixels)
            page_file = f"page_{book_id}_{school.lower()}.webp"
            page_image.save(OUT / page_file, quality=90)
            runtime_page = {"first_spell_id": SCHOOL_FIRST_SPELL[page_def["skill"]],
                            "page": f"maw_sb{prefix}_{school.lower()}",
                            "tab": f"maw_st{prefix}_{school.lower()}_d",
                            "tab_selected": f"maw_st{prefix}_{school.lower()}_u", "spells": []}
            page_image.save(RUNTIME / f"{runtime_page['page']}.png")
            tabs = build_tab(page_def["tab"], clean_idle, selected_frame, disc)
            for state, image in tabs.items():
                image.save(OUT / f"{page_def['tab']}_{state}.png")
                image.save(RUNTIME / f"maw_st{prefix}_{school.lower()}_{state}.png")
            slots = SLOTS[len(page_def["spells"])]
            spells_out = []
            for (spell_id, name, mastery, source, maw_name, note), slot in zip(page_def["spells"], slots):
                stem = f"spell_{book_id}_{spell_id}"
                if source.startswith("new:"):
                    master = MASTERS / f"{source[4:]}.png"
                    if master.exists():
                        highlighted = Image.open(master).convert("RGBA")
                    else:
                        highlighted = Image.new("RGBA", (300, 240), (200, 60, 60, 120))
                    normal = sepia_state(highlighted, ramp)
                    box_w, box_h = slot[2] * 2, slot[3] * 2
                else:
                    element = original_spell_element(int(source[5:]))
                    normal = load_icon(element["asset"]["default"])
                    highlighted = load_icon(element["asset"]["highlighted"])
                    # Originals keep their native size, shrunk only to fit the slot.
                    box_w = min(slot[2], element["width"]) * 2
                    box_h = min(slot[3], element["height"]) * 2
                normal = fit(normal, box_w, box_h)
                highlighted = fit(highlighted, box_w, box_h)
                normal.save(OUT / f"{stem}_b.webp", quality=88)
                highlighted.save(OUT / f"{stem}_a.webp", quality=88)
                if source.startswith("new:"):
                    asset = f"maw_sb{prefix}{spell_id:02d}"
                    normal.save(RUNTIME / f"{asset}b.png")
                    highlighted.save(RUNTIME / f"{asset}a.png")
                    assets = (f"{asset}b", f"{asset}a")
                else:
                    assets = (element["asset"]["default"].lower(), element["asset"]["highlighted"].lower())
                runtime_page["spells"].append({
                    "id": spell_id, "asset": assets[0], "highlighted": assets[1],
                    "x": round(slot[0] - normal.width / 4, 1), "y": round(slot[1] - normal.height / 4, 1),
                    "w": round(normal.width / 2, 1), "h": round(normal.height / 2, 1)})
                spells_out.append({
                    "id": spell_id, "name": name, "mastery": MASTERY[mastery], "maw_name": maw_name, "note": note,
                    "new_art": source.startswith("new:"), "x": slot[0], "y": slot[1],
                    "w": normal.width / 2, "h": normal.height / 2, "b": f"{stem}_b.webp", "a": f"{stem}_a.webp",
                })
            runtime_skin[book_id].append(runtime_page)
            book_out["pages"].append({"school": school, "skill": page_def["skill"], "page": page_file,
                                      "tab_d": f"{page_def['tab']}_d.png", "tab_u": f"{page_def['tab']}_u.png",
                                      "spells": spells_out})

        # Today: the original school pages with only this class's spells drawn, under their MAW names.
        for school_name, page_def in zip(book["today_tabs"], book["pages"]):
            school_index = SCHOOL_PAGES.index(school_name)
            page_file = f"today_{school_name.lower()}.webp"
            load_icon(ORIGINAL_PAGES[school_index]).save(OUT / page_file, quality=90)
            button = ELEMENTS[f"SpellbookSchoolButton{school_name}"]["asset"]
            for state, key in (("d", "default"), ("u", "pressed")):
                load_icon(button[key]).save(OUT / f"today_tab_{school_name.lower()}_{state}.png")
            spells_out = []
            for spell_id, name, mastery, source, maw_name, note in page_def["spells"]:
                element = original_spell_element(spell_id)
                stem = f"today_spell_{spell_id}"
                load_icon(element["asset"]["default"]).save(OUT / f"{stem}_b.webp", quality=88)
                load_icon(element["asset"]["highlighted"]).save(OUT / f"{stem}_a.webp", quality=88)
                table_name = element["id"].split("Spell", 1)[1]
                spells_out.append({
                    "id": spell_id, "name": maw_name or name, "mastery": MASTERY[mastery], "picture_of": table_name,
                    "x": 320 + element.get("offset_x", 0), "y": 240 + element.get("offset_y", 0),
                    "w": element["width"], "h": element["height"], "b": f"{stem}_b.webp", "a": f"{stem}_a.webp",
                })
            book_out["today"].append({"school": f"{school_name} Magic", "page": page_file,
                                      "tab_d": f"today_tab_{school_name.lower()}_d.png",
                                      "tab_u": f"today_tab_{school_name.lower()}_u.png",
                                      "tab_slot": school_index, "spells": spells_out})
        data["books"].append(book_out)

    for name in ["stxtu", "stssu", "gf-aspell"]:
        load_icon(name).save(OUT / f"{name}.png")
    (OUT / "pages.json").write_text(json.dumps(data, indent=1))
    (RUNTIME / "skin.json").write_text(json.dumps(runtime_skin, indent=1))
    template = (STUDY / "scripts/index.template.html").read_text()
    (STUDY / "index.html").write_text(template.replace("/*PAGES_JSON*/null", json.dumps(data)))
    render_previews(data)


def render_previews(data):
    """Static composites of every proposed page (normal state) for the README."""
    for book in data["books"]:
        for index, page in enumerate(book["pages"]):
            canvas = Image.open(OUT / page["page"]).convert("RGBA")
            for spell in page["spells"]:
                image = Image.open(OUT / spell["b"]).convert("RGBA")
                canvas.alpha_composite(image, (int(spell["x"] * 2 - image.width / 2),
                                               int(spell["y"] * 2 - image.height / 2)))
            for tab_index, other in enumerate(book["pages"]):
                tab = Image.open(OUT / (other["tab_u"] if tab_index == index else other["tab_d"])).convert("RGBA")
                canvas.alpha_composite(tab, (1280 - tab.width, 4 + tab_index * 78))
            canvas.convert("RGB").save(PREVIEWS / f"{book['id']}_{page['school'].lower()}.png")


if __name__ == "__main__":
    main()
