"""Build the small camera-save helper against this checkout's existing game libraries."""
from pathlib import Path
import shlex
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
build = ROOT / 'build/tools'
target = build / 'CMakeFiles/openyamm_levelgen_inspect_save.dir'
flags = {}
for line in (target / 'flags.make').read_text().splitlines():
    if ' = ' in line:
        key, value = line.split(' = ', 1)
        flags[key] = shlex.split(value)
link = shlex.split((target / 'link.txt').read_text())
obj = '/tmp/mm7-terrain-capture-save.o'
output = '/tmp/mm7-terrain-capture-save'
subprocess.run([link[0], *flags['CXX_DEFINES'], *flags['CXX_INCLUDES'], *flags['CXX_FLAGS'],
                '-c', str(P / 'prepare_capture_save.cpp'), '-o', obj], check=True)
link = [obj if token.endswith('levelgen_inspect_save_main.cpp.o') else token for token in link]
link[link.index('-o') + 1] = output
subprocess.run(link, cwd=build, check=True)
print(output)
