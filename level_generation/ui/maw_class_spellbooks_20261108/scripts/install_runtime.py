"""Installs the class spellbook art into the engine icons (assets_dev/engine/icons_x2, lowercase, mode 0644) and prints
the picture table for game/rules/maw/MawClassSpells.cpp (mawClassSpellbookSkin), from runtime_x2/ as
build_mockup.py writes it.

Run: python3 -I install_runtime.py [--table-only]
"""
import json
import os
import shutil
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
RUNTIME = STUDY / "runtime_x2"
ICONS = ROOT / "assets_dev/engine/icons_x2"
LINES = {"death_knight": "DeathKnightSpellbook", "assassin": "AssassinSpellbook"}


def number(value):
    return f"{value:.1f}"


def table(skin):
    out = []
    for line, pages in skin.items():
        out.append(f"const SpellbookSkin {LINES[line]} = {{{{")
        for page in pages:
            out.append(f"    {{{page['first_spell_id']}, \"{page['page']}\", \"{page['tab']}\", "
                       f"\"{page['tab_selected']}\", {{")
            for spell in page["spells"]:
                out.append(f"        {{{spell['id']}, \"{spell['asset']}\", \"{spell['highlighted']}\", "
                           f"{{{number(spell['x'])}f, {number(spell['y'])}f, {number(spell['w'])}f, "
                           f"{number(spell['h'])}f}}}},")
            out.append("    }},")
        out.append("}};")
        out.append("")
    return "\n".join(out)


def main():
    skin = json.loads((RUNTIME / "skin.json").read_text())
    if "--table-only" not in sys.argv:
        for path in sorted(RUNTIME.glob("*.png")):
            target = ICONS / path.name.lower()
            shutil.copyfile(path, target)
            os.chmod(target, 0o644)
            print("installed", target.relative_to(ROOT))
    print(table(skin))


if __name__ == "__main__":
    main()
