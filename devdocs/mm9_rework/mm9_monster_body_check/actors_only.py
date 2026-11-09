"""Run a mm9r converter up to its placed actors only (no package write, no compile, no install) and dump them.
usage: python3 actors_only.py <project dir> <scratch dir>; writes <scratch dir>/actors_only.json (nothing installed)."""
import json, runpy, sys
from pathlib import Path
ROOT = Path("/home/pjasicek/github/OpenYAMM")
sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
import dungeon.build as B

def run(self, plan_only=False):
    project = self.project
    project.work.mkdir(parents=True, exist_ok=True)
    self.geometry()
    self.package = B.SourcePackage(self.source, self.hooks.generator)
    self.faces()
    self.movers = B.build_movers(self.source, self.plan, self.package, self.rooms, self.stats,
                                 self.hooks.mover_events, self.glass, self.present)
    self.lights = B.build_lights(self.source, self.polygons, self.package, self.rooms,
                                 set(project.overrides.get("skip_lights") or []))
    from dungeon.content import Content
    self.content = Content(self)
    self.hooks.populate(self)
    self.sector_of_room = {rid: index + 1 for index, rid in enumerate(sorted(self.present))}
    actors = self.hooks.actors(self, self.sector_of_room)
    (project.work / "actors_only.json").write_text(json.dumps(actors, indent=0) + "\n")
    print("ACTORS", len(actors), project.work / "actors_only.json")
    return 0

B.Build.run = run
project_dir, scratch = Path(sys.argv[1]), sys.argv[2]
sys.argv = [str(project_dir / "convert.py"), "--scratch", scratch]
sys.path.insert(0, str(project_dir))
runpy.run_path(str(project_dir / "convert.py"), run_name="__main__")
