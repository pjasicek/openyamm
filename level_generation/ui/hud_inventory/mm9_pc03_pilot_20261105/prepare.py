"""Prepare the MM9 PC03 portrait pilot: MM9 frames remapped into the 56 MM6-MM8 portrait slots.

Each sheet gets two reference images in the 7x4 layout of the accepted 2026-09-27 PC restoration
(1092x728, 156x182 slots, 118x158 windows at inset 19,12):
  template_<A|B>.png  accepted transparent pc07 x2 frames: framing, head size, crop, lighting, state treatment
  source_<A|B>.png    MM9 PC03 frames chosen for each slot, 2x nearest: identity and expression
plus identity.png, MM9 PC03 frame 1 at 4x.
"""

import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MM9 = ROOT / "mm9/extracted/ART/ART/PCPORTRAITS/PC03"
TEMPLATE = ROOT / "assets_dev/engine/icons_x2"
TEMPLATE_FAMILY = "pc07"
SLOT = (156, 182)
INSET = (19, 12)
SHEET = (1092, 728)

# Our slot -> (meaning, MM9 PC03 frame used as identity/expression source, who controls the state).
# "mm9": the MM9 frame already shows this state; "template": take head angle/state/tint from pc07.
MAPPING = {
    1: ("neutral", 1, "mm9"),
    2: ("cursed: heavy-lidded, drained", 31, "template"),
    3: ("weak: eyes almost closed, tired", 31, "template"),
    4: ("asleep: eyes closed, head tilted", 32, "template"),
    5: ("fear: wide eyes, open mouth", 49, "template"),
    6: ("drunk: tilted, loose grin", 30, "template"),
    7: ("insane: manic grin", 23, "template"),
    8: ("poisoned: sickly green skin", 33, "template"),
    9: ("diseased: pustules", 2, "template"),
    10: ("paralyzed: fixed stare", 10, "template"),
    11: ("unconscious: eyes closed, bruise, tilted", 36, "template"),
    12: ("petrified: grey stone", 53, "mm9"),
    13: ("blink", 4, "mm9"),
    14: ("wink", 6, "mm9"),
    15: ("mouth slightly open", 41, "mm9"),
    16: ("lips pursed", 25, "mm9"),
    17: ("look up", 13, "template"),
    18: ("glance to its own left, head slightly turned the other way (repaired in repair_18_48/)", 3, "template"),
    19: ("look left", 7, "template"),
    20: ("look down", 18, "template"),
    21: ("talk: mouth closed", 18, "mm9"),
    22: ("talk: mouth open", 42, "mm9"),
    23: ("talk: open smile, teeth", 20, "mm9"),
    24: ("talk: O mouth", 50, "mm9"),
    25: ("head shake: turned far", 7, "template"),
    26: ("head shake: turned half", 7, "template"),
    27: ("head shake: slightly turned", 1, "template"),
    28: ("head shake: half, other side", 9, "template"),
    29: ("head shake: far, other side", 9, "template"),
}
MAPPING.update({
    30: ("nod: head up", 14, "template"),
    31: ("nod: slightly up", 13, "template"),
    32: ("nod: level", 1, "template"),
    33: ("nod: down", 18, "template"),
    34: ("dodge: head tilted aside", 9, "template"),
    35: ("dodge: ducking low", 28, "template"),
    36: ("dodge: almost out of frame", 29, "template"),
    37: ("hit, minor: bruise, wince", 8, "template"),
    38: ("hit, moderate: cuts, head turned", 14, "template"),
    39: ("hit, major: battered, mouth open", 11, "template"),
    40: ("smile", 12, "mm9"),
    41: ("wide smile", 21, "mm9"),
    42: ("frown", 26, "mm9"),
    43: ("casting: eyes squeezed shut", 36, "template"),
    44: ("determined, lips parted", 17, "template"),
    45: ("pout", 25, "template"),
    46: ("scared: raised brows", 27, "mm9"),
    47: ("eyes closed, calm", 31, "template"),
    48: ("smug smile (corrected 2026-11-05: was \"stern\"; repaired in repair_18_48/)", 15, "template"),
    49: ("disgust: tongue out", 38, "mm9"),
    50: ("happy", 19, "mm9"),
    51: ("suspicious squint", 15, "template"),
    52: ("slight smile", 15, "mm9"),
    53: ("angry", 17, "mm9"),
    54: ("enraged: red face, snarl", 24, "template"),
    55: ("grin", 22, "mm9"),
    56: ("shout, mouth wide open", 23, "mm9"),
})


def place(sheet, image, slot):
    x = slot % 7 * SLOT[0] + INSET[0]
    y = slot // 7 * SLOT[1] + INSET[1]
    sheet.alpha_composite(image, (x, y))


def main():
    assert sorted(MAPPING) == list(range(1, 57))
    for letter, first in (("A", 1), ("B", 29)):
        template = Image.new("RGBA", SHEET)
        source = Image.new("RGBA", SHEET)
        for slot in range(28):
            number = first + slot
            _, mm9_frame, _ = MAPPING[number]
            frame = Image.open(TEMPLATE / f"{TEMPLATE_FAMILY}-{number:02d}.png").convert("RGBA")
            assert frame.size == (118, 158)
            place(template, frame, slot)
            mm9 = Image.open(MM9 / f"PC-03-{mm9_frame:02d}.pcx").convert("RGBA")
            # 60x80 -> 120x160 nearest; drop the extra column/row so it sits in the same 118x158 window.
            place(source, mm9.resize((120, 160), Image.Resampling.NEAREST).crop((1, 1, 119, 159)), slot)
        template.save(HERE / f"template_{letter}.png")
        source.save(HERE / f"source_{letter}.png")
    Image.open(MM9 / "PC-03-01.pcx").convert("RGB").resize((240, 320), Image.Resampling.LANCZOS).save(
        HERE / "identity.png")
    mapping = {str(k): {"meaning": v[0], "mm9_frame": v[1], "state_from": v[2]} for k, v in MAPPING.items()}
    (HERE / "mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")


if __name__ == "__main__":
    main()
