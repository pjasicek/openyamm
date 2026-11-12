#!/usr/bin/env python3
"""Check the release publisher without a server: pack reuse, packages, signatures, upload order and cleanup."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("publish_release", HERE / "publish_release.py")
publish_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publish_release)
REAL_SITE = publish_release.Site


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class FakeSite:
    """The published state of a site, as files below a folder instead of HTTPS."""

    def __init__(self, root):
        self.root = Path(root)

    def __call__(self, public_url, site):
        fake = REAL_SITE(public_url, site)
        fake.fetch_json = self.fetch_json
        return fake

    def fetch_json(self, path):
        file = self.root / "updates" / path
        return json.loads(file.read_text()) if file.is_file() else None

    def publish(self, out):
        """What a successful upload leaves on the server, without the cleanup."""
        shutil.copytree(Path(out) / "site", self.root, dirs_exist_ok=True)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="openyamm-publish-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        key = Ed25519PrivateKey.generate()
        self.key = self.root / "manifest.key"
        self.key.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
        self.public_key = publish_release.public_key_hex(key)
        self.server = FakeSite(self.root / "server")
        for patch in (mock.patch.object(publish_release, "committed_public_keys", lambda: {1: self.public_key}),
                      mock.patch.object(publish_release, "android_version_code", lambda apk: 123),
                      mock.patch.object(publish_release, "Site", self.server)):
            patch.start()
            self.addCleanup(patch.stop)

    def artifacts(self, version, packs):
        """The CI artifacts of a release: both content profiles, the desktop stages and the APK."""
        build = self.root / f"artifacts-{version}"
        contents = []
        for profile in ("desktop", "android"):
            records = []
            for pack_id, data in packs.items():
                file_name = f"{pack_id}-{sha256(b'content ' + data)[:16]}.zip"
                path = build / f"content-{profile}" / "packs" / file_name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                record = {"id": pack_id, "package": "engine", "mount": "/engine", "file": file_name,
                          "size": len(data), "content_id": "c" + sha256(data), "sha256": sha256(data)}
                if pack_id.startswith("lang-"):    # a language's optional pack: lang-<id>.engine.<folder>
                    record["language"] = pack_id[len("lang-"):].split(".")[0]
                    record["mount"] = "/engine/" + pack_id.split(".")[2]
                records.append(record)
            (build / f"content-{profile}" / "index.json").write_text(json.dumps(
                {"schema": 1, "release": version, "build": version, "profile": profile, "content_format": 1,
                 "store": "packs", "packs": records}))
            contents.append(f"{profile}={build / f'content-{profile}'}")
        stages = []
        game_files = {
            "windows-x64": {"openyamm.exe": f"game {version}", "runtime/shaders/glsl/vs_model.bin": "shader"},
            "linux-x64": {"openyamm": f"game {version}", "runtime/shaders/glsl/vs_model.bin": "shader"},
            "macos-arm64": {"OpenYAMM.app/Contents/MacOS/OpenYAMM": f"game {version}",
                            "OpenYAMM.app/Contents/Info.plist": "plist",
                            "OpenYAMM.app/Contents/Resources/runtime/shaders/metal/vs_model.bin": "shader",
                            "OpenYAMM.app/Contents/_CodeSignature/CodeResources": "seal"},
        }
        for platform, suffix in (("windows-x64", ".exe"), ("linux-x64", ""), ("macos-arm64", "")):
            root = build / f"stage-{platform}" / "OpenYAMM"
            files = {f"app/{version}/{name}": data for name, data in game_files[platform].items()}
            for name, data in ((f"OpenYAMM{suffix}", "launcher"), ("app/current", f"{version}\n"),
                               (f"app/{version}/OpenYAMM-launcher{suffix}", "launcher"), *files.items(),
                               ("LICENSE", "license")):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(data)
            (root / "assets").mkdir(exist_ok=True)
            if platform == "macos-arm64":
                (root.parent / "OpenYAMM.dmg").write_bytes(b"disk image")
            stages.append(f"{platform}={root.parent}")
        apk = build / "openyamm.apk"
        apk.write_bytes(f"apk {version}".encode())
        return contents, stages, apk

    def prepare(self, version, packs, site="stable", replace=False, without=None):
        contents, stages, apk = self.artifacts(version, packs)
        out = self.root / f"publish-{version}-{site}"
        publish_release.prepare(argparse.Namespace(
            version=version, site=site, content=contents, stage=stages, apk=str(apk), notes=None, notes_url=None,
            replace=replace, without=without, out=str(out), public_url="https://example.invalid"))
        publish_release.sign(argparse.Namespace(out=str(out), key=str(self.key)))
        return out

    def manifest(self, out, platform):
        return json.loads((out / f"site/updates/channels/stable/{platform}.json").read_text())

    def test_prepare_builds_signed_manifests_packages_and_history(self):
        out = self.prepare("0.8", {"engine.core": b"core v1", "engine.icons_x2.0": b"icons"})
        updates = out / "site/updates"
        for platform in publish_release.PLATFORMS:
            data = (updates / f"channels/stable/{platform}.json").read_bytes()
            signature = (updates / f"channels/stable/{platform}.json.sig").read_bytes()
            self.assertEqual(publish_release.verify_manifest_signature(data, signature, {1: self.public_key}), 1)
            manifest = json.loads(data)
            self.assertEqual(manifest["release"], "0.8")
            for item in [manifest["app"], *manifest["packs"]]:
                self.assertEqual(publish_release.sha256_file(updates / item["url"]), item["sha256"])
            self.assertEqual(json.loads((updates / f"history/0.8/{platform}.json").read_text()), manifest)
        self.assertEqual(self.manifest(out, "android-arm64")["app"]["android_version_code"], 123)
        self.assertEqual(json.loads((updates / "history/releases.json").read_text()), {"releases": ["0.8"]})

        # The small packages carry the game and the index, no packs; the app archive is what the updater extracts.
        downloads = out / "site/downloads/0.8"
        with zipfile.ZipFile(downloads / "OpenYAMM-0.8-windows-x64.zip") as package:
            names = package.namelist()
            index = json.loads(package.read("OpenYAMM/app/0.8/index.json"))
        self.assertIn("OpenYAMM/OpenYAMM.exe", names)
        self.assertFalse(any("/assets/" in name for name in names))
        self.assertEqual(index["store"], "../../assets/packs")
        self.assertEqual([pack["file"] for pack in index["packs"]],
                         [pack["file"] for pack in self.manifest(out, "windows-x64")["packs"]])
        with tarfile.open(downloads / "OpenYAMM-0.8-linux-x64.tar.gz") as package:
            members = {member.name: member for member in package.getmembers()}
        self.assertEqual(members["OpenYAMM/OpenYAMM"].mode, 0o755)
        self.assertEqual(members["OpenYAMM/app/0.8/openyamm"].mode, 0o755)
        self.assertEqual(members["OpenYAMM/LICENSE"].mode, 0o644)
        self.assertTrue(members["OpenYAMM/assets/packs"].isdir())
        linux_app = updates / self.manifest(out, "linux-x64")["app"]["url"]
        with zipfile.ZipFile(linux_app) as app:
            self.assertEqual(app.getinfo("OpenYAMM/app/0.8/openyamm").external_attr >> 16, 0o100755)

        # The macOS download is the macOS job's disk image, unchanged; the app archive carries the index.
        self.assertEqual((downloads / "OpenYAMM-0.8-macos-arm64.dmg").read_bytes(), b"disk image")
        macos_app = updates / self.manifest(out, "macos-arm64")["app"]["url"]
        with zipfile.ZipFile(macos_app) as app:
            names = app.namelist()
            self.assertEqual(app.getinfo("OpenYAMM/app/0.8/OpenYAMM.app/Contents/MacOS/OpenYAMM").external_attr >> 16,
                             0o100755)
        self.assertIn("OpenYAMM/app/0.8/index.json", names)
        self.assertIn("OpenYAMM/app/0.8/OpenYAMM-launcher", names)
        for package in ("OpenYAMM-0.8-windows-x64.zip", "OpenYAMM-0.8-linux-x64.tar.gz",
                        "OpenYAMM-0.8-macos-arm64.dmg", "OpenYAMM-0.8-android-arm64.apk"):
            self.assertTrue((downloads / f"{package}.sha256").is_file())

    def test_packages_are_reproducible(self):
        first = self.prepare("0.8", {"engine.core": b"core"})
        second = self.prepare("0.8", {"engine.core": b"core"}, site="staging")
        for name in ("OpenYAMM-0.8-windows-x64.zip", "OpenYAMM-0.8-linux-x64.tar.gz", "OpenYAMM-0.8-macos-arm64.dmg"):
            self.assertEqual((first / "site/downloads/0.8" / name).read_bytes(),
                             (second / "site/downloads/0.8" / name).read_bytes())

    def test_language_packs_are_listed_apart_from_older_updaters(self):
        # Updaters before 2.0 read only "packs" and know no language field, and check every pack of a new version's
        # index before switching to it: manifests and the release index list a language's optional packs under
        # "language_packs", so an update from them downloads none and does not miss them.
        packs = {"engine.core": b"core", "lang-de.engine.audio": b"german voices"}
        out = self.prepare("2.0", packs)
        for platform in ("windows-x64", "android-arm64"):
            manifest = self.manifest(out, platform)
            self.assertEqual([pack["id"] for pack in manifest["packs"]], ["engine.core"])
            self.assertEqual([(pack["id"], pack["language"]) for pack in manifest["language_packs"]],
                             [("lang-de.engine.audio", "de")])
        desktop = self.manifest(out, "windows-x64")
        with zipfile.ZipFile(out / "site/downloads/2.0/OpenYAMM-2.0-windows-x64.zip") as package:
            index = json.loads(package.read("OpenYAMM/app/2.0/index.json"))
        self.assertEqual([pack["id"] for pack in index["packs"]], ["engine.core"])
        self.assertEqual([(pack["id"], pack["language"]) for pack in index["language_packs"]],
                         [("lang-de.engine.audio", "de")])
        # The language pack is uploaded and protected from the store cleanup like any other.
        url = desktop["language_packs"][0]["url"]
        self.assertTrue((out / "site/updates" / url).is_file())
        self.assertIn(url, json.loads((out / "plan.json").read_text())["keep_store"])
        # A later release reuses the published language pack.
        self.server.publish(out)
        again = self.manifest(self.prepare("2.1", {"engine.core": b"core 2", "lang-de.engine.audio": b"german voices"}),
                              "windows-x64")
        self.assertEqual(again["language_packs"][0]["file"], desktop["language_packs"][0]["file"])

    def test_unchanged_packs_keep_their_published_file(self):
        first = self.prepare("0.8", {"engine.core": b"core 8", "engine.icons_x2.0": b"icons"})
        self.server.publish(first)
        second = self.prepare("0.9", {"engine.core": b"core 9", "engine.icons_x2.0": b"icons"})
        published = {pack["id"]: pack for pack in self.manifest(first, "windows-x64")["packs"]}
        packs = {pack["id"]: pack for pack in self.manifest(second, "windows-x64")["packs"]}
        self.assertEqual(packs["engine.icons_x2.0"]["file"], published["engine.icons_x2.0"]["file"])
        self.assertNotEqual(packs["engine.core"]["sha256"], published["engine.core"]["sha256"])
        new_packs = sorted(path.name for path in (second / "site/updates/packs").iterdir())
        self.assertEqual(new_packs, [f"{sha256(b'core 9')}.zip"])
        # The install check serves the unchanged pack from the artifact instead of the server.
        self.assertTrue((second / f"check-store/packs/{sha256(b'icons')}.zip").is_file())
        self.assertEqual(json.loads((second / "site/updates/history/releases.json").read_text()),
                         {"releases": ["0.9", "0.8"]})

    def test_releases_must_be_newer_except_a_replaced_staging_release(self):
        self.server.publish(self.prepare("0.8", {"engine.core": b"core"}))
        with self.assertRaisesRegex(SystemExit, "not newer"):
            self.prepare("0.8", {"engine.core": b"core"})
        with self.assertRaisesRegex(SystemExit, "not newer"):
            self.prepare("0.7", {"engine.core": b"core"})
        with self.assertRaisesRegex(SystemExit, "staging site only"):
            self.prepare("0.8", {"engine.core": b"core"}, replace=True)

    def test_a_rehearsal_may_leave_a_desktop_platform_out(self):
        out = self.prepare("0.8", {"engine.core": b"core"}, without=["macos-arm64"])
        channels = out / "site/updates/channels/stable"
        self.assertEqual(sorted(path.name for path in channels.glob("*.sig")),
                         ["android-arm64.json.sig", "linux-x64.json.sig", "windows-x64.json.sig"])
        self.assertFalse((out / "site/downloads/0.8/OpenYAMM-0.8-macos-arm64.dmg").exists())

    def test_old_updaters_must_accept_every_mount(self):
        self.assertTrue(publish_release.released_updaters_accept("engine", "/engine/rulesets"))
        self.assertTrue(publish_release.released_updaters_accept("mm6", "/worlds/mm6/maps"))
        self.assertFalse(publish_release.released_updaters_accept("rulesets", "/rulesets/maw"))
        self.assertFalse(publish_release.released_updaters_accept("engine", "/engines"))
        content = self.root / "content"
        (content / "packs").mkdir(parents=True)
        (content / "packs" / "rulesets.maw.zip").write_bytes(b"maw")
        (content / "index.json").write_text(json.dumps(
            {"schema": 1, "release": "0.9", "build": "0.9", "profile": "desktop", "content_format": 1,
             "store": "packs", "packs": [{"id": "rulesets.maw", "package": "rulesets", "mount": "/rulesets/maw",
                                          "file": "rulesets.maw.zip", "size": 3, "content_id": "c", "sha256": "s"}]}))
        with self.assertRaisesRegex(SystemExit, "1.8-1.10"):
            publish_release.load_content(content, "0.9")

    def test_signing_needs_the_committed_key(self):
        out = self.prepare("0.8", {"engine.core": b"core"})
        with mock.patch.object(publish_release, "committed_public_keys", lambda: {1: "00" * 32}):
            with self.assertRaisesRegex(SystemExit, "does not match"):
                publish_release.sign(argparse.Namespace(out=str(out), key=str(self.key)))

    def test_upload_publishes_manifests_last_and_removes_only_unreferenced_files(self):
        for version, core in (("0.6", b"core 6"), ("0.7", b"core 7"), ("0.8", b"core 8")):
            out = self.prepare(version, {"engine.core": core, "engine.icons_x2.0": b"icons"})
            self.server.publish(out)
        out = self.prepare("0.9", {"engine.core": b"core 9", "engine.icons_x2.0": b"icons"})
        remote = self.root / "remote"
        shutil.copytree(self.server.root, remote / "openyamm")
        (remote / "openyamm/downloads/notes.html").write_text("a page the publisher does not own")
        (remote / "openyamm/updates/packs/README").write_text("not a store file")
        commands = publish_release.upload_commands(out, f"{remote}/openyamm/", "ssh")
        texts = [" ".join(command) for command in commands]
        channels = next(index for index, text in enumerate(texts) if "updates/channels/" in text)
        for prerequisite in ("updates/packs/", "updates/apps/", "downloads/0.9/", "updates/history/"):
            self.assertLess(next(index for index, text in enumerate(texts) if prerequisite in text), channels)
        self.assertTrue(all(index > channels for index, text in enumerate(texts) if "--delete" in text))

        if shutil.which("rsync") is None:
            self.skipTest("rsync is not installed")
        for command in commands:
            subprocess.run([part for part in command if part not in ("-e", "ssh")], check=True)
        packs = {path.name for path in (remote / "openyamm/updates/packs").iterdir()}
        # The three newest releases keep their packs; 0.6's core goes, as does nothing else.
        self.assertEqual(packs, {f"{sha256(data)}.zip" for data in (b"core 7", b"core 8", b"core 9", b"icons")}
                         | {"README"})
        downloads = {path.name for path in (remote / "openyamm/downloads").iterdir()}
        self.assertEqual(downloads, {"0.9", "0.8", "notes.html"})
        manifest = json.loads((remote / "openyamm/updates/channels/stable/linux-x64.json").read_text())
        self.assertEqual(manifest["release"], "0.9")
        for item in [manifest["app"], *manifest["packs"]]:
            self.assertTrue((remote / "openyamm/updates" / item["url"]).is_file(), item["url"])


if __name__ == "__main__":
    unittest.main()
