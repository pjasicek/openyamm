#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


# MM9-SongNN.mp3 is OpenYAMM track 90000 + NN (worlds/mm9/music/900NN.mp3).
MM9_MUSIC_TRACK_BASE = 90000
MM9_MUSIC_PATTERN = re.compile(r"^MM9-Song(\d{2})\.mp3$", re.IGNORECASE)


def track_for_mapstats_music(music_track: int) -> int:
    """The OpenYAMM track of MM9 MAPSTATS's "Music Track" N: MM9 plays MM9-Song(N-1), as the column counts CD tracks
    and the CD's track 1 was data (devdocs/mm9_rework/MM9_AMBIENT_AUDIO_RE.md section 2). 0 for N below 2, which MM9
    plays nothing new for."""
    return MM9_MUSIC_TRACK_BASE + music_track - 1 if music_track >= 2 else 0


@dataclass(frozen=True)
class MusicImport:
    source: Path
    source_track: int
    destination_track: int

    @property
    def destination_name(self) -> str:
        return f"{self.destination_track}.mp3"


def selected_music_imports(source_root: Path) -> list[MusicImport]:
    imports: list[MusicImport] = []
    seen_source_tracks: set[int] = set()

    if not source_root.is_dir():
        return imports

    for source in source_root.iterdir():
        if not source.is_file():
            continue

        match = MM9_MUSIC_PATTERN.fullmatch(source.name)
        if match is None:
            continue

        source_track = int(match.group(1))
        if source_track < 1 or source_track in seen_source_tracks:
            raise ValueError(f"invalid or duplicate MM9 music track {source_track}: {source}")

        seen_source_tracks.add(source_track)
        imports.append(MusicImport(source, source_track, MM9_MUSIC_TRACK_BASE + source_track))

    imports.sort(key=lambda entry: entry.source_track)
    return imports


def import_music(imports: list[MusicImport], output_root: Path, check: bool) -> tuple[int, int]:
    copied = 0
    unchanged = 0

    for entry in imports:
        destination = output_root / entry.destination_name
        source_bytes = entry.source.read_bytes()
        destination_bytes = destination.read_bytes() if destination.is_file() else None
        if destination_bytes == source_bytes:
            unchanged += 1
            continue
        if check:
            raise ValueError(f"missing or stale MM9 music asset: {destination}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(entry.source, destination)
        copied += 1

    return copied, unchanged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import MM9 music with globally unique OpenYAMM track numbers.")
    parser.add_argument("--source-root", type=Path, default=Path("mm9/game/music"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("assets_dev/worlds/mm9/music"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        imports = selected_music_imports(args.source_root)
        if not imports:
            raise ValueError("no MM9 music assets selected")
        copied, unchanged = import_music(imports, args.output_root, args.check)
    except (OSError, ValueError) as exception:
        print(exception)
        return 1

    print(
        f"MM9 world music selected={len(imports)} copied={copied} unchanged={unchanged}"
        f" output={args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
