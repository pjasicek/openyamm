"""
The MM9 dungeon -> native BLV converter shared by the MM9 rework's dungeon projects (generalised from the Anskram
Keep pilot). A map project (`level_generation/projects/mm9r_<map>/`) holds overrides.yml and a small convert.py:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mm9r_common"))
    import dungeon

    class MyMap(dungeon.Hooks):
        mover_events = {...}
        def populate(self, build): ...
        def actors(self, build, sector_of_room): ...
        def map_script(self, build): ...

    if __name__ == "__main__":
        sys.exit(dungeon.main(Path(__file__).resolve().parent, MyMap()))

Modules: source (project settings, DAT, frame, model rules), geometry (rings, merging, clipping, voxels, GLB), rooms
(portals, air, rooms, face assignment, plans), package (source package), movers, lights, content (decorations,
pads, actors, loot), tables (review-root rows, install), lua (map script helpers), scenarios, tour, sheet, audit
(walkability), lighting (bake). The route, decisions and gates: ../DUNGEON_PLAYBOOK.md.
"""

from .build import Build, Hooks, main  # noqa: F401
from .source import ROOT, SCALE, Project, Source  # noqa: F401
