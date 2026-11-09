"""Use the normal development build for private fixtures and native geometry checks."""
from pathlib import Path
import shlex
import subprocess

here = Path(__file__).resolve().parent
repo = here.parents[3]
flags = (repo/'build/game/CMakeFiles/openyamm_game.dir/flags.make').read_text()
includes = next(line.split(' = ', 1)[1] for line in flags.splitlines() if line.startswith('CXX_INCLUDES = '))
link = shlex.split((repo/'build/game/CMakeFiles/openyamm.dir/link.txt').read_text())
libs = link[link.index('libopenyamm_game.a'):]
binary = '/tmp/obsidian-remaining-prepare'
subprocess.run(['c++', '-std=c++20', '-O0', '-DBX_CONFIG_DEBUG=0', *shlex.split(includes),
                str(here/'prepare.cpp'), '-o', binary, *libs, '-pthread'], cwd=repo/'build/game', check=True)
subprocess.run([binary, str(repo)], check=True)

# Compile only this source's Android branch against host SDL for deterministic touch-event checks.
# This does not substitute for the Android SDK/NDK release build.
touch_binary = '/tmp/obsidian-remaining-touch-input'
subprocess.run(['c++', '-std=c++20', '-O0', '-D__ANDROID__', '-DBX_CONFIG_DEBUG=0', *shlex.split(includes),
                str(here/'verify_touch.cpp'), str(repo/'game/app/GameInputSystem.cpp'), '-o', touch_binary,
                *libs, '-pthread'], cwd=repo/'build/game', check=True)
subprocess.run([touch_binary, str(repo)], check=True)
