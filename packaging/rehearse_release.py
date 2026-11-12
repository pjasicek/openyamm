#!/usr/bin/env python3
"""Rehearse a release on this PC before tagging one (packaging/RELEASE.md, "Rehearsal").

Builds what the workflow builds, from this checkout, publishes it with the real publisher to a local copy of the server
(served on 127.0.0.1 like nginx), installs the small packages as players would and updates them to a second release:

  build VERSION [--reuse V] [--change TEXT]   content packs, Linux and Windows stages, a thin x86_64 APK
  publish VERSION                             prepare, sign (real key), the install check, upload with cleanup
  install VERSION --platform P [--visible]    a fresh installation downloads its content and renders a map
  update FROM TO --platform P [--manual]      that installation updates itself, then plays a scenario
  all FIRST SECOND [--manual]                 every step above for both releases and all platforms
  clean                                       stops the server and emulator and removes the work folder

--site URL (for install and update) takes the packages and updates from a published site instead, for example
https://jasicek.net/openyamm-staging after a staging run.

Platforms: linux (native), windows (Wine), android (the emulator; its x86_64 APK stands in for the arm64 one). Nothing
is uploaded anywhere; the work folder (default build-rehearsal/) holds the builds, the site and the installations.
"""

import argparse
import configparser
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packaging"))
import publish_release  # noqa: E402

PLATFORMS = ("linux", "windows", "android")
PACKAGE = "org.openyamm.android"
MANIFEST_KEY = Path.home() / "openyamm-keys" / "manifest-ed25519.key"
AVD = os.environ.get("OPENYAMM_AVD_NAME", "openyamm_api35")
# A file of the engine's core pack: --change adds it, so exactly one pack differs between the releases.
CHANGE_MARKER = REPO / "assets_dev/engine/branding/rehearsal.txt"


def log(message):
    print(f"\n==> {message}", flush=True)


def fail(message):
    raise SystemExit(f"rehearsal failed: {message}")


def run(command, **options):
    print("$ " + " ".join(str(part) for part in command), flush=True)
    return subprocess.run([str(part) for part in command], check=True, **options)


class Work:
    """The work folder and its state.json: server port and PIDs of what the rehearsal started."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.state_path = self.root / "state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.is_file() else {}
        self.site = None  # a published site (--site) in place of the local one

    def save(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=1) + "\n")

    def artifacts(self, version):
        return self.root / "artifacts" / version

    @property
    def www(self):
        return self.root / "www"

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.state['port']}"

    @property
    def channel_url(self):
        if self.site:
            return f"{self.site}/updates/"
        return f"{self.base_url}/openyamm/updates/"

    def install_dir(self, platform):
        return self.root / "installs" / platform / "OpenYAMM"


# The local site

def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def ensure_server(work):
    if alive(work.state.get("server_pid")):
        return
    work.www.mkdir(parents=True, exist_ok=True)
    work.state.setdefault("port", publish_release.free_port())
    server_log = (work.root / "server.log").open("a")
    process = subprocess.Popen([sys.executable, str(REPO / "packaging/serve_channel.py"), "--port",
                                str(work.state["port"]), str(work.www)],
                               stdout=server_log, stderr=server_log, start_new_session=True)
    work.state["server_pid"] = process.pid
    work.save()
    for _ in range(50):
        try:
            urllib.request.urlopen(work.base_url + "/", timeout=2).read()
            break
        except urllib.error.HTTPError:
            break
        except OSError:
            time.sleep(0.2)
    log(f"local site {work.base_url}/openyamm/ serves {work.www}/openyamm")


def published_package(work, version, platform):
    name = publish_release.PACKAGE_NAMES[platform].format(version=version)
    if work.site:
        path = work.root / "downloads" / version / name
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"{work.site}/downloads/{version}/{name}"
            log(f"downloading {url}")
            with urllib.request.urlopen(url, timeout=60) as response, path.with_suffix(".part").open("wb") as stream:
                shutil.copyfileobj(response, stream)
            path.with_suffix(".part").rename(path)
        return path
    path = work.www / "openyamm" / "downloads" / version / name
    if not path.is_file():
        fail(f"{path} is missing; publish {version} first")
    return path


# Build

def linux_build_dir(work):
    return work.root / "build-linux"


def host_tool(work, name):
    matches = sorted(linux_build_dir(work).rglob(name))
    matches = [path for path in matches if path.is_file() and os.access(path, os.X_OK)]
    if not matches:
        fail(f"no {name} in {linux_build_dir(work)}; build the Linux stage first")
    return matches[0]


def copy_stage(source, target):
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, symlinks=True)


def build_linux(work, version, out, jobs):
    build = linux_build_dir(work)
    run(["cmake", "-S", REPO, "-B", build, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
         "-DOPENYAMM_BUILD_DESKTOP_EXECUTABLE=ON", "-DOPENYAMM_BUILD_TESTS=OFF", "-DOPENYAMM_BUILD_EDITOR=OFF",
         "-DOPENYAMM_BUILD_TOOLS=OFF", "-DOPENYAMM_COOK_ON_BUILD=OFF", "-DOPENYAMM_STATIC_LIBSTDCXX=ON",
         "-DOPENYAMM_RUNTIME_SHADER_PATH=runtime/shaders", "-DOPENYAMM_RELEASE_THIN=ON",
         f"-DOPENYAMM_RELEASE_VERSION={version}"])
    run(["cmake", "--build", build, "--target", "openyamm_release_package", "openyamm_sprite_atlas_cook",
         "openyamm_shaderc", "-j", jobs])
    copy_stage(build / "release" / "Release", out / "stage-linux-x64")


def build_windows(work, version, out, jobs):
    build = work.root / "build-windows"
    run(["cmake", "-S", REPO, "-B", build, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release",
         f"-DCMAKE_TOOLCHAIN_FILE={REPO / 'cmake/toolchains/mingw-w64-x86_64.cmake'}",
         "-DOPENYAMM_BUILD_DESKTOP_EXECUTABLE=ON", "-DOPENYAMM_BUILD_TESTS=OFF", "-DOPENYAMM_BUILD_EDITOR=OFF",
         "-DOPENYAMM_BUILD_TOOLS=OFF", f"-DOPENYAMM_HOST_SHADERC={host_tool(work, 'openyamm_shaderc')}",
         "-DOPENYAMM_RELEASE_THIN=ON", f"-DOPENYAMM_RELEASE_VERSION={version}"])
    run(["cmake", "--build", build, "--target", "openyamm_release_package", "-j", jobs])
    copy_stage(build / "release" / "Release", out / "stage-windows-x64")


def android_version_code(version):
    major, minor = publish_release.version_key(version)
    return major * 100 + minor


def build_android(work, version, out):
    # A throwaway key, the same for both releases: the emulator installs the second over the first.
    env = dict(os.environ, OPENYAMM_ANDROID_CONTENT="download", OPENYAMM_ANDROID_RELEASE_ABIS="x86_64",
               OPENYAMM_ANDROID_VERSION_NAME=version, OPENYAMM_ANDROID_VERSION_CODE=str(android_version_code(version)),
               OPENYAMM_ANDROID_KEYSTORE=str(work.root / "rehearsal.jks"), OPENYAMM_ANDROID_KEY_ALIAS="openyamm",
               OPENYAMM_ANDROID_KEYSTORE_PASSWORD="rehearsal", OPENYAMM_ANDROID_KEY_PASSWORD="rehearsal",
               OPENYAMM_HOST_SHADERC=str(host_tool(work, "openyamm_shaderc")))
    run([REPO / "android/build_release_apk.sh"], env=env, cwd=REPO)
    shutil.copyfile(REPO / "android/app-release.apk", out / "openyamm.apk")


def build_content(work, version, out, reuse, change):
    cooker = host_tool(work, "openyamm_sprite_atlas_cook")
    if change:
        CHANGE_MARKER.write_text(change + "\n")
    try:
        for profile in ("desktop", "android"):
            target = out / f"content-{profile}"
            if target.exists():
                shutil.rmtree(target)
            command = [sys.executable, REPO / "tools/package_runtime_assets.py", "--assets-root", REPO / "assets_dev",
                       "--output", target, "--profile", profile, "--cooker", cooker, "--release", version,
                       "--build", version]
            if profile == "android":
                command += ["--sprites", REPO / "assets_cooked/android/sprites_new"]
            if reuse:
                previous = work.artifacts(reuse) / f"content-{profile}"
                command += ["--reuse-manifest", previous / "index.json", "--reuse-store", previous / "packs"]
            run(command, cwd=REPO)
    finally:
        CHANGE_MARKER.unlink(missing_ok=True)


def build(work, args):
    version = args.version
    publish_release.version_key(version)
    out = work.artifacts(version)
    out.mkdir(parents=True, exist_ok=True)
    parts = set(args.only.split(",")) if args.only else {"linux", "windows", "android", "content"}
    jobs = str(args.jobs)
    # The Linux build also makes the host tools (shader compiler, sprite cooker) of the other steps.
    if "linux" in parts or not (linux_build_dir(work) / "build.ninja").is_file():
        log(f"{version}: Linux stage")
        build_linux(work, version, out, jobs)
    if "windows" in parts:
        log(f"{version}: Windows stage (MinGW)")
        build_windows(work, version, out, jobs)
    if "android" in parts:
        log(f"{version}: thin x86_64 APK")
        build_android(work, version, out)
    if "content" in parts:
        log(f"{version}: content packs" + (f", reusing {args.reuse}" if args.reuse else "")
            + (f", changed: {args.change}" if args.change else ""))
        build_content(work, version, out, args.reuse, args.change)


# Publish

def publish(work, args):
    version = args.version
    out = work.artifacts(version)
    tree = work.root / "publish" / version
    ensure_server(work)
    publisher = [sys.executable, REPO / "packaging/publish_release.py", "--public-url", work.base_url]
    notes = work.root / f"notes-{version}.txt"
    notes.write_text(f"Rehearsal release {version}.\n")
    log(f"{version}: prepare")
    run(publisher + ["prepare", "--version", version, "--site", "stable",
                     "--content", f"desktop={out / 'content-desktop'}", "--content", f"android={out / 'content-android'}",
                     "--stage", f"windows-x64={out / 'stage-windows-x64'}",
                     "--stage", f"linux-x64={out / 'stage-linux-x64'}",
                     # This PC cannot build the macOS app; the workflow's macOS job checks it.
                     "--without", "macos-arm64",
                     "--apk", out / "openyamm.apk", "--notes", notes, "--out", tree])
    log(f"{version}: sign with {MANIFEST_KEY}")
    run(publisher + ["sign", "--out", tree, "--key", args.key])
    log(f"{version}: the workflow's install check")
    run(publisher + ["check", "--out", tree, "--scenario", first_scenario()])
    log(f"{version}: upload to {work.www}/openyamm")
    for command in publish_release.upload_commands(tree, f"{work.www}/openyamm/", "ssh"):
        command = [part for part in command if part not in ("-e", "ssh")]
        run(command)
    manifest = json.loads((work.www / "openyamm/updates/channels/stable/linux-x64.json").read_text())
    if manifest["release"] != version:
        fail(f"the local site names {manifest['release']}, not {version}")
    print(f"published {version}: {len(manifest['packs'])} desktop packs", flush=True)


def first_scenario():
    lines = (REPO / "tests/scenarios/release/scenarios.txt").read_text().splitlines()
    names = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    return REPO / "tests/scenarios" / names[0]


# Desktop installations

class Desktop:
    def __init__(self, work, platform):
        self.work = work
        self.platform = platform
        self.windows = platform == "windows"
        self.install = work.install_dir(platform)
        self.suffix = ".exe" if self.windows else ""
        self.env = dict(os.environ)
        if self.windows:
            self.env.update(WINEPREFIX=str(work.root / "wineprefix"), WINEDEBUG="-all",
                            WINEDLLOVERRIDES="mscoree,mshtml=")

    def path(self, path):
        """A path as the game sees it."""
        if not self.windows:
            return str(path)
        return subprocess.run(["winepath", "-w", str(path)], env=self.env, capture_output=True, text=True,
                              check=True).stdout.strip()

    def wineserver(self, *arguments):
        server = shutil.which("wineserver") or "/usr/lib/x86_64-linux-gnu/wine/wineserver"
        subprocess.run([server, *arguments], env=self.env, check=False, timeout=3600)

    def start(self, executable, *arguments, visible=False):
        env = dict(self.env)
        # Under Wine a minimized OpenGL window reads back black frames, so Windows runs stay visible.
        if not visible and not self.windows:
            env["OPENYAMM_START_MINIMIZED"] = "1"
        command = (["wine"] if self.windows else []) + [str(executable), *arguments]
        print("$ " + " ".join(command), flush=True)
        result = subprocess.run(command, cwd=self.install, env=env, timeout=3600)
        # The launcher exits after starting the game, and an update restarts the game as a new process: wait for
        # every process of this installation.
        if self.windows:
            self.wineserver("-w")
        else:
            while self.running():
                time.sleep(1)
        return result.returncode

    def running(self):
        """Processes started from this installation's executables."""
        found = []
        for entry in Path("/proc").iterdir():
            try:
                if entry.name.isdigit() and Path(os.readlink(entry / "exe")).is_relative_to(self.install):
                    found.append(int(entry.name))
            except OSError:
                continue
        return found

    def launcher(self):
        return self.install / f"OpenYAMM{self.suffix}"

    def game(self, version):
        return self.install / "app" / version / f"openyamm{self.suffix}"

    def current(self):
        return (self.install / "app" / "current").read_text().strip()

    def index_files(self, version):
        """The packs an English installation of the version holds: all but the languages' optional ones (apart under
        language_packs in a release index, among the packs in a rehearsal's own build before 2.0)."""
        index = json.loads((self.install / "app" / version / "index.json").read_text())
        return {pack["file"]: pack["size"] for pack in index["packs"] if not pack.get("language")}

    def packs(self):
        folder = self.install / "assets" / "packs"
        if not folder.is_dir():
            return {}  # the Windows zip lists no empty folders; the first start creates it
        return {path.name: path.stat().st_size for path in folder.iterdir() if path.is_file()}

    def write_settings(self, extra=None):
        """A player's settings.ini: the game's defaults, with the local site as the update channel."""
        config = configparser.ConfigParser()
        config.read_dict({"profile": {"name": "desktop", "version": "5"},
                          "updates": {"url": self.work.channel_url}, **(extra or {})})
        with (self.install / "settings.ini").open("w") as stream:
            config.write(stream)


def check_screenshot(path):
    from PIL import Image, ImageStat
    with Image.open(path) as image:
        stat = ImageStat.Stat(image.convert("L"))
    if stat.mean[0] < 20 or stat.stddev[0] < 10:
        fail(f"{path} looks blank (mean {stat.mean[0]:.1f}, deviation {stat.stddev[0]:.1f})")
    print(f"rendered: {path}", flush=True)


def install_desktop(work, version, platform, visible):
    desktop = Desktop(work, platform)
    package = published_package(work, version, f"{platform}-x64")
    root = desktop.install.parent
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    log(f"{platform}: fresh installation of {package.name}")
    if package.name.endswith(".tar.gz"):
        with tarfile.open(package) as archive:
            archive.extractall(root, filter="tar")
    else:
        with zipfile.ZipFile(package) as archive:
            archive.extractall(root)
    if desktop.windows:
        subprocess.run(["wineboot", "-i"], env=desktop.env, capture_output=True, check=False)
        desktop.wineserver("-w")
    if desktop.packs():
        fail("the small package already holds content packs")

    # The first start: the content setup window downloads everything, then the game renders New Sorpigal and exits.
    shots = work.root / "shots" / f"{platform}-{version}"
    if shots.exists():
        shutil.rmtree(shots)
    tour = work.root / f"tour-{platform}.yml"
    tour.write_text(f"output_dir: {desktop.path(shots)}\nexit: true\nsettle_seconds: 3\nshots:\n"
                    "  - name: new-sorpigal\n    position: [0, 0, 512]\n    yaw: 0.0\n    pitch: -0.1\n")
    desktop.write_settings({"startup": {"start_in_main_menu": "false"}, "video": {"skip_event_cutscenes": "true"},
                            "debug": {"start_world": "mm6", "start_map_file": "oute3.odm", "preseed_party": "true",
                                      "screenshot_tour_path": desktop.path(tour)}})
    started = time.monotonic()
    status = desktop.start(desktop.launcher(), visible=visible)
    if status != 0:
        fail(f"the first start exited with {status}; see {desktop.install / 'openyamm.log'}")
    if desktop.current() != version:
        fail(f"app/current names {desktop.current()}, not {version}")
    if desktop.packs() != desktop.index_files(version):
        fail("the installed packs differ from the release's index")
    shot = next(iter(sorted(shots.glob("*.png"))), None)
    if not shot:
        fail(f"the first start rendered no screenshot; see {desktop.install / 'openyamm.log'}")
    check_screenshot(shot)
    desktop.write_settings()
    print(f"{platform}: {len(desktop.packs())} packs downloaded and a map rendered in "
          f"{time.monotonic() - started:.0f} s; installation {desktop.install}", flush=True)


def update_desktop(work, previous, version, platform, manual):
    desktop = Desktop(work, platform)
    if desktop.current() != previous:
        fail(f"the {platform} installation runs {desktop.current()}, not {previous}")
    before = desktop.packs()
    old_index = desktop.index_files(previous)
    desktop.write_settings()
    if manual:
        log(f"{platform}: update {previous} -> {version} in the game")
        print("The game starts. In the main menu it offers the update: accept it. The game downloads it, restarts as "
              f"{version} and returns to the main menu; then quit the game.", flush=True)
        desktop.start(desktop.launcher(), visible=True)
    else:
        log(f"{platform}: {previous} updates itself to {version} (--headless-update)")
        status = desktop.start(desktop.game(previous), "--headless-update", work.channel_url)
        if status != 0:
            fail(f"--headless-update exited with {status}")
    if desktop.current() != version:
        fail(f"app/current names {desktop.current()} after the update, not {version}")
    new_index = desktop.index_files(version)
    downloaded = set(desktop.packs()) - set(before)
    expected = set(new_index) - set(old_index)
    if not downloaded <= expected or not expected <= set(desktop.packs()):
        fail(f"the update downloaded {sorted(downloaded)}, expected {sorted(expected)}")
    print(f"{platform}: downloaded {len(expected)} changed packs of {len(new_index)}: {sorted(expected)}", flush=True)

    # Through the launcher, as players start it: the new version plays, marks itself healthy and removes the old one.
    log(f"{platform}: {version} plays a scenario through the launcher")
    status = desktop.start(desktop.launcher(), "--headless-run-scenario", desktop.path(first_scenario()))
    if status != 0:
        fail(f"the scenario failed under {version} with {status}")
    if not (desktop.install / "app" / version / "healthy").is_file():
        fail(f"{version} did not mark itself healthy")
    if (desktop.install / "app" / previous).exists():
        fail(f"the healthy start of {version} kept app/{previous}")
    if desktop.packs() != new_index:
        fail(f"the packs after the update differ from {version}'s index: "
             f"{sorted(set(desktop.packs()) ^ set(new_index))}")
    print(f"{platform}: updated {previous} -> {version}; {previous} and its unused packs are gone", flush=True)


# Android

def android_sdk():
    for candidate in (os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
                      str(Path.home() / "android-sdk")):
        if candidate and (Path(candidate) / "platform-tools/adb").is_file():
            return Path(candidate)
    fail("no Android SDK with platform-tools/adb")


class Android:
    def __init__(self, work):
        self.work = work
        self.sdk = android_sdk()
        self.adb_path = self.sdk / "platform-tools/adb"
        self.serial = None
        self.storage = f"/sdcard/Android/data/{PACKAGE}/files"

    def adb(self, *arguments, check=True, capture=True):
        command = [str(self.adb_path)] + (["-s", self.serial] if self.serial else []) + [str(part) for part in arguments]
        result = subprocess.run(command, capture_output=capture, text=True, timeout=300)
        if check and result.returncode:
            fail(f"{' '.join(command)}: {result.stderr}{result.stdout}")
        return result.stdout if capture else ""

    def emulators(self):
        lines = self.adb("devices").splitlines()
        return [line.split()[0] for line in lines if line.startswith("emulator-") and line.endswith("device")]

    def ensure_emulator(self):
        running = self.emulators()
        if running:
            self.serial = running[0]
        else:
            log(f"starting the emulator {AVD}")
            # ANGLE over SwiftShader: the emulator's own GLES renderer crashes on this NVIDIA host when a map loads.
            emulator_log = (self.work.root / "emulator.log").open("a")
            process = subprocess.Popen(
                [str(self.sdk / "emulator/emulator"), "-avd", AVD, "-gpu", "swangle_indirect", "-no-snapshot-save",
                 "-no-boot-anim", "-no-audio"], env=dict(os.environ, QT_QPA_PLATFORM="xcb"),
                stdout=emulator_log, stderr=emulator_log, start_new_session=True)
            self.work.state["emulator_pid"] = process.pid
            self.work.save()
            self.adb("wait-for-device")
            self.serial = self.emulators()[0]
            deadline = time.monotonic() + 300
            while self.adb("shell", "getprop", "sys.boot_completed", check=False).strip() != "1":
                if time.monotonic() > deadline:
                    fail("the emulator did not boot")
                time.sleep(2)
            # A fresh boot keeps applying resource overlays, each of which recreates a running activity.
            time.sleep(60)
        if self.adb("shell", "getprop", "ro.kernel.qemu").strip() != "1":
            fail("Android checks run only on an emulator")
        if not self.work.site:
            port = self.work.state["port"]
            self.adb("reverse", f"tcp:{port}", f"tcp:{port}")

    def version_name(self):
        for line in self.adb("shell", "dumpsys", "package", PACKAGE, check=False).splitlines():
            if "versionName=" in line:
                return line.split("versionName=", 1)[1].strip()
        return None

    def screenshot(self, name):
        path = self.work.root / "shots" / f"android-{name}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.adb("emu", "screenrecord", "screenshot", path.resolve(), check=False)
        return path

    def push_settings(self):
        config = configparser.ConfigParser()
        config.read_dict({"profile": {"name": "android", "version": "5"}, "updates": {"url": self.work.channel_url}})
        settings = self.work.root / "android-settings.ini"
        with settings.open("w") as stream:
            config.write(stream)
        self.adb("push", settings, f"{self.storage}/settings.ini")

    def tap_native_button(self, labels):
        """Taps a native Android button (the update screen's or the package installer's) whose text is in labels."""
        import re
        self.adb("shell", "uiautomator", "dump", "/sdcard/window.xml", check=False)
        dump = self.adb("exec-out", "cat", "/sdcard/window.xml", check=False)
        for node in re.finditer(r'<node [^>]*>', dump):
            text = re.search(r'text="([^"]*)"', node.group(0))
            bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node.group(0))
            if text and bounds and text.group(1).strip().upper() in labels and 'clickable="true"' in node.group(0):
                x1, y1, x2, y2 = map(int, bounds.groups())
                self.adb("shell", "input", "tap", (x1 + x2) // 2, (y1 + y2) // 2)
                return text.group(1)
        return None


def install_android(work, version):
    android = Android(work)
    android.ensure_emulator()
    apk = published_package(work, version, "android-arm64")
    log(f"android: fresh installation of {apk.name}")
    output = work.root / "android" / f"install-{version}"
    run([sys.executable, REPO / "android/test_release_apk.py", apk, "--adb", android.adb_path, "--serial",
         android.serial, "--output", output, "--update-url", work.channel_url, "--world", "mm6", "--map", "oute3.odm",
         "--resume-cycles", "0"])
    if android.version_name() != version:
        fail(f"the emulator runs {android.version_name()}, not {version}")
    android.push_settings()
    print(f"android: {version} downloaded its content and rendered a map; screenshots in {output}", flush=True)


def update_android(work, previous, version):
    android = Android(work)
    android.ensure_emulator()
    if android.version_name() != previous:
        fail(f"the emulator runs {android.version_name()}, not {previous}")
    android.push_settings()
    # A player allows "install unknown apps" for OpenYAMM once, in Settings, on the first in-app update.
    android.adb("shell", "appops", "set", PACKAGE, "REQUEST_INSTALL_PACKAGES", "allow")
    android.adb("logcat", "-c")
    android.adb("shell", "am", "force-stop", PACKAGE)
    android.adb("shell", "am", "start", "-n", f"{PACKAGE}/.OpenYammActivity")
    log(f"android: update {previous} -> {version}")
    print("In the emulator window, answer the game's \"Check for Updates?\" with At start, then choose the update in "
          "the main menu and confirm it. The update screen and the system's install question are confirmed "
          "automatically.", flush=True)
    deadline = time.monotonic() + 1800
    while android.version_name() != version:
        if time.monotonic() > deadline:
            android.screenshot("update-timeout")
            fail(f"the emulator still runs {android.version_name()}")
        tapped = android.tap_native_button({"UPDATE", "INSTALL"})
        if tapped:
            print(f"tapped {tapped}", flush=True)
        time.sleep(3)
    # Replacing the package ends the running app, so Android returns to the home screen; the player starts the game
    # again from its icon, and it promotes the staged content.
    android.adb("logcat", "-c")
    time.sleep(5)
    android.adb("shell", "am", "start", "-n", f"{PACKAGE}/.OpenYammActivity")
    deadline = time.monotonic() + 600
    while "Starting shared OpenYAMM game entry" not in android.adb("logcat", "-d", "-s", "OpenYAMM", check=False):
        if time.monotonic() > deadline:
            android.screenshot("update-no-start")
            fail(f"{version} did not start after the update")
        android.tap_native_button({"PLAY", "OPEN"})
        time.sleep(3)
    time.sleep(20)
    shot = android.screenshot(f"updated-{version}")
    print(f"android: updated {previous} -> {version} and started; screenshot {shot}", flush=True)


# Commands

def install(work, args):
    if not work.site:
        ensure_server(work)
    if args.platform == "android":
        install_android(work, args.version)
    else:
        install_desktop(work, args.version, args.platform, args.visible)


def update(work, args):
    if not work.site:
        ensure_server(work)
    if args.platform == "android":
        update_android(work, args.previous, args.version)
    else:
        update_desktop(work, args.previous, args.version, args.platform, args.manual)


def everything(work, args):
    first, second = args.first, args.second
    platforms = args.platforms.split(",")
    build(work, argparse.Namespace(version=first, reuse=None, change=None, only=None, jobs=args.jobs))
    publish(work, argparse.Namespace(version=first, key=args.key))
    for platform in platforms:
        install(work, argparse.Namespace(version=first, platform=platform, visible=args.visible))
    build(work, argparse.Namespace(version=second, reuse=first, change=f"Rehearsal {second}", only=None,
                                   jobs=args.jobs))
    publish(work, argparse.Namespace(version=second, key=args.key))
    for platform in platforms:
        update(work, argparse.Namespace(previous=first, version=second, platform=platform, manual=args.manual))
    log(f"rehearsal passed: {first} installs and updates to {second} on {', '.join(platforms)}")


def clean(work, args):
    if alive(work.state.get("server_pid")):
        os.killpg(work.state["server_pid"], signal.SIGTERM)
    try:
        android = Android(work)
        if android.emulators():
            android.serial = android.emulators()[0]
            android.adb("reverse", "--remove-all", check=False)
            android.adb("uninstall", PACKAGE, check=False)
            if alive(work.state.get("emulator_pid")):
                android.adb("emu", "kill", check=False)
                # It writes to its temporary folder in the work folder until it exits.
                deadline = time.monotonic() + 60
                while alive(work.state["emulator_pid"]) and time.monotonic() < deadline:
                    time.sleep(1)
    except SystemExit:
        pass
    if (work.root / "wineprefix").is_dir():
        Desktop(work, "windows").wineserver("-k")
    CHANGE_MARKER.unlink(missing_ok=True)
    (REPO / "android/app-release.apk").unlink(missing_ok=True)
    shutil.rmtree(work.root, ignore_errors=True)
    print(f"removed {work.root}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", default=str(REPO / "build-rehearsal"))
    parser.add_argument("--site", help="Install and update from this published site, e.g. "
                        "https://jasicek.net/openyamm-staging, instead of the local one")
    commands = parser.add_subparsers(dest="command", required=True)

    build_parser = commands.add_parser("build")
    build_parser.add_argument("version")
    build_parser.add_argument("--reuse", help="Pack the content reusing this built release's unchanged packs")
    build_parser.add_argument("--change", help="Ship this text as a new file of the engine's core pack")
    build_parser.add_argument("--only", help="Comma-separated parts: linux, windows, android, content")
    build_parser.add_argument("--jobs", type=int, default=os.cpu_count())

    publish_parser = commands.add_parser("publish")
    publish_parser.add_argument("version")
    publish_parser.add_argument("--key", default=str(MANIFEST_KEY))

    install_parser = commands.add_parser("install")
    install_parser.add_argument("version")
    install_parser.add_argument("--platform", choices=PLATFORMS, required=True)
    install_parser.add_argument("--visible", action="store_true", help="Show the game window instead of minimizing it")

    update_parser = commands.add_parser("update")
    update_parser.add_argument("previous")
    update_parser.add_argument("version")
    update_parser.add_argument("--platform", choices=PLATFORMS, required=True)
    update_parser.add_argument("--manual", action="store_true", help="Accept the update in the game's main menu")

    all_parser = commands.add_parser("all")
    all_parser.add_argument("first")
    all_parser.add_argument("second")
    all_parser.add_argument("--platforms", default=",".join(PLATFORMS))
    all_parser.add_argument("--manual", action="store_true")
    all_parser.add_argument("--visible", action="store_true")
    all_parser.add_argument("--key", default=str(MANIFEST_KEY))
    all_parser.add_argument("--jobs", type=int, default=os.cpu_count())

    commands.add_parser("clean")

    args = parser.parse_args()
    work = Work(args.work)
    work.site = args.site.rstrip("/") if args.site else None
    # Compilers, the packer and the publisher write gigabytes of temporary files: keep them in the work folder on disk,
    # not in /tmp, which is often a size-limited RAM disk.
    if args.command != "clean":
        (work.root / "tmp").mkdir(parents=True, exist_ok=True)
        os.environ["TMPDIR"] = str(work.root / "tmp")
    {"build": build, "publish": publish, "install": install, "update": update, "all": everything,
     "clean": clean}[args.command](work, args)


if __name__ == "__main__":
    main()
