"""Composites the spellbook as the game draws it (spellbook.yml): page art plus spell pictures, x2 assets."""
import sys
from pathlib import Path
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
ICONS = ROOT / "assets_dev/engine/icons_x2"
LAYOUT = yaml.safe_load((ROOT / "assets_dev/engine/ui/gameplay/spellbook.yml").read_text())


def elements():
    out = {}

    def walk(items):
        for e in items:
            out[e["id"]] = e
            walk(e.get("children", []))
    walk(LAYOUT["elements"])
    return out


def compose(page, spells, state="default", tabs=True):
    els = elements()
    canvas = Image.new("RGBA", (1280, 960))
    bg = Image.open(ICONS / f"{els[page]['asset']['default']}.png").convert("RGBA")
    canvas.alpha_composite(bg.resize((1280, 960)))
    for sid in spells:
        e = els[sid]
        img = Image.open(ICONS / f"{e['asset'][state]}.png").convert("RGBA")
        w, h = e["width"] * 2, e["height"] * 2
        img = img.resize((w, h))
        cx = 640 + e.get("offset_x", 0) * 2
        cy = 480 + e.get("offset_y", 0) * 2
        canvas.alpha_composite(img, (cx - w // 2, cy - h // 2))
    return canvas


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    els = elements()
    for page, prefix in [("SpellbookPageWater", "SpellbookPageWaterSpell"), ("SpellbookPageDarkElf", "SpellbookPageDarkElfSpell"),
                         ("SpellbookPageDark", "SpellbookPageDarkSpell"), ("SpellbookPageBody", "SpellbookPageBodySpell")]:
        ids = [k for k in els if k.startswith(prefix)]
        compose(page, ids).save(out / f"{page}_all.png")
    print([k for k in els if k.startswith("SpellbookSchoolButton")])
