#!/usr/bin/env python3
"""Check that release bundles retain gameplay assets and exclude development model payloads."""

from pathlib import Path
import tempfile
import zipfile

from package_runtime_assets import package


def check_model_exclusions():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in ("engine", "mm6"):
            source = root / name
            files = {
                "world.yml": b"id: mm6\n",
                "sprites/grass.png": b"grass",
                "models/actors.yml": b"actors:\n- model: worlds/mm6/models/demon.glb\n",
                "models/demon.glb": b"model",
                "models/fixtures/checker.png": b"fixture texture",
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
                    "world.yml", "sprites/grass.png", "effects/mm9/models/spells/bugpath.glb"
                }, archive.namelist()
                assert all(b"worlds/mm6/models/" not in archive.read(path) for path in archive.namelist())


if __name__ == "__main__":
    check_model_exclusions()
    print("Model payload and binding exclusions passed for engine and world packages.")
