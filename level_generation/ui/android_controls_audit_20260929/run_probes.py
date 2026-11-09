"""Compile current Android input paths against host SDL; these are not APK/device checks."""
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
flags = (ROOT / "build/game/CMakeFiles/openyamm_game.dir/flags.make").read_text()
includes = next(line.split(" = ", 1)[1] for line in flags.splitlines() if line.startswith("CXX_INCLUDES = "))
link = shlex.split((ROOT / "build/game/CMakeFiles/openyamm.dir/link.txt").read_text())
libraries = link[link.index("libopenyamm_game.a"):]
sources = {
    "current_touch_controls": ROOT / "level_generation/ui/obsidian_remaining_20260929/native/verify_touch.cpp",
    "gesture_order": HERE / "gesture_probe.cpp",
}
for name, source in sources.items():
    binary = Path("/tmp") / ("openyamm-android-audit-" + name)
    subprocess.run([
        "c++", "-std=c++20", "-O0", "-D__ANDROID__", "-DBX_CONFIG_DEBUG=0", *shlex.split(includes),
        str(source), str(ROOT / "game/app/GameInputSystem.cpp"), "-o", str(binary), *libraries, "-pthread",
    ], cwd=ROOT / "build/game", check=True)
    arguments = [str(ROOT)] if name == "current_touch_controls" else []
    result = subprocess.run([str(binary), *arguments], capture_output=True, text=True, check=True)
    (HERE / (name + ".log")).write_text(result.stdout + result.stderr)
    print(name + ":\n" + result.stdout.strip())
