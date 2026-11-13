#!/usr/bin/env python3
"""Split release packages into content packs (packaging/UPDATER_PLAN.md, part B).

A pack is a deterministic zip holding part of one package (engine or a world) and mounted at its own virtual folder.
Unchanged files produce an unchanged pack, so an update downloads only the packs whose content changed.

- Small, often-changed domains (top-level folders) of a package share one core pack, mounted at the package root.
- Every other domain is split into a committed number of hash buckets, keyed by a group of files that change
  together, and mounted at the domain's folder. A domain may route some files (by extension) into their own
  bucket set, so large rarely-changed files (light bakes) do not ride along with small often-changed ones.
- A pack's identity (content_id) is its logical content, independent of the compressor's output bytes.
- A language pack's text ships in the engine package (languages/<id>/, always installed); its fonts, sounds and videos
  become optional packs with a "language" field, mounted over the game's folders of the same name while that is the
  interface language and downloaded only for a language the player chose (devdocs/LOCALIZATION.md).
"""

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import zipfile

import yaml

PACK_FORMAT = 1
# The fields of a pack in index.json and the release manifest; "language" only on a language's optional packs.
PACK_RECORD_KEYS = ("id", "package", "mount", "file", "size", "content_id", "sha256", "language")
INDEX_SCHEMA = 1
MIB = 1024 * 1024
# Formats that are already compressed: storing them saves load time at no size cost.
STORED_SUFFIXES = (".oyatlas", ".oytex", ".ogv", ".ogg", ".mp3", ".png", ".jpg", ".jpeg")


def fnv1a64(text):
    value = 0xcbf29ce484222325
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * 0x100000001b3) & 0xffffffffffffffff
    return value


def entry_bytes(source):
    return source if isinstance(source, bytes) else Path(source).read_bytes()


def write_zip(entries, output):
    """Write {name: source path or bytes} as a deterministic zip: sorted names, fixed timestamps and permissions."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=output.name + ".", suffix=".tmp", dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
            for name, source in sorted(entries.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                info.compress_type = (zipfile.ZIP_STORED if name.lower().endswith(STORED_SUFFIXES)
                                      else zipfile.ZIP_DEFLATED)
                with archive.open(info, "w", force_zip64=True) as target:
                    if isinstance(source, bytes):
                        target.write(source)
                    else:
                        with Path(source).open("rb") as source_stream:
                            while block := source_stream.read(MIB):
                                target.write(block)
        temporary.chmod(0o644)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(4 * MIB):
            digest.update(block)
    return digest.hexdigest()


def content_id(entries):
    """SHA-256 over the pack format and the sorted (name, size, SHA-256 of bytes) of every entry."""
    digest = hashlib.sha256(f"openyamm-pack {PACK_FORMAT}\n".encode())
    for name, source in sorted(entries.items()):
        data = entry_bytes(source)
        digest.update(f"{name}\0{len(data)}\0{hashlib.sha256(data).hexdigest()}\n".encode())
    return digest.hexdigest()


def glb_image_uris(path):
    """Image URIs of a binary glTF file's JSON chunk."""
    with Path(path).open("rb") as stream:
        header = stream.read(20)
        if len(header) < 20 or header[:4] != b"glTF":
            return []
        chunk_length, chunk_type = struct.unpack_from("<II", header, 12)
        if chunk_type != 0x4E4F534A:
            return []
        document = json.loads(stream.read(chunk_length))
    return [image["uri"] for image in document.get("images", []) if "uri" in image]


def model_groups(entries, domain):
    """Group of each model texture: the first model (by path) whose GLB references it."""
    groups = {}
    for name in sorted(entries):
        if name.startswith(domain + "/") and name.endswith(".glb"):
            source = entries[name]
            if isinstance(source, bytes):
                continue
            model_dir = name[:name.rfind("/") + 1]
            stem = name[len(domain) + 1:-len(".glb")]
            for uri in glb_image_uris(source):
                groups.setdefault(model_dir + uri, stem)
    return groups


def group_key(domain_path, rule, full_name, texture_groups):
    """The key that keeps files changing together in one bucket."""
    directory, _, file_name = domain_path.rpartition("/")
    stem = (directory + "/" if directory else "") + file_name.split(".", 1)[0]
    if rule == "stem":
        return stem
    if rule == "first_dir":
        return domain_path.split("/", 1)[0] if "/" in domain_path else stem
    if rule == "model":
        if full_name.endswith(".glb"):
            return domain_path[:-len(".glb")]
        return texture_groups.get(full_name, stem)
    raise ValueError(f"Unknown pack group rule: {rule}")


def profile_value(value, profile):
    """A bucket count that may differ by profile ({desktop: 9, android: 6})."""
    if isinstance(value, dict):
        if profile not in value:
            raise ValueError(f"No bucket count for profile {profile}: {value}")
        return value[profile]
    return value


class PackConfig:
    def __init__(self, document):
        if document.get("schema") != 1:
            raise ValueError("Unsupported packs.yml schema")
        self.target = document["target_mib"] * MIB
        self.maximum = document["max_mib"] * MIB
        self.core_maximum = document["core_max_mib"] * MIB
        self.worlds = list(document["worlds"])
        self.packages = document["packages"]
        self.language_overlays = document.get("languages", {}).get("overlays", {})

    @classmethod
    def load(cls, path):
        with Path(path).open(encoding="utf-8") as stream:
            return cls(yaml.safe_load(stream))

    def package(self, package_id):
        if package_id == "engine":
            return self.packages[package_id]
        world = self.packages["world"]
        override = self.packages.get(package_id, {})
        return {"core": override.get("core", world.get("core", [])),
                "domains": {**world.get("domains", {}), **override.get("domains", {})}}


def package_mount(package_id):
    if package_id == "engine":
        return "/engine"
    return f"/worlds/{package_id}"


def assign_packs(package_id, entries, config, profile):
    """{pack id: {"mount": virtual folder, "entries": {name inside the pack: source}}} for one package."""
    package_config = config.package(package_id)
    core_domains = set(package_config.get("core", []))
    domains = package_config.get("domains", {})
    mount = package_mount(package_id)
    packs = {}
    texture_groups = {}
    for domain, domain_config in domains.items():
        if domain_config.get("group") == "model":
            texture_groups.update(model_groups(entries, domain))

    def add(pack_id, pack_mount, name, source):
        pack = packs.setdefault(pack_id, {"mount": pack_mount, "entries": {}})
        if pack["mount"] != pack_mount:
            raise ValueError(f"Pack {pack_id} mounts at both {pack['mount']} and {pack_mount}")
        pack["entries"][name] = source

    for name, source in sorted(entries.items()):
        domain, separator, domain_path = name.partition("/")
        if not separator or domain in core_domains:
            add(f"{package_id}.core", mount, name, source)
            continue
        if domain not in domains:
            raise ValueError(f"packs.yml lists {package_id} domain '{domain}' nowhere (file {name})")
        domain_config = domains[domain]
        pack_name, rule_config = domain, domain_config
        for split_name, split in domain_config.get("split", {}).items():
            if name.lower().endswith(tuple(split["extensions"])):
                pack_name, rule_config = f"{domain}.{split_name}", split
                break
        buckets = profile_value(rule_config.get("buckets", 1), profile)
        if buckets < 1:
            raise ValueError(f"Invalid bucket count for {package_id}.{pack_name}")
        rule = rule_config.get("group", domain_config.get("group", "stem"))
        bucket = fnv1a64(group_key(domain_path, rule, name, texture_groups)) % buckets
        pack_id = f"{package_id}.{pack_name}" + (f".{bucket}" if buckets > 1 else "")
        add(pack_id, f"{mount}/{domain}", domain_path, source)
    return packs


# The folders of a language pack that mount over the game's (AssetFileSystem::mountLanguagePack), per package kind.
# icons_x2: images with text in them (the Arcomage card sheet), OY-579.
LANGUAGE_OVERLAYS = {"engine": ("fonts", "audio", "videos", "icons_x2"), "world": ("audio", "videos", "icons_x2")}


def assign_language_packs(language_id, entries, config, profile, worlds):
    """{pack id: {"mount", "package", "entries"}} of a language's optional packs. entries are named as in the language
    folder: engine/fonts/..., worlds/<world>/audio/...; files of worlds the release does not ship, and of overlay folders
    packs.yml marks ship: false, are left out."""
    packs = {}
    for name, source in sorted(entries.items()):
        parts = name.split("/")
        if parts[0] == "engine" and len(parts) > 2 and parts[1] in LANGUAGE_OVERLAYS["engine"]:
            package_id, domain, domain_path = "engine", parts[1], "/".join(parts[2:])
        elif parts[0] == "worlds" and len(parts) > 3 and parts[2] in LANGUAGE_OVERLAYS["world"]:
            package_id, domain, domain_path = parts[1], parts[2], "/".join(parts[3:])
            if package_id not in worlds:
                continue
        else:
            raise ValueError(f"Language {language_id}: {name} is in no folder a language pack overlays")
        if domain not in config.language_overlays:
            raise ValueError(f"packs.yml lists no language overlay '{domain}' (file {name})")
        if not config.language_overlays[domain].get("ship", True):
            continue
        buckets = profile_value(config.language_overlays[domain].get("buckets", 1), profile)
        bucket = fnv1a64(group_key(domain_path, "stem", name, {})) % buckets
        pack_id = f"lang-{language_id}.{package_id}.{domain}" + (f".{bucket}" if buckets > 1 else "")
        pack = packs.setdefault(pack_id, {"mount": f"{package_mount(package_id)}/{domain}", "package": package_id,
                                          "entries": {}})
        pack["entries"][domain_path] = source
    return packs


def pack_file_name(pack_id, identity):
    return f"{pack_id}-{identity[:16]}.zip"


def build_packs(packages, config, profile, output, reuse=None, languages=None):
    """Write the packs of {package id: entries} and of {language id: overlay entries} into output/packs and return
    their index records.

    reuse maps a content_id to an already published pack file; its bytes are copied instead of packing again, so
    every output carries the published bytes of an unchanged pack."""
    reuse = reuse or {}
    store = Path(output) / "packs"
    store.mkdir(parents=True, exist_ok=True)
    records = []
    problems = []
    seen = {}
    layout = []
    for package_id, entries in packages.items():
        for pack_id, pack in sorted(assign_packs(package_id, entries, config, profile).items()):
            layout.append((pack_id, {**pack, "package": package_id}, ""))
    for language_id, entries in (languages or {}).items():
        language_packs = assign_language_packs(language_id, entries, config, profile, set(packages))
        for pack_id, pack in sorted(language_packs.items()):
            layout.append((pack_id, pack, language_id))
    for pack_id, pack, language_id in layout:
        package_id = pack["package"]
        # A language's files replace the game's at the same path, so only files of one language may collide.
        for name in pack["entries"]:
            virtual = (language_id, pack["mount"] + "/" + name)
            if virtual in seen:
                problems.append(f"{virtual[1]} is in both {seen[virtual]} and {pack_id}")
            seen[virtual] = pack_id
        identity = content_id(pack["entries"])
        file_name = pack_file_name(pack_id, identity)
        target = store / file_name
        if identity in reuse:
            data = Path(reuse[identity]).read_bytes()
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(target)
        elif not target.is_file():
            write_zip(pack["entries"], target)
        size = target.stat().st_size
        limit = config.core_maximum if pack_id.endswith(".core") else config.maximum
        if size > limit:
            problems.append(f"{pack_id} is {size / MIB:.1f} MiB, over its {limit // MIB} MiB limit; "
                            f"raise its bucket count in packs.yml")
        record = {"id": pack_id, "package": package_id, "mount": pack["mount"], "file": file_name,
                  "size": size, "content_id": identity, "sha256": file_sha256(target),
                  "entries": len(pack["entries"])}
        if language_id:
            record["language"] = language_id
        records.append(record)
    if problems:
        raise ValueError("Pack layout problems:\n  " + "\n  ".join(problems))
    current = {record["file"] for record in records}
    for stale in store.glob("*.zip"):
        if stale.name not in current:
            stale.unlink()
    return records


def write_index(output, records, *, profile, release, build, content_format):
    index = {
        "schema": INDEX_SCHEMA,
        "release": release,
        "build": build,
        "profile": profile,
        "content_format": content_format,
        "store": "packs",
        "packs": [{key: record[key] for key in PACK_RECORD_KEYS if key in record} for record in records],
    }
    path = Path(output) / "index.json"
    path.write_text(json.dumps(index, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    return path


def report(records, config):
    lines = []
    for record in sorted(records, key=lambda item: item["id"]):
        flag = ""
        if record["id"].endswith(".core"):
            flag = "  over core size" if record["size"] > config.core_maximum else ""
        elif record["size"] > config.target:
            flag = "  over target"
        lines.append(f"{record['id']:<40} {record['size'] / MIB:8.1f} MiB {record['entries']:6} files{flag}")
    total = sum(record["size"] for record in records)
    lines.append(f"{len(records)} packs, {total / MIB:.1f} MiB")
    return "\n".join(lines)
