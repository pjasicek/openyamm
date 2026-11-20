#!/usr/bin/env python3
"""MM9's player-character voices as OpenYAMM voice sets (devdocs/mm9_rework/MM9_PC_VOICES.md).

MM9 has 18 voice sets (VOICES/PC: seven personalities and two lich voices, female and male), each with up to three takes
of 42 lines, listed by DATA/PCVOICES/<SET>.txt (the authority: file numbers differ between sets). This script

- converts every listed take to IMA ADPCM WAV (the engine's own voices' format, 22 050 Hz mono, as MM9's) at
  worlds/mm9/audio/voices/pc/<set>/<file>.wav (lower case);
- writes worlds/mm9/data_tables/pc_voice_sounds.txt (the world's sounds, ids 55000-58599: 55000 + 200 x set + 3 x line +
  take; 50000-54999 are generate_mm9_monster_sounds.py's), contributed by worlds/mm9/world.yml;
- writes the voice sets as columns 79-96 of engine/data_tables/character_voices.txt (79 + MM9's own getPCVoice number:
  female Angry ... Half-Orc Lich 0-8, male 9-17), each MM9 line in the sound types of the matching speech, third takes
  in rows of their own, and the sets' Name, World and Man / Woman / Undead Man / Undead Woman rows.

    python3 tools/mm9_import_discovery/generate_mm9_pc_voices.py [--check]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PC = ROOT / "mm9/extracted/VOICES/VOICES/PC"
TABLES = ROOT / "mm9/extracted/DATA/DATA/PCVOICES"
AUDIO = ROOT / "assets_dev/worlds/mm9/audio"
SOUNDS = ROOT / "assets_dev/worlds/mm9/data_tables/pc_voice_sounds.txt"
VOICES = ROOT / "assets_dev/engine/data_tables/character_voices.txt"
FIRST_SET = 79
FIRST_SOUND = 55000

# MM9's getPCVoice order (FATEMAN.scr :Init): (table, folder, name, female, lich)
PERSONALITIES = ["Angry", "Arrogant", "Assertive", "Cowardly", "Dim", "Happy", "Sarcastic", "Lich", "Half-Orc Lich"]
SETS = []
for female in (True, False):
    for name in PERSONALITIES:
        key = name.replace("-", "").replace(" ", "").upper() + ("F" if female else "M")
        folder = name.replace("-", " ").upper() + (" FEMALE" if female else " MALE")
        SETS.append((key, folder, name, female, "Lich" in name))

# MM9's 42 lines (0-41, the tables' rows) -> the OpenYAMM sound types that play them, in the voice table's own rows. A
# group's takes fill its rows in order; more takes than rows get rows of their own under the group's last type name.
# Lines 13 (cannot talk, danger nearby) and 37 (No) have no speech in OpenYAMM.
GROUPS = [
    (["Disarmed", "Disarmed"], [0]),
    (["Closed1", "Closed2"], [1]),
    (["FailedDisarm1", "FailedDisarm2"], [2]),
    (["ChooseMe1", "ChooseMe2"], [3]),
    (["BadItem1", "BadItem2"], [4]),
    (["GoodItem1", "GoodItem2"], [5]),
    (["CantIdent1", "CantIdent2"], [6]),
    (["Repaired1", "Repaired2"], [7]),
    (["CantRep1", "CantRep2"], [8]),
    (["WeakMonster1", "WeakMonster2"], [9]),
    (["BigMonster1", "BigMonster2"], [10]),
    (["CantIdMon1", "CantIdMon2"], [11]),
    (["QuickSpell1", "QuickSpell2"], [12]),
    (["SoftInjure1", "SoftInjure1"], [14, 15]),
    (["HardInjured1", "HardInjured2"], [34]),
    (["Dying1", "Dying2"], [16]),
    (["Drunk1", "Drunk2"], [17]),
    (["Insane1", "Insane2"], [18]),
    (["Poison1", "Poison2"], [19]),
    (["Cursed1", "Cursed2"], [20]),
    (["Fall1", "Fall2"], [21]),
    (["CantRestHere1", "CantRestHere2"], [22]),
    (["NeedMoreGold1", "NeedMoreGold2"], [23]),
    (["NeedAKey1", "NeedAKey2"], [24]),
    (["LearnSpell1", "LearnSpell2"], [25]),
    (["CantLearn1", "CantLearn2"], [26]),
    (["CantEquip1", "CantEquip2"], [27]),
    (["Hello1", "Hello2", "Hello3", "Hello4"], [28, 29]),
    (["Hello5", "Hello6"], [30]),
    (["Win!1", "Win!2"], [31]),
    (["Heh1", "Heh2"], [32]),
    (["LastStanding1", "LastStanding2"], [33]),
    (["Enter1", "Enter2"], [35]),
    (["Yes1", "Yes2"], [36]),
    (["Indignant", "Indignant"], [38]),
    (["Thanks1", "Thanks2"], [39]),
    (["n/uShutUp1", "n/uShutUp2"], [40]),
    (["Move!1", "Move!2"], [41]),
]
HELLO_LINES = [28, 29]          # "Pick this voice" is missing from three sets: they say hello instead
CHOOSE_ME = 3


def table_rows(key: str) -> list[list[str]]:
    lines = (TABLES / f"{key}.txt").read_text(encoding="latin-1").splitlines()[1:]
    return [line.split("\t")[:3] for line in lines if line.strip()]


def source_file(folder: Path, name: str) -> Path | None:
    files = {path.name.lower(): path for path in folder.iterdir()}
    for candidate in (name.lower(), name.lower().replace("arrrogant", "arrogant")):
        if candidate in files:
            return files[candidate]
    return None


def collect() -> tuple[dict[int, dict[int, list[tuple[int, Path, str]]]], list[str]]:
    """Per set index, per line: its takes (sound id, source file, installed name)."""
    takes: dict[int, dict[int, list[tuple[int, Path, str]]]] = {}
    missing = []
    for index, (key, folder, name, female, lich) in enumerate(SETS):
        directory = PC / folder
        set_dir = folder.lower().replace(" ", "")
        takes[index] = {}
        for line, row in enumerate(table_rows(key)):
            for take, cell in enumerate(row):
                cell = cell.strip()
                if not cell or cell.lower() == "blank":
                    continue
                path = source_file(directory, cell)
                if path is None:
                    missing.append(f"{folder}/{cell}")
                    continue
                sound_id = FIRST_SOUND + 200 * index + 3 * line + take
                takes[index].setdefault(line, []).append(
                    (sound_id, path, f"voices/pc/{set_dir}/{path.stem.lower()}"))
    return takes, missing


def convert(source: Path, target: Path, check: bool) -> bool:
    if target.is_file() and target.stat().st_mtime >= source.stat().st_mtime:
        return False
    if check:
        raise SystemExit(f"missing or stale MM9 PC voice: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-c:a", "adpcm_ima_wav", "-ar", "22050",
                    "-ac", "1", str(target)], check=True)
    target.chmod(0o644)
    return True


def voice_table(takes) -> str:
    """character_voices.txt with the MM9 sets as columns 79-96. The table's own rows keep their place; the MM9 sets'
    third takes, Name and World rows form a block of their own between the first blank line and the Man row (a rerun
    replaces that block and the columns)."""
    text = VOICES.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = [line.split("\t") for line in text.splitlines()]
    width = FIRST_SET + 1                 # the type column and the old sets 0-78
    rows = [(row + [""] * width)[:width] for row in rows]
    blank = next(number for number, row in enumerate(rows) if number > 0 and not row[0].strip())
    man = next(number for number, row in enumerate(rows) if row[0].strip() == "Man")
    rows = rows[:blank + 1] + rows[man:]
    by_type: dict[str, list[int]] = {}
    for number, row in enumerate(rows[:blank]):
        by_type.setdefault(row[0].strip(), []).append(number)
    values: dict[int, list[str]] = {number: ["0"] * len(SETS) for number in range(blank)}
    block: list[list[str]] = []

    for types, lines in GROUPS:
        slots = []
        used: dict[str, int] = {}
        for name in types:
            occurrence = used.get(name, 0)
            used[name] = occurrence + 1
            slots.append(by_type[name][occurrence])
        group_extra: list[list[str]] = []
        for index in range(len(SETS)):
            line_takes = [t for line in lines for t in takes[index].get(line, [])]
            if not line_takes and lines == [CHOOSE_ME]:
                line_takes = [t for line in HELLO_LINES for t in takes[index].get(line, [])]
            for position, (sound_id, _, _) in enumerate(line_takes):
                if position < len(slots):
                    values[slots[position]][index] = str(sound_id)
                else:
                    while len(group_extra) <= position - len(slots):
                        group_extra.append(["0"] * len(SETS))
                    group_extra[position - len(slots)][index] = str(sound_id)
        block += [[types[-1]] + ["0"] * FIRST_SET + ids for ids in group_extra]
    block.append(["Name"] + [""] * FIRST_SET + [name for _, _, name, _, _ in SETS])
    block.append(["World"] + [""] * FIRST_SET + ["mm9"] * len(SETS))
    block.append([""] * (width + len(SETS)))

    meta = {
        "Man": ["x" if not female and not lich else "-" for _, _, _, female, lich in SETS],
        "Woman": ["x" if female and not lich else "-" for _, _, _, female, lich in SETS],
        "Undead Man": ["x" if not female and lich else "-" for _, _, _, female, lich in SETS],
        "Undead Woman": ["x" if female and lich else "-" for _, _, _, female, lich in SETS],
        "Notes": [f"mm9 {name.lower()} {'female' if female else 'male'}" for _, _, name, female, _ in SETS],
    }
    out = []
    for number, row in enumerate(rows):
        name = row[0].strip()
        if number == 0:
            out.append(row + [str(FIRST_SET + index) for index in range(len(SETS))])
        elif number < blank:
            out.append(row + values[number])
        elif number == blank:
            out.append(row + [""] * len(SETS))
            out += block
        else:
            out.append(row + meta.get(name, [""] * len(SETS)))
    return newline.join("\t".join(row) for row in out) + newline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if anything would change")
    args = parser.parse_args()

    takes, missing = collect()
    converted = 0
    lines = ["/NAME\tID\tTYPE\t3D\tCOMMENTS",
             "/MM9 player-character voices (generate_mm9_pc_voices.py; devdocs/mm9_rework/MM9_PC_VOICES.md)."]
    for index in sorted(takes):
        for line in sorted(takes[index]):
            for sound_id, source, name in takes[index][line]:
                converted += convert(source, AUDIO / f"{name}.wav", args.check)
                lines.append(f"{name}\t{sound_id}\tswap\t0")
    sounds_text = "\n".join(lines) + "\n"
    table_text = voice_table(takes)
    for path, text in ((SOUNDS, sounds_text), (VOICES, table_text)):
        if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
            if args.check:
                raise SystemExit(f"stale: {path}")
            path.write_bytes(text.encode("utf-8"))
    total = sum(len(t) for per in takes.values() for t in per.values())
    print(f"MM9 PC voices: {len(SETS)} sets, {total} takes, converted {converted}; "
          f"{len(missing)} listed files MM9 does not ship: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
