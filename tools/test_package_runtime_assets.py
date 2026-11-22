#!/usr/bin/env python3
"""Check that release bundles ship runtime models and leave development model files out."""

import json
from pathlib import Path
import struct
import tempfile
import zipfile

from package_runtime_assets import check_model_references, package, share_model_textures


def check_model_selection():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in ("engine", "mm6"):
            source = root / name
            files = {
                "world.yml": b"id: mm6\n",
                "sprites/grass.png": b"grass",
                "models/actors.yml": b"actors:\n- model: worlds/mm6/models/demon.glb\n",
                "models/projectiles.yml": b"projectiles: []\n",
                "models/demon.glb": b"model",
                "models/textures/0123.oytex": b"cooked texture",
                "models/README.md": b"notes",
                "models/crowd_test.yml": b"actors: []\n",
                "models/fixtures/checker.png": b"fixture texture",
                "world_items/items.yml": b"items: []\n",
                "world_items/models/boots.glb": b"ground item model",
                "world_items/models/textures/boots.oytex": b"ground item texture",
                "effects/mm9/models/spells/bugpath.glb": b"existing particle animation path",
                "source/maps.yml": b"maps: []\n",
                ".build_world.lock": b"",
                "maps/oute3.studio.yml": b"project: oute3\n",
                "models/decoration_data.txt": b"/table rows\n",
            }
            if name == "mm6":
                files["world.yml"] = (b"id: mm6\ntableContributions:\n"
                                      b"  - {table: decorations, mode: append, path: models/decoration_data.txt}\n")
            for relative, content in files.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            output = root / "packages" / f"{name}.zip"
            package(source, output)
            with zipfile.ZipFile(output) as archive:
                # A table the world's manifest names ships from models/ too; leftovers of the authoring tools do not.
                assert set(archive.namelist()) == {
                    "world.yml", "sprites/grass.png", "models/actors.yml", "models/projectiles.yml", "models/demon.glb",
                    "models/textures/0123.oytex", "effects/mm9/models/spells/bugpath.glb",
                    "world_items/items.yml", "world_items/models/boots.glb", "world_items/models/textures/boots.oytex"
                } | ({"models/decoration_data.txt"} if name == "mm6" else set()), archive.namelist()


def glb(uris):
    """A minimal binary glTF whose JSON chunk names these image URIs."""
    document = json.dumps({"asset": {"version": "2.0"}, "images": [{"uri": uri} for uri in uris]}).encode()
    document += b" " * (-len(document) % 4)
    return struct.pack("<III", 0x46546C67, 2, 20 + len(document)) + struct.pack("<II", len(document), 0x4E4F534A) \
        + document


def check_shared_model_textures():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        files = {
            "engine/models/textures/a.oytex": b"shared with the engine",
            "mm6/models/textures/b.oytex": b"shared with mm6",
            "mm9/models/textures/c.oytex": b"shared with mm9 only",
            "xeen/models/body.glb": glb(["textures/a.oytex", "textures/b.oytex", "textures/c.oytex",
                                         "textures/d.oytex"]),
            "xeen/models/textures/a.oytex": b"shared with the engine",
            "xeen/models/textures/b.oytex": b"shared with mm6",
            "xeen/models/textures/c.oytex": b"shared with mm9 only",
            "xeen/models/textures/d.oytex": b"xeen's own",
        }
        packages = {}
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            package_id, name = relative.split("/", 1)
            packages.setdefault(package_id, {})[name] = path
        dependencies = {"mm6": ["engine"], "mm9": ["engine"], "xeen": ["engine", "mm6"]}
        saved = share_model_textures(packages, dependencies)
        # Only what the engine or a dependency ships is left out; MM9 is no dependency of Xeen.
        assert sorted(packages["xeen"]) == ["models/body.glb", "models/textures/c.oytex", "models/textures/d.oytex"]
        assert saved["xeen"] == len(files["xeen/models/textures/a.oytex"]) + len(files["xeen/models/textures/b.oytex"])
        check_model_references(packages, dependencies)
        del packages["xeen"]["models/textures/d.oytex"]
        try:
            check_model_references(packages, dependencies)
        except ValueError as error:
            assert "textures/d.oytex" in str(error), error
        else:
            raise AssertionError("A model texture no package ships was accepted")
        # A different file under the same name stays.
        packages["xeen"]["models/textures/a.oytex"] = b"another texture"
        share_model_textures(packages, dependencies)
        assert "models/textures/a.oytex" in packages["xeen"]


def check_profile_textures():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source, overlay = root / "engine", root / "android/engine"
        runtime_textures = ("models/textures/demon.oytex", "world_items/models/textures/boots.oytex")
        for name in runtime_textures:
            for folder, content in ((source, b"desktop texture"), (overlay, b"android texture")):
                path = folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        output = root / "engine.zip"
        package(source, output, model_textures=overlay)
        with zipfile.ZipFile(output) as archive:
            assert sorted(archive.namelist()) == sorted(runtime_textures), archive.namelist()
            assert all(archive.read(name) == b"android texture" for name in runtime_textures)

        # Every released texture, ground items included, requires a complete, current profile overlay.
        (overlay / runtime_textures[1]).unlink()
        for extra in (False, True):
            if extra:
                (overlay / "models/textures/stale.oytex").write_bytes(b"stale texture")
            try:
                package(source, output, model_textures=overlay)
            except ValueError as error:
                assert "1 missing" in str(error), error
                assert f"{int(extra)} stale" in str(error), error
            else:
                raise AssertionError("An incomplete runtime texture profile was accepted")


if __name__ == "__main__":
    check_model_selection()
    check_profile_textures()
    check_shared_model_textures()
    print("Model selection and profile textures passed for release packages.")
