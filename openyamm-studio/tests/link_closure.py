#!/usr/bin/env python3
"""Link closure of game and engine sources, from the objects of the game's own build tree (build/).

An include closure says which headers a source reads; this says which other sources it needs at link time, which is
what decides whether the studio can compile it in place (PLAN.md section 1). For each root source it prints the
sources its symbols pull in and flags the ones that reach SDL, bgfx or bimg.

    openyamm-studio/tests/link_closure.py game/indoor/IndoorMovementController.cpp [more roots ...]
"""
import collections
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OBJECT_DIRS = [ROOT / "build/game/CMakeFiles/openyamm_game.dir", ROOT / "build/engine/CMakeFiles/openyamm_engine.dir",
               ROOT / "build/core/CMakeFiles/openyamm_core.dir", ROOT / "build/core/CMakeFiles/openyamm_core_compile.dir"]
FOREIGN = ("SDL_", "bgfx", "bimg", "ImGui", "av_", "avcodec", "avformat", "sws_", "swr_", "FT_")


def source_of(obj: pathlib.Path) -> str:
    text = str(obj)
    for marker, prefix in ((".dir/__/game/", "game/"), (".dir/__/engine/", "engine/"),
                           ("openyamm_core_compile.dir/compile/", "core/compile/"), ("openyamm_game.dir/", "game/"),
                           ("openyamm_engine.dir/", "engine/")):
        if marker in text:
            return prefix + text.split(marker, 1)[1][:-2]
    return text


def main() -> int:
    defined, undefined = {}, collections.defaultdict(set)
    for directory in OBJECT_DIRS:
        for obj in directory.rglob("*.o"):
            source = source_of(obj)
            out = subprocess.run(["nm", "-C", "--defined-only", str(obj)], capture_output=True, text=True).stdout
            for line in out.splitlines():
                parts = line.split(" ", 2)
                if len(parts) == 3 and parts[1] in "TDBR":
                    defined.setdefault(parts[2], source)
            out = subprocess.run(["nm", "-C", "--undefined-only", str(obj)], capture_output=True, text=True).stdout
            for line in out.splitlines():
                undefined[source].add(line.strip()[2:].strip())
    for root in sys.argv[1:]:
        seen, queue, foreign = {root: None}, [root], collections.defaultdict(set)
        while queue:
            source = queue.pop()
            for symbol in undefined.get(source, ()):
                if symbol.startswith(FOREIGN) or "bgfx::" in symbol or "bimg::" in symbol:
                    foreign[source].add(symbol.split("(")[0])
                owner = defined.get(symbol)
                if owner and owner not in seen:
                    seen[owner] = (source, symbol.split("(")[0])
                    queue.append(owner)
        print(f"{root}: {len(seen)} sources" + ("" if root in undefined else "  (no object found)"))
        for source in sorted(seen):
            if source != root:
                via = seen[source]
                mark = "  FOREIGN " + ", ".join(sorted(foreign[source])[:3]) if foreign.get(source) else ""
                print(f"    {source}  <- {via[0]} ({via[1]}){mark}"[:230])
        if foreign.get(root):
            print("    root itself uses: " + ", ".join(sorted(foreign[root])[:4]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
