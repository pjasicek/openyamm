"""Build the visual fixture helper against the ordinary development build."""
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
flags = (ROOT / "build/game/CMakeFiles/openyamm_game.dir/flags.make").read_text()
includes = next(line.split(" = ", 1)[1] for line in flags.splitlines() if line.startswith("CXX_INCLUDES = "))
link = shlex.split((ROOT / "build/game/CMakeFiles/openyamm.dir/link.txt").read_text())
libs = link[link.index("libopenyamm_game.a"):]
binary = "/tmp/obsidian-guild-fixture"
subprocess.run(["c++", "-std=c++20", "-O0", "-DBX_CONFIG_DEBUG=0", *shlex.split(includes),
                str(HERE / "prepare_fixture.cpp"), "-o", binary, *libs, "-pthread"],
               cwd=ROOT / "build/game", check=True)
subprocess.run([binary, str(ROOT)], check=True)
