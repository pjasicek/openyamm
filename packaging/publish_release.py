#!/usr/bin/env python3
"""Publish a release from CI (.github/workflows/packages.yml; packaging/RELEASE.md, packaging/UPDATER_PLAN.md 7.4).

The server is plain nginx. Its site folder (/var/www/html/openyamm for releases, openyamm-staging for test releases)
holds the published state; this script reads it over HTTPS and writes it with rsync. Commands:

  init-keys   create the manifest signing keys (once, on a trusted machine; the private key becomes a CI secret)
  prepare     build a publish tree from the CI artifacts: content packs that are not published yet, the small
              download packages and app archives, unsigned manifests and the release history
  sign        sign the manifests of a publish tree
  check       install the small Linux package from a local channel of the publish tree, as a player would, and play a
              scenario with the installed game
  upload      upload a signed publish tree in an order that never publishes a reference to a missing file, then remove
              what no recent release references
  verify      fetch the public manifests and check their signatures, HTTP Range and caching
"""

import argparse
import base64
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

REPO = Path(__file__).resolve().parents[1]
CHANNEL = "stable"
# The fields of a pack (tools/runtime_packs.py PACK_RECORD_KEYS); "language" only on a language's optional packs.
PACK_RECORD_KEYS = ("id", "package", "mount", "file", "size", "content_id", "sha256", "language")
MANIFEST_SCHEMA = 1
MIN_UPDATER_SCHEMA = 1
# Every platform's manifest and the content profile its packs come from.
PLATFORMS = {"windows-x64": "desktop", "linux-x64": "desktop", "macos-arm64": "desktop", "android-arm64": "android"}
DESKTOP_PLATFORMS = ("windows-x64", "linux-x64", "macos-arm64")
# Site folders below the server's web root; the staging site serves test releases with the same layout.
SITES = {"stable": "openyamm", "staging": "openyamm-staging"}
# Packs and apps of the newest releases stay on the server (players mid-update, rollbacks); downloads of the newest two.
KEEP_RELEASES = 3
KEEP_DOWNLOADS = 2
MAX_NOTES = 1500
MANIFEST_KEY = "manifest-ed25519.key"
OFFLINE_MANIFEST_KEY = "manifest-ed25519-offline.key"
# The small download packages; a zip keeps nothing of Unix permissions that players' tools honour reliably.
PACKAGE_NAMES = {
    "windows-x64": "OpenYAMM-{version}-windows-x64.zip",
    "linux-x64": "OpenYAMM-{version}-linux-x64.tar.gz",
    "macos-arm64": "OpenYAMM-{version}-macos-arm64.dmg",
    "android-arm64": "OpenYAMM-{version}-android-arm64.apk",
}
# Files of a desktop installation that must be executable (artifact uploads drop permissions); on macOS the game is
# OpenYAMM.app/Contents/MacOS/OpenYAMM.
EXECUTABLE_NAMES = {"OpenYAMM", "openyamm", "OpenYAMM-launcher"}
# Files a desktop stage's version folder (app/<version>/) must have: the game, one of its shaders and, on macOS, the
# bundle's signature, without which macOS refuses to open the downloaded app.
APP_FILES = {
    "windows-x64": ("openyamm.exe", "runtime/shaders/glsl/vs_model.bin"),
    "linux-x64": ("openyamm", "runtime/shaders/glsl/vs_model.bin"),
    "macos-arm64": ("OpenYAMM.app/Contents/MacOS/OpenYAMM",
                    "OpenYAMM.app/Contents/Resources/runtime/shaders/metal/vs_model.bin",
                    "OpenYAMM.app/Contents/_CodeSignature/CodeResources"),
}
# Fixed timestamps make the archives reproducible from the same files.
ARCHIVE_TIME = (1980, 1, 1, 0, 0, 0)


def log(message):
    print(message, flush=True)


def fail(message):
    raise SystemExit(f"error: {message}")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def version_key(version):
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version or "")
    if not match:
        fail(f"invalid release version {version!r}; expected X.Y")
    return int(match.group(1)), int(match.group(2))


def write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def place(source, target):
    """A hard link into the publish tree, or a copy across file systems."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copyfile(source, target)


# Keys

def load_signing_key(path):
    from cryptography.hazmat.primitives import serialization
    path = Path(path)
    if not path.is_file():
        fail(f"no manifest signing key at {path}")
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def public_key_hex(private_key):
    from cryptography.hazmat.primitives import serialization
    return private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def sign_manifest(manifest_bytes, private_key, slot=1):
    signature = private_key.sign(manifest_bytes)
    return (json.dumps({"key": slot, "algorithm": "ed25519", "signature": base64.b64encode(signature).decode()},
                       indent=1) + "\n").encode()


def verify_manifest_signature(manifest_bytes, signature_bytes, public_keys):
    """public_keys: {slot: 32-byte hex}. Returns the slot that verified, or None."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    document = json.loads(signature_bytes)
    key = public_keys.get(document.get("key"))
    if document.get("algorithm") != "ed25519" or key is None:
        return None
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(key)).verify(base64.b64decode(document["signature"]),
                                                                       manifest_bytes)
    except (InvalidSignature, ValueError):
        return None
    return document["key"]


def committed_public_keys():
    keys = {}
    for slot in (1, 2):
        path = REPO / f"packaging/keys/manifest-ed25519-{slot}.pub"
        if path.is_file():
            keys[slot] = path.read_text().strip()
    return keys


def init_keys(args):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    keys = Path(args.keys)
    keys.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(keys, 0o700)
    public_dir = Path(args.public_dir)
    public_dir.mkdir(parents=True, exist_ok=True)
    for slot, name in ((1, MANIFEST_KEY), (2, OFFLINE_MANIFEST_KEY)):
        path = keys / name
        if path.exists():
            log(f"keeping existing {path}")
            private_key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        else:
            private_key = Ed25519PrivateKey.generate()
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                       serialization.NoEncryption()))
            log(f"created {path}")
        (public_dir / f"manifest-ed25519-{slot}.pub").write_text(public_key_hex(private_key) + "\n")
    log(f"""
Public keys written to {public_dir}; commit them. Store {keys / MANIFEST_KEY} as the release environment's
OPENYAMM_MANIFEST_KEY secret, and keep {keys / OFFLINE_MANIFEST_KEY} (the slot-2 rotation key) offline only.""")


# The published state

class Site:
    """A published site, read over HTTPS: <public url>/<site folder>/updates/..."""

    def __init__(self, public_url, site):
        self.name = site
        self.folder = SITES[site]
        self.url = f"{public_url.rstrip('/')}/{self.folder}"
        self.updates_url = f"{self.url}/updates/"

    def fetch_json(self, path):
        """The JSON document at updates/<path>, or None when the server has none."""
        try:
            with urllib.request.urlopen(self.updates_url + path, timeout=60) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def manifests(self):
        return {platform: self.fetch_json(f"channels/{CHANNEL}/{platform}.json") for platform in PLATFORMS}

    def releases(self):
        document = self.fetch_json("history/releases.json")
        return document["releases"] if document else []


def published_release(manifests):
    releases = [manifest["release"] for manifest in manifests.values() if manifest]
    return max(releases, key=version_key) if releases else None


def published_packs(manifests, profile):
    """{(content_id, package, mount): manifest pack record} of the published packs of a content profile."""
    packs = {}
    for platform, manifest in manifests.items():
        if manifest and PLATFORMS[platform] == profile:
            for pack in manifest_packs(manifest):
                packs[(pack["content_id"], pack["package"], pack["mount"], pack.get("language", ""))] = pack
    return packs


def final_index(index, published, release):
    """The release's index: the packer's records, where an unchanged pack (same content id, package and mount) keeps
    its published file, so players never download it again. Returns (index, [(record, fresh pack path)] of new packs,
    [(record, fresh pack path)] of reused packs whose fresh bytes are the published ones)."""
    records, new, identical = [], [], []
    for pack in index["packs"]:
        fresh = Path(index["_root"]) / index["store"] / pack["file"]
        known = published.get((pack["content_id"], pack["package"], pack["mount"], pack.get("language", "")))
        if known:
            record = {key: known[key] for key in ("file", "size", "sha256")}
            record = {"id": pack["id"], "package": pack["package"], "mount": pack["mount"], **record,
                      "content_id": pack["content_id"]}
            if pack.get("language"):
                record["language"] = pack["language"]
            if known["sha256"] == pack["sha256"]:
                identical.append((record, fresh))
        else:
            record = {key: pack[key] for key in PACK_RECORD_KEYS if key in pack}
            new.append((record, fresh))
        records.append(record)
    files = [record["file"] for record in records]
    if len(set(files)) != len(files):
        fail("two packs of the release share a published file name")
    document = {key: index[key] for key in ("schema", "profile", "content_format")}
    document.update({"release": release, "build": release, "store": "../../assets/packs",
                     "packs": [{key: record[key] for key in PACK_RECORD_KEYS if key in record} for record in records]})
    return document, new, identical


def released_updaters_accept(package, mount):
    """Whether the updaters of releases 1.8-1.10 accept a pack's mount. They validate every pack of a manifest before
    its min_updater_schema, so one mount outside /engine or /worlds/<package> stops them updating at all."""
    root = "/engine" if package == "engine" else f"/worlds/{package}"
    return mount == root or mount.startswith(root + "/")


def load_content(directory, release):
    index_path = Path(directory) / "index.json"
    if not index_path.is_file():
        fail(f"missing {index_path}")
    index = json.loads(index_path.read_text())
    if index["release"] != release:
        fail(f"{index_path} was packed for release {index['release']}, not {release}")
    index["_root"] = str(index_path.parent)
    for pack in index["packs"]:
        path = index_path.parent / index["store"] / pack["file"]
        if not path.is_file() or path.stat().st_size != pack["size"]:
            fail(f"{path} is missing or does not match its index record")
        if not released_updaters_accept(pack["package"], pack["mount"]):
            fail(f"{pack['id']} mounts at {pack['mount']}: the updaters of releases 1.8-1.10 accept only /engine and "
                 f"/worlds/<package> mounts, so they could not update to this release")
    return index


# Packages

def stage_files(stage, platform, release):
    """{archive name: (source path, mode)} of a desktop stage folder (its OpenYAMM/ tree), checked against the
    versioned layout."""
    root = Path(stage) / "OpenYAMM"
    if not root.is_dir():
        fail(f"{stage} holds no OpenYAMM folder")
    suffix = ".exe" if platform == "windows-x64" else ""
    app = f"app/{release}"
    required = [f"OpenYAMM{suffix}", "app/current", f"{app}/OpenYAMM-launcher{suffix}",
                *(f"{app}/{name}" for name in APP_FILES[platform])]
    for name in required:
        if not (root / name).is_file():
            fail(f"the {platform} stage lacks OpenYAMM/{name}")
    if (root / "app/current").read_text().strip() != release:
        fail(f"the {platform} stage was built for {(root / 'app/current').read_text().strip()}, not {release}")
    files = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir() or relative.startswith("assets/") or relative == f"{app}/index.json":
            continue
        executable = path.name in EXECUTABLE_NAMES or path.suffix in (".exe", ".dll")
        files["OpenYAMM/" + relative] = (path, 0o755 if executable else 0o644)
    return files


def write_zip(output, files):
    """files: {archive name: (source path or bytes, mode)}, written in name order with fixed timestamps."""
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        for name in sorted(files):
            source, mode = files[name]
            entry = zipfile.ZipInfo(name, ARCHIVE_TIME)
            entry.create_system = 3
            entry.external_attr = (0o100000 | mode) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            data = source if isinstance(source, bytes) else Path(source).read_bytes()
            archive.writestr(entry, data, compresslevel=9)


def write_tar_gz(output, files, directories):
    """A reproducible tar.gz: directories first, then files, with fixed owners, times and modes."""
    import gzip
    with open(output, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as compressed, \
            tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for name in sorted(directories):
            info = tarfile.TarInfo(name)
            info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, 0
            archive.addfile(info)
        for name in sorted(files):
            source, mode = files[name]
            data = source if isinstance(source, bytes) else Path(source).read_bytes()
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), mode, 0
            archive.addfile(info, io.BytesIO(data))


def assemble(platform, stage, index, release, packages_dir, apps_dir):
    """The small download package and the updater's app archive of a desktop platform. Returns (package, app)."""
    files = stage_files(stage, platform, release)
    files[f"OpenYAMM/app/{release}/index.json"] = ((json.dumps(index_document(index), indent=1) + "\n").encode(),
                                                   0o644)
    package = packages_dir / PACKAGE_NAMES[platform].format(version=release)
    package.parent.mkdir(parents=True, exist_ok=True)
    if platform == "macos-arm64":
        # The disk image of the macOS job: OpenYAMM.app as built and signed there. Adding the index would break the
        # bundle's seal, so the app carries none; it installs its release from the update channel into the per-user
        # folder and starts it from there (packaging/UPDATER_PLAN.md 9.4).
        image = Path(stage) / "OpenYAMM.dmg"
        if not image.is_file():
            fail(f"the {platform} stage lacks OpenYAMM.dmg")
        shutil.copyfile(image, package)
    elif package.name.endswith(".tar.gz"):
        directories = {name.rsplit("/", 1)[0] for name in files} | {"OpenYAMM/assets/packs"}
        parents = set()
        for directory in directories:
            parts = directory.split("/")
            parents.update("/".join(parts[:count]) for count in range(1, len(parts) + 1))
        write_tar_gz(package, files, parents)
    else:
        write_zip(package, files)
    # The updater extracts OpenYAMM/app/<release>/ from the app archive, a zip (PhysicsFS) on every platform.
    app = apps_dir / f"app-{platform}-{release}.zip"
    app.parent.mkdir(parents=True, exist_ok=True)
    write_zip(app, files)
    return package, app


def android_sdks():
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(name):
            yield Path(os.environ[name])
    yield Path.home() / "android-sdk"


def android_version_code(apk):
    """The APK's versionCode via aapt. The updater compares it with the installed app, so a manifest without it
    would leave every Android player without updates: no SDK is an error."""
    for sdk in android_sdks():
        for aapt in sorted(sdk.glob("build-tools/*/aapt"), reverse=True):
            output = subprocess.run([str(aapt), "dump", "badging", str(apk)], capture_output=True, text=True)
            match = re.search(r"versionCode='(\d+)'", output.stdout)
            if match:
                return int(match.group(1))
    fail(f"cannot read the versionCode of {apk}: no Android build tools (aapt) found")


def read_notes(path):
    """Short release notes for the update question: plain text, signed with the manifest."""
    if not path:
        return None
    text = Path(path).read_text(encoding="utf-8").strip()
    if len(text) > MAX_NOTES:
        fail(f"{path} has {len(text)} characters; the update question shows at most {MAX_NOTES}")
    return text or None


def file_record(path, folder, name, suffix):
    sha256 = sha256_file(path)
    return {"file": name, "url": f"{folder}/{sha256}{suffix}", "size": path.stat().st_size, "sha256": sha256}


def manifest_packs(manifest):
    """Every pack a manifest or release index lists: its packs and the languages' optional packs."""
    return [*manifest["packs"], *manifest.get("language_packs", [])]


def split_language_packs(records):
    """(packs, language_packs) of a manifest or release index. The languages' optional packs go apart: updaters
    before 2.0 read only packs and know no language field. They would download every language's packs (on Android
    and recorded without their language, so mounted in every language), and they check every pack of a new
    version's index before switching to it, so they would refuse a desktop release missing one."""
    return ([record for record in records if not record.get("language")],
            [record for record in records if record.get("language")])


def index_document(index):
    """A release's index.json as the packages and app archives carry it: the languages' packs apart."""
    packs, language_packs = split_language_packs(index["packs"])
    return {**index, "packs": packs, **({"language_packs": language_packs} if language_packs else {})}


def build_manifest(platform, release, index, app_record, published, notes_url, notes):
    """2.0 and later read both lists of a manifest; desktop fetches a language's packs only for the languages kept
    installed, Android (OpenYammUpdater.java) fetches them all (fonts only)."""
    records = [{"id": pack["id"], "package": pack["package"], "mount": pack["mount"], "file": pack["file"],
                "url": f"packs/{pack['sha256']}.zip", "size": pack["size"], "content_id": pack["content_id"],
                "sha256": pack["sha256"], **({"language": pack["language"]} if pack.get("language") else {})}
               for pack in index["packs"]]
    packs, language_packs = split_language_packs(records)
    return {
        "schema": MANIFEST_SCHEMA,
        "channel": CHANNEL,
        "platform": platform,
        "release": release,
        "build": index["build"],
        "published": published,
        "content_format": index["content_format"],
        "min_updater_schema": MIN_UPDATER_SCHEMA,
        "notes_url": notes_url,
        "notes": notes,
        "app": app_record,
        "packs": packs,
        **({"language_packs": language_packs} if language_packs else {}),
    }


def parse_pairs(values, allowed, what):
    pairs = {}
    for value in values or []:
        key, _, path = value.partition("=")
        if key not in allowed or not path:
            fail(f"--{what} expects one of {', '.join(allowed)}=PATH, not {value!r}")
        pairs[key] = Path(path)
    return pairs


def protected_store_files(site, releases, manifests):
    """Store paths (packs/..., apps/...) that the newest releases and the new manifests reference."""
    referenced = set()
    for manifest in manifests:
        referenced.add(manifest["app"]["url"])
        referenced.update(pack["url"] for pack in manifest_packs(manifest))
    for release in releases[:KEEP_RELEASES]:
        for platform in PLATFORMS:
            manifest = site.fetch_json(f"history/{release}/{platform}.json")
            if manifest:
                referenced.add(manifest["app"]["url"])
                referenced.update(pack["url"] for pack in manifest_packs(manifest))
    return sorted(referenced)


def prepare(args):
    release = args.version
    version_key(release)
    if args.replace and args.site != "staging":
        fail("--replace is for the staging site only")
    contents = parse_pairs(args.content, ("desktop", "android"), "content")
    stages = parse_pairs(args.stage, DESKTOP_PLATFORMS, "stage")
    desktops = [platform for platform in DESKTOP_PLATFORMS if platform not in (args.without or [])]
    missing = [name for name in ("desktop", "android") if name not in contents] \
        + [platform for platform in desktops if platform not in stages] + ([] if args.apk else ["--apk"])
    if missing:
        fail("prepare needs every platform's artifacts; missing: " + ", ".join(missing))

    site = Site(args.public_url, args.site)
    live = site.manifests()
    published = published_release(live)
    if published is not None and version_key(release) <= version_key(published):
        if not (args.replace and release == published):
            fail(f"{release} is not newer than the published release {published} on {site.url}")
    log(f"{site.url}: published {published or 'nothing yet'}; preparing {release}")

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    tree = out / "site"
    updates = tree / "updates"
    downloads = tree / "downloads" / release
    scratch = out / "scratch"
    check_store = out / "check-store"

    indexes = {}
    new_bytes = 0
    for profile, directory in contents.items():
        index, new, identical = final_index(load_content(directory, release), published_packs(live, profile), release)
        indexes[profile] = index
        for record, fresh in new:
            place(fresh, updates / "packs" / f"{record['sha256']}.zip")
            new_bytes += record["size"]
        # The check serves unchanged packs from these local copies instead of the server.
        for record, fresh in identical:
            place(fresh, check_store / "packs" / f"{record['sha256']}.zip")
        log(f"{profile}: {len(index['packs'])} packs, {len(new)} new, {len(index['packs']) - len(new)} published")
    log(f"new content: {new_bytes / 2**20:.1f} MiB")

    published_at = utc_now()
    notes = read_notes(args.notes)
    manifests = {}
    for platform in desktops:
        package, app = assemble(platform, stages[platform], indexes["desktop"], release, downloads, scratch)
        record = file_record(app, "apps", app.name, ".zip")
        place(app, updates / record["url"])
        record["android_version_code"] = None
        manifests[platform] = build_manifest(platform, release, indexes["desktop"], record, published_at,
                                             args.notes_url, notes)
    apk = downloads / PACKAGE_NAMES["android-arm64"].format(version=release)
    place(Path(args.apk), apk)
    record = file_record(apk, "apps", apk.name, ".apk")
    place(apk, updates / record["url"])
    record["android_version_code"] = android_version_code(apk)
    manifests["android-arm64"] = build_manifest("android-arm64", release, indexes["android"], record, published_at,
                                                args.notes_url, notes)

    for package in sorted(downloads.iterdir()):
        (downloads / f"{package.name}.sha256").write_text(f"{sha256_file(package)}  {package.name}\n")
    for platform, manifest in manifests.items():
        write_json(updates / "channels" / CHANNEL / f"{platform}.json", manifest)
        write_json(updates / "history" / release / f"{platform}.json", manifest)
    releases = [release] + [name for name in site.releases() if name != release]
    write_json(updates / "history" / "releases.json", {"releases": releases})
    write_json(out / "plan.json", {
        "release": release,
        "site": args.site,
        "site_url": site.url,
        "platforms": sorted(manifests),
        "published": published_at,
        "previous": published,
        "keep_store": protected_store_files(site, releases, manifests.values()),
        "keep_downloads": releases[:KEEP_DOWNLOADS],
    })
    shutil.rmtree(scratch, ignore_errors=True)
    log(f"publish tree for {release}: {out}")


def sign(args):
    out = Path(args.out)
    key = load_signing_key(args.key)
    if committed_public_keys().get(1) != public_key_hex(key):
        fail("packaging/keys/manifest-ed25519-1.pub does not match the signing key; the game would reject manifests")
    channels = out / "site" / "updates" / "channels" / CHANNEL
    if not (out / "plan.json").is_file():
        fail(f"missing {out / 'plan.json'}; run prepare first")
    platforms = json.loads((out / "plan.json").read_text())["platforms"]
    for platform in platforms:
        path = channels / f"{platform}.json"
        if not path.is_file():
            fail(f"missing {path}; run prepare first")
        (channels / f"{platform}.json.sig").write_bytes(sign_manifest(path.read_bytes(), key))
    log(f"signed {len(platforms)} manifests")


# The install check

def serve(roots, fallback, port):
    """A local channel over HTTP: files from the first root that has them, otherwise a redirect to fallback."""
    command = [sys.executable, str(Path(__file__).with_name("serve_channel.py")), "--port", str(port)]
    if fallback:
        command += ["--fallback", fallback]
    return subprocess.Popen(command + [str(root) for root in roots])


def free_port():
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def check(args):
    out = Path(args.out)
    plan = json.loads((out / "plan.json").read_text())
    release = plan["release"]
    channel = out / "site" / "updates" / "channels" / CHANNEL / "linux-x64.json.sig"
    if not channel.is_file():
        fail("sign the publish tree before checking it")
    package = out / "site" / "downloads" / release / PACKAGE_NAMES["linux-x64"].format(version=release)
    work = Path(tempfile.mkdtemp(prefix="openyamm-install-check-"))
    with tarfile.open(package) as archive:
        archive.extractall(work, filter="tar")
    install = work / "OpenYAMM"
    game = install / "app" / release / "openyamm"
    port = free_port()
    server = serve([out / "site" / "updates", out / "check-store"], plan["site_url"] + "/updates", port)
    try:
        url = f"http://127.0.0.1:{port}/updates/"
        for _ in range(50):
            try:
                urllib.request.urlopen(url + f"channels/{CHANNEL}/linux-x64.json", timeout=2).read()
                break
            except OSError:
                time.sleep(0.2)
        log(f"install check: the small Linux package downloads its content from {url}")
        subprocess.run([str(game), "--headless-update", url], cwd=install, check=True)
        index = json.loads((install / "app" / release / "index.json").read_text())
        if any(pack.get("language") for pack in index["packs"]):
            fail("the release index lists a language's pack among its packs, where updaters before 2.0 require it")
        # A fresh install in English gets every pack but the languages' optional ones, which download only when
        # their language is chosen (devdocs/LOCALIZATION.md).
        for pack in manifest_packs(index):
            path = install / "assets" / "packs" / pack["file"]
            if pack.get("language"):
                if path.exists():
                    fail(f"the install check installed {pack['file']}, a pack of a language nobody chose")
            elif not path.is_file() or path.stat().st_size != pack["size"]:
                fail(f"the install check did not install {pack['file']}")
        for scenario in args.scenario:
            log(f"install check: scenario {scenario}")
            subprocess.run([str(install / "OpenYAMM"), "--headless-run-scenario", str(Path(scenario).resolve())],
                           cwd=work, check=True)
        if args.scenario and not (install / "app" / release / "healthy").is_file():
            fail("the installed game did not mark itself healthy")
        log(f"install check passed: {len(index['packs'])} packs installed into {install}, "
            f"{len(index.get('language_packs', []))} language packs left for their languages")
    finally:
        server.terminate()
        shutil.rmtree(work, ignore_errors=True)


# Upload

def ssh_command(args):
    command = ["ssh", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes"]
    if args.ssh_port:
        command += ["-p", str(args.ssh_port)]
    if args.ssh_key:
        command += ["-i", args.ssh_key]
    if args.known_hosts:
        command += ["-o", f"UserKnownHostsFile={args.known_hosts}"]
    return " ".join(command)


def upload_commands(out, remote, ssh):
    """rsync passes in an order in which no published file references one that is not there yet, then the removal of
    store files and downloads that no recent release references. remote ends with the site folder and a slash."""
    plan = json.loads((Path(out) / "plan.json").read_text())
    tree = Path(out) / "site"
    base = ["rsync", "-rt", "--mkpath", "--chmod=D755,F644", "-e", ssh]
    commands = []
    for folder in ("updates/packs", "updates/apps"):
        if (tree / folder).is_dir():
            commands.append(base + ["--ignore-existing", f"{tree}/{folder}/", f"{remote}{folder}/"])
    commands += [
        base + [f"{tree}/downloads/{plan['release']}/", f"{remote}downloads/{plan['release']}/"],
        # Small files whose size may not change between releases: compared by content, not size and time.
        base + ["--checksum", f"{tree}/updates/history/", f"{remote}updates/history/"],
        base + ["--checksum", f"{tree}/updates/channels/", f"{remote}updates/channels/"],
    ]
    # The removal passes delete only store files and release download folders that no recent release needs;
    # anything else in those folders is protected (rsync filter rules: first match wins, R exposes to --delete).
    keep = {"updates/packs": [], "updates/apps": [], "downloads": []}
    for path in plan["keep_store"]:
        folder, name = path.split("/", 1)
        keep[f"updates/{folder}"].append(f"P /{name}")
    keep["downloads"] = [f"P /{release}/***" for release in plan["keep_downloads"]]
    removable = {"updates/packs": ["R /*.zip"], "updates/apps": ["R /*.zip", "R /*.apk"],
                 "downloads": ["R /[0-9]*.[0-9]*/***"]}
    empty = Path(out) / "empty"
    empty.mkdir(exist_ok=True)
    for folder, rules in keep.items():
        filters = Path(out) / f"keep-{folder.replace('/', '-')}.rsync-filter"
        filters.write_text("\n".join(rules + removable[folder] + ["P *"]) + "\n")
        commands.append(base + ["--delete", f"--filter=merge {filters}", f"{empty}/", f"{remote}{folder}/"])
    return commands


def upload(args):
    out = Path(args.out)
    plan = json.loads((out / "plan.json").read_text())
    channels = out / "site" / "updates" / "channels" / CHANNEL
    for platform in plan["platforms"]:
        if not (channels / f"{platform}.json.sig").is_file():
            fail(f"{platform}.json is not signed")
    # The removal pass must keep everything the new manifests reference; refuse a plan that would not.
    keep = set(plan["keep_store"])
    for platform in plan["platforms"]:
        manifest = json.loads((channels / f"{platform}.json").read_text())
        urls = {manifest["app"]["url"], *(pack["url"] for pack in manifest_packs(manifest))}
        if not urls <= keep:
            fail(f"the removal plan drops files {platform} references")
    if not args.remote.endswith(":"):
        fail(f"--remote names the deploy login as user@host:, not {args.remote!r}")
    remote = f"{args.remote}{SITES[plan['site']]}/"
    for command in upload_commands(out, remote, ssh_command(args)):
        if not args.gc and "--delete" in command:
            continue
        if args.dry_run:
            command = command[:1] + ["--dry-run", "--itemize-changes"] + command[1:]
        log("$ " + " ".join(command))
        subprocess.run(command, check=True)
    log("upload complete" if not args.dry_run else "dry run: nothing uploaded")


# Verification

def fetch(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.status, dict(response.headers), response.read()


def verify(args):
    site = Site(args.public_url, args.site)
    public_keys = committed_public_keys()
    problems = []
    for platform in PLATFORMS:
        base = f"{site.updates_url}channels/{CHANNEL}/{platform}.json"
        try:
            _, headers, manifest = fetch(base)
        except urllib.error.HTTPError as error:
            problems.append(f"{base}: HTTP {error.code}")
            continue
        _, _, signature = fetch(base + ".sig")
        if verify_manifest_signature(manifest, signature, public_keys) is None:
            problems.append(f"{base}: signature does not verify against packaging/keys")
        document = json.loads(manifest)
        if args.expect and document["release"] != args.expect:
            problems.append(f"{base}: release {document['release']}, expected {args.expect}")
        pack = min(document["packs"], key=lambda item: item["size"])
        status, pack_headers, data = fetch(site.updates_url + pack["url"], {"Range": "bytes=0-15"})
        if status != 206 or len(data) != 16:
            problems.append(f"{pack['url']}: HTTP Range is not honoured (status {status})")
        if args.site == "stable" and "immutable" not in pack_headers.get("Cache-Control", ""):
            problems.append(f"{pack['url']}: missing immutable Cache-Control")
        if args.site == "stable" and "max-age" not in headers.get("Cache-Control", ""):
            problems.append(f"{base}: missing short Cache-Control")
        log(f"{platform}: release {document['release']}, {len(document['packs'])} packs")
    if problems:
        fail("verification failed:\n  " + "\n  ".join(problems))
    log("published manifests, signatures, Range and caching verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--public-url", default=os.environ.get("OPENYAMM_PUBLIC_URL", "https://jasicek.net"))
    commands = parser.add_subparsers(dest="command", required=True)

    keys = commands.add_parser("init-keys", help="Create the manifest signing keys (once)")
    keys.add_argument("--keys", default=os.environ.get("OPENYAMM_KEYS_DIR", str(Path.home() / "openyamm-keys")))
    keys.add_argument("--public-dir", default=str(REPO / "packaging/keys"))

    prepare_parser = commands.add_parser("prepare", help="Build a publish tree from the CI artifacts")
    prepare_parser.add_argument("--version", required=True)
    prepare_parser.add_argument("--site", choices=sorted(SITES), required=True)
    prepare_parser.add_argument("--content", action="append", help="PROFILE=DIR of a content job (index.json, packs/)")
    prepare_parser.add_argument("--stage", action="append", help="PLATFORM=DIR of a desktop job (OpenYAMM/)")
    prepare_parser.add_argument("--apk", help="The signed thin APK")
    prepare_parser.add_argument("--notes", help="Text file of short release notes, shown in the update question")
    prepare_parser.add_argument("--notes-url")
    prepare_parser.add_argument("--replace", action="store_true", help="Publish the staged release again (staging)")
    prepare_parser.add_argument("--without", action="append", choices=DESKTOP_PLATFORMS,
                                help="Leave a desktop platform out: rehearsals on a machine that cannot build it")
    prepare_parser.add_argument("--out", required=True)

    sign_parser = commands.add_parser("sign", help="Sign the manifests of a publish tree")
    sign_parser.add_argument("--out", required=True)
    sign_parser.add_argument("--key", required=True, help="PEM file of the slot-1 Ed25519 key")

    check_parser = commands.add_parser("check", help="Install the small Linux package from a local channel")
    check_parser.add_argument("--out", required=True)
    check_parser.add_argument("--scenario", action="append", default=[], help="A scenario the installed game plays")

    upload_parser = commands.add_parser("upload", help="Upload a signed publish tree")
    upload_parser.add_argument("--out", required=True)
    upload_parser.add_argument("--remote", required=True,
                               help="user@host: of the deploy login, whose rrsync root is the web root")
    upload_parser.add_argument("--ssh-key")
    upload_parser.add_argument("--ssh-port", type=int)
    upload_parser.add_argument("--known-hosts")
    upload_parser.add_argument("--no-gc", dest="gc", action="store_false",
                               help="Keep every store file and download on the server")
    upload_parser.add_argument("--dry-run", action="store_true")

    verify_parser = commands.add_parser("verify", help="Check the published release from outside")
    verify_parser.add_argument("--site", choices=sorted(SITES), default="stable")
    verify_parser.add_argument("--expect", help="The release the manifests must name")

    args = parser.parse_args()
    {"init-keys": init_keys, "prepare": prepare, "sign": sign, "check": check, "upload": upload,
     "verify": verify}[args.command](args)


if __name__ == "__main__":
    main()
