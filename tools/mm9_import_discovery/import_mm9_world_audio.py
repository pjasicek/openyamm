#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


# Every MM9 sound (SOUNDS/): ambience, monsters, doors, events, items, weapons, the scripts' magic and spell sounds,
# the player's (footsteps, winces, splashes), gibs and the battle music. A world must not miss a sound one of its scripts,
# effects or placements names. Files at the root of SOUNDS/ whose name the engine's audio root already has are left to
# the engine's.
SHARED_SOUND_PATHS = {"events/quest.wav"}
# Names MM9's scripts play that MM9 never shipped (silent in MM9 too), given the nearest MM9 recording under the name the
# script uses (2026-11-08; the user's choice): script name -> SOUNDS/ file. vo/irequireassistance.wav (Drangheim Prison's
# guard calling for help) has none: no MM9 recording says it.
SCRIPT_SOUND_STAND_INS = {
    "animsounds/dragonredrattack3.wav": "ANIMSOUNDS/DRAGON/RATTACK3.wav",  # KingKong.scr (Thjorad Mine's cages)
    "events/rockfall.wav": "EVENTS/RUBBLECRASH.wav",                      # Tasar Academy's crack, Verhoffin's busts
    "events/doorbreak.wav": "EVENTS/SHATTERWOOD02.wav",                   # Verhoffin Ruins' bolt
    "ambient/fountain_20.wav": "AMBIENT/WATER/FOUNTAIN.wav",              # Verhoffin Ruins' fountain
    "weapons/swordhit01.wav": "WEAPONS/FLESHHIT01.wav",                   # Dark Passageway's ambush
}


@dataclass(frozen=True)
class AudioImport:
    source: Path
    destination_relative: Path


def lowercase_relative(path: Path) -> Path:
    return Path(*(part.lower() for part in path.parts))


def selected_audio_imports(
    sounds_root: Path,
    voices_root: Path,
    engine_audio_root: Path | None = None,
) -> list[AudioImport]:
    imports: list[AudioImport] = []
    engine_audio_entries = (
        engine_audio_root.iterdir()
        if engine_audio_root is not None and engine_audio_root.is_dir()
        else [])
    engine_root_names = {path.name.lower() for path in engine_audio_entries if path.is_file()}

    if sounds_root.is_dir():
        for source in sounds_root.rglob("*.wav"):
            relative = source.relative_to(sounds_root)
            normalized_relative = lowercase_relative(relative)
            if normalized_relative.as_posix() in SHARED_SOUND_PATHS:
                continue
            if len(relative.parts) == 1 and relative.name.lower() in engine_root_names:
                continue
            imports.append(AudioImport(source, normalized_relative))

    for name, source in SCRIPT_SOUND_STAND_INS.items():
        if (sounds_root / source).is_file():
            imports.append(AudioImport(sounds_root / source, Path(name)))

    # The NPCs' greetings, and the cutscenes' voices (VOICES/CINEMA: the council, Sven's speech, the first-sight
    # scenes; devdocs/mm9_rework/MM9_CUTSCENES.md), at MM9's own relative paths.
    for folder in ("NPC", "CINEMA"):
        voice_root = voices_root / folder
        if voice_root.is_dir():
            for source in voice_root.rglob("*"):
                if source.is_file() and source.suffix.lower() == ".wav":
                    relative = Path("voices") / folder.lower() / source.relative_to(voice_root)
                    imports.append(AudioImport(source, lowercase_relative(relative)))

    imports.sort(key=lambda entry: entry.destination_relative.as_posix())
    destinations: dict[Path, Path] = {}
    for entry in imports:
        previous = destinations.get(entry.destination_relative)
        if previous is not None and previous != entry.source:
            raise ValueError(
                f"MM9 audio paths collide after normalization: {previous} and {entry.source}"
                f" -> {entry.destination_relative}")
        destinations[entry.destination_relative] = entry.source
    return imports


def import_audio(imports: list[AudioImport], output_root: Path, check: bool) -> tuple[int, int]:
    copied = 0
    unchanged = 0

    for entry in imports:
        destination = output_root / entry.destination_relative
        source_bytes = entry.source.read_bytes()
        destination_bytes = destination.read_bytes() if destination.is_file() else None
        if destination_bytes == source_bytes:
            unchanged += 1
            continue
        if check:
            raise ValueError(f"missing or stale MM9 audio asset: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(entry.source, destination)
        copied += 1

    return copied, unchanged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import every MM9 sound and the NPC and cutscene voices into the MM9 world package.")
    parser.add_argument(
        "--sounds-root",
        type=Path,
        default=Path("mm9/extracted/SOUNDS/SOUNDS"))
    parser.add_argument(
        "--voices-root",
        type=Path,
        default=Path("mm9/extracted/VOICES/VOICES"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("assets_dev/worlds/mm9/audio"))
    parser.add_argument(
        "--engine-audio-root",
        type=Path,
        default=Path("assets_dev/engine/audio"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        imports = selected_audio_imports(args.sounds_root, args.voices_root, args.engine_audio_root)
        if not imports:
            raise ValueError("no MM9 world audio assets selected")
        copied, unchanged = import_audio(imports, args.output_root, args.check)
    except (OSError, ValueError) as exception:
        print(exception)
        return 1

    print(
        f"MM9 world audio selected={len(imports)} copied={copied} unchanged={unchanged}"
        f" output={args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
