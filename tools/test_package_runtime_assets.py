#!/usr/bin/env python3
"""Check that release bundles ship runtime models and leave development model files out."""

from pathlib import Path
import tempfile
import zipfile

from package_runtime_assets import package


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
            }
            for relative, content in files.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            output = root / "packages" / f"{name}.zip"
            package(source, output)
            with zipfile.ZipFile(output) as archive:
                assert set(archive.namelist()) == {
                    "world.yml", "sprites/grass.png", "models/actors.yml", "models/projectiles.yml", "models/demon.glb",
                    "models/textures/0123.oytex", "effects/mm9/models/spells/bugpath.glb",
                    "world_items/items.yml", "world_items/models/boots.glb", "world_items/models/textures/boots.oytex"
                }, archive.namelist()


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
    print("Model selection and profile textures passed for release packages.")
