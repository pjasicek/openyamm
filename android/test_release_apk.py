#!/usr/bin/env python3
"""Load a rendered map in a disposable emulator using a signed release APK.

The selected emulator is test-owned: this replaces its game settings. Optional
--baseline-apk and --save exercise an in-place update without uninstalling.
"""

import argparse
import configparser
import hashlib
import io
from pathlib import Path
import subprocess
import time
import zipfile

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline-apk", type=Path)
    parser.add_argument("--save", type=Path)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--map", default="out13.odm")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--resume-cycles", type=int, default=3,
                        help="Test Home, task switching and screen off/on without restarting the game")
    args = parser.parse_args()
    if args.resume_cycles < 0:
        parser.error("--resume-cycles must be nonnegative")
    args.output.mkdir(parents=True, exist_ok=True)
    package = "org.openyamm.android"
    storage = "/sdcard/Android/data/" + package + "/files"

    def adb(*command, check=True):
        result = subprocess.run(
            [args.adb, "-s", args.serial, *command], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=240, check=False,
        )
        if check and result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace") + result.stdout.decode(errors="replace"))
        return result.stdout

    if adb("shell", "getprop", "ro.kernel.qemu").strip() != b"1":
        raise RuntimeError("This test requires a disposable Android emulator, not a physical device.")
    adb("shell", "settings", "put", "secure", "immersive_mode_confirmations", "confirmed")

    def launch():
        adb("shell", "am", "start", "-n", package + "/.OpenYammActivity")

    def capture_rendered_screen(name):
        screenshot = adb("exec-out", "screencap", "-p")
        (args.output / (name + ".png")).write_bytes(screenshot)
        with Image.open(io.BytesIO(screenshot)) as image:
            width, height = image.size
            # Exclude Android status/navigation bars and game letterboxing.
            center = image.crop((width // 4, height // 4, 3 * width // 4, 3 * height // 4)).convert("L")
            histogram = center.histogram()
        return sum(histogram[24:]) > sum(histogram) * 0.10

    with zipfile.ZipFile(args.apk) as apk:
        config = configparser.ConfigParser()
        config.read_string(apk.read("assets/settings.ini").decode())
        shaders = {
            name[len("assets/"):]: apk.read(name) for name in apk.namelist()
            if name.startswith("assets/runtime/shaders/essl/") and name.endswith(".bin")
        }
    if not shaders:
        raise RuntimeError("APK contains no Android shaders.")

    if args.baseline_apk:
        print("Installing baseline APK", flush=True)
        adb("install", "-r", str(args.baseline_apk.resolve()))
        launch()
        time.sleep(10)
        adb("shell", "am", "force-stop", package)

    # No uninstall, clear-data, save conversion or manual shader installation.
    if args.baseline_apk:
        adb("shell", "mkdir", "-p", storage + "/saves", storage + "/logs")
        if args.save:
            adb("push", str(args.save.resolve()), storage + "/saves/upgrade-test.oysav")

    config["startup"]["start_in_main_menu"] = "false"
    config["startup"]["save_file"] = "saves/upgrade-test.oysav" if args.save else ""
    config["debug"]["start_world"] = args.world
    config["debug"]["start_map_file"] = args.map
    config["debug"]["preseed_party"] = "true"
    config["debug"]["immortal"] = "true"
    config["logging"]["gameplay_trace"] = "true"
    config["logging"]["gameplay_trace_file"] = "logs/android-release-test.log"
    config["logging"]["gameplay_trace_append"] = "false"
    # Exercise the new decoration shaders as well as terrain and creature shaders.
    config["video"]["terrain_decorations"] = "true"
    config["video"]["skip_event_cutscenes"] = "true"
    settings = args.output / "settings.ini"
    with settings.open("w") as stream:
        config.write(stream)

    # On updates, settings and saves must survive the package replacement.
    if args.baseline_apk:
        adb("push", str(settings.resolve()), storage + "/settings.ini")
    print("Installing candidate APK with adb install -r", flush=True)
    adb("install", "-r", str(args.apk.resolve()))
    if not args.baseline_apk:
        adb("shell", "mkdir", "-p", storage + "/saves", storage + "/logs")
        adb("push", str(settings.resolve()), storage + "/settings.ini")
        if args.save:
            adb("push", str(args.save.resolve()), storage + "/saves/upgrade-test.oysav")
    if adb("exec-out", "cat", storage + "/settings.ini") != settings.read_bytes():
        raise RuntimeError("Update changed the existing settings file.")
    if args.save:
        actual = adb("exec-out", "cat", storage + "/saves/upgrade-test.oysav")
        if hashlib.sha256(actual).digest() != hashlib.sha256(args.save.read_bytes()).digest():
            raise RuntimeError("Update changed the existing save.")

    adb("logcat", "-c")
    adb("shell", "rm", "-f", storage + "/logs/android-release-test.log")
    launch()
    marker = ('load_game_applied ' if args.save else 'map_loaded ') + 'map="' + args.map + '"'
    ready_since = None
    deadline = time.monotonic() + args.timeout
    try:
        while time.monotonic() < deadline:
            time.sleep(2)
            # Settings initialization can reopen the trace file during a new game;
            # logcat retains the completed renderer initialization marker.
            text = adb("logcat", "-d", "-v", "brief", "-s", "OpenYAMM").decode(errors="replace")
            lines = text.splitlines()
            loaded = any(
                ("load_game_applied " if args.save else "map_loaded ") in line
                and ('map="' + args.map + '"') in line
                and (args.save or "initialize_view=true" in line) for line in lines
            )
            pid = adb("shell", "pidof", package, check=False).strip()
            if loaded and pid:
                ready_since = ready_since or time.monotonic()
                if time.monotonic() - ready_since >= 5:
                    break
            elif ready_since:
                raise RuntimeError("Game exited after initializing the map.")
        else:
            raise RuntimeError("Timed out waiting for rendered map readiness: " + marker)

        if not capture_rendered_screen("before-resume"):
            raise RuntimeError("Map initialized, but the initial screen is black.")
        original_pid = adb("shell", "pidof", package).strip()
        for cycle in range(args.resume_cycles):
            transition = ("home", "task-switch", "screen-off")[cycle % 3]
            print("Testing resume " + str(cycle + 1) + ": " + transition, flush=True)
            lifecycle_log = adb("logcat", "-d", "-v", "brief", "-s", "SDL")
            destroyed_count = lifecycle_log.count(b"surfaceDestroyed()")
            created_count = lifecycle_log.count(b"surfaceCreated()")
            if transition == "home":
                adb("shell", "input", "keyevent", "KEYCODE_HOME")
            elif transition == "task-switch":
                adb("shell", "am", "start", "-a", "android.settings.SETTINGS")
            else:
                adb("shell", "input", "keyevent", "KEYCODE_SLEEP")

            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                time.sleep(1)
                lifecycle_log = adb("logcat", "-d", "-v", "brief", "-s", "SDL")
                if lifecycle_log.count(b"surfaceDestroyed()") > destroyed_count:
                    break
            else:
                raise RuntimeError("Background transition did not destroy the Android surface.")

            if transition == "screen-off":
                adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
                adb("shell", "wm", "dismiss-keyguard")
            launch()
            # Let Android's cached task snapshot disappear before judging game pixels.
            time.sleep(3)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                time.sleep(1)
                if adb("shell", "pidof", package, check=False).strip() != original_pid:
                    raise RuntimeError("Game exited or restarted during " + transition + ".")
                window_state = adb("shell", "dumpsys", "window").decode(errors="replace")
                focused = any("mCurrentFocus=" in line and package in line for line in window_state.splitlines())
                lifecycle_log = adb("logcat", "-d", "-v", "brief", "-s", "SDL")
                recreated = lifecycle_log.count(b"surfaceCreated()") > created_count
                if focused and recreated and capture_rendered_screen("resume-" + str(cycle + 1) + "-" + transition):
                    break
            else:
                raise RuntimeError("Rendering did not recover after " + transition + ".")

        print("PASS: " + str(args.resume_cycles) + " surface recreation/resume cycles without restart", flush=True)
        for path, expected in shaders.items():
            if adb("exec-out", "cat", storage + "/" + path) != expected:
                raise RuntimeError("Extracted shader differs from installed APK: " + path)
        print("PASS: rendered " + args.map + "; all " + str(len(shaders)) + " shaders match APK", flush=True)
    finally:
        (args.output / "logcat.txt").write_bytes(adb("logcat", "-d", "-v", "threadtime"))
        (args.output / "gameplay.log").write_bytes(
            adb("exec-out", "cat", storage + "/logs/android-release-test.log", check=False))
        (args.output / "screen.png").write_bytes(adb("exec-out", "screencap", "-p", check=False))
        adb("shell", "am", "force-stop", package)


if __name__ == "__main__":
    main()
