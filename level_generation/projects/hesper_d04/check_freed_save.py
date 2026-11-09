"""Build the project-local save check against existing engine libraries, then inspect the scenario's real saves."""
import fcntl
import shlex
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
target = ROOT / 'build/tools/CMakeFiles/openyamm_levelgen_inspect_save.dir'
binary = Path('/tmp/hesper_d04_check_freed_save')
with (ROOT / 'output/hesper_stage/locks/engine_build.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    flags = dict(line.split(' = ', 1) for line in (target / 'flags.make').read_text().splitlines() if ' = ' in line)
    link = shlex.split((target / 'link.txt').read_text())
    libraries = link[link.index('-o') + 2:]
    subprocess.run(['c++', '-std=c++20', *shlex.split(flags['CXX_DEFINES']),
                    *shlex.split(flags['CXX_INCLUDES']), str(PROJECT / 'check_freed_save.cpp'),
                    '-o', str(binary), *libraries], cwd=ROOT / 'build/tools', check=True)
saves = Path('/tmp/openyamm_scenario_saves/hesper_d04_main_path')
subprocess.run([str(binary), str(saves / 'd04_freed.oysav'), str(saves / 'd04_freed_reloaded.oysav')], check=True)
