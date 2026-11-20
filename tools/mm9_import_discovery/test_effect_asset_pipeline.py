#!/usr/bin/env python3
"""Focused deterministic/pixel/resource checks for the migrated MM9 effect assets."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile

from PIL import Image
import yaml

from convert_abc_model import decode_dtx_mips
from convert_effect_dtx import convert_effect_texture
from import_mm9_effect_assets import import_texture, load_restorations


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))
EXPECTED_FIXTURE_HASHES = {
    "shared_model_fixture.glb": "29110d31dd4fb435127190133bd265a770661a0aae3e912f8430c0fefad6e2fb",
    "checker.png": "b29dfd6008ebc2007576e1e4e88defd22e5205f6ffd9d5c1c8948aba02da0823",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_model_fixture() -> None:
    import generate_model_fixtures

    glb, png = generate_model_fixtures.build_fixture()
    actual = {
        "shared_model_fixture.glb": hashlib.sha256(glb).hexdigest(),
        "checker.png": hashlib.sha256(png).hexdigest(),
    }
    assert actual == EXPECTED_FIXTURE_HASHES, actual
    for name, expected in EXPECTED_FIXTURE_HASHES.items():
        checked_in = REPOSITORY_ROOT / "assets_dev/engine/models/fixtures" / name
        assert sha256(checked_in) == expected, checked_in


def check_texture_conversion() -> None:
    source = REPOSITORY_ROOT / "mm9/extracted/SPRITETEXTURES/SPRITETEXTURES/BLACKWHITERING.dtx"
    source_images, source_metadata = decode_dtx_mips(source, repair_opaque_alpha=False)
    with tempfile.TemporaryDirectory(prefix="openyamm-effect-import-") as temporary_directory:
        temporary = Path(temporary_directory)
        outputs = []
        for run in ("first", "second"):
            output = temporary / run / "blackwhitering.png"
            import_directory = temporary / run / "import"
            convert_effect_texture(
                source,
                output,
                import_directory,
                color_space="srgb",
                alpha_usage="blend",
                min_filter="linear",
                mag_filter="linear",
                wrap_u="clamp",
                wrap_v="clamp",
                runtime_texture_path="engine/effects/mm9/textures/blackwhitering.png",
            )
            outputs.append((output, import_directory))

        assert outputs[0][0].read_bytes() == outputs[1][0].read_bytes()
        with Image.open(outputs[0][0]) as runtime_image:
            assert runtime_image.convert("RGBA").tobytes() == source_images[0].convert("RGBA").tobytes()

        for mip_index, source_image in enumerate(source_images):
            first_mip = outputs[0][1] / "mips" / f"{mip_index:02d}.png"
            second_mip = outputs[1][1] / "mips" / f"{mip_index:02d}.png"
            assert first_mip.read_bytes() == second_mip.read_bytes()
            with Image.open(first_mip) as imported_mip:
                assert imported_mip.convert("RGBA").tobytes() == source_image.convert("RGBA").tobytes()

        report = yaml.safe_load((outputs[0][1] / "texture_import.yml").read_text(encoding="utf-8"))
        assert report["conversion"]["decodedRgbChanged"] is False
        assert report["conversion"]["decodedAlphaChanged"] is False
        assert report["conversion"]["opaqueAlphaRepair"] is False
        assert report["conversion"]["zeroAlphaRgbPreserved"] is True
        assert report["dtx"]["mipCount"] == len(source_images)
        assert report["source"]["sha256"] == source_metadata["sourceSha256"]
        assert report["runtime"]["texture"] == "engine/effects/mm9/textures/blackwhitering.png"

    report_root = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/import/textures"
    texture_root = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/textures"
    checked_reports = 0
    for report_path in report_root.rglob("texture_import.yml"):
        report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
        texture_path = report["runtime"]["texture"]
        assert texture_path.startswith("engine/effects/mm9/textures/"), report_path
        assert not Path(texture_path).is_absolute(), report_path
        checked_reports += 1
    assert checked_reports == len(list(texture_root.rglob("*.png"))), checked_reports


def check_sprite_bindings() -> None:
    bindings_path = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/resource_bindings.yml"
    bindings_document = yaml.safe_load(bindings_path.read_text(encoding="utf-8"))
    bindings = bindings_document["bindings"]
    legacy_references = [binding["legacy"] for binding in bindings]
    assert len(legacy_references) == len(set(legacy_references))
    assert legacy_references == [reference.replace("\\", "/").lower() for reference in legacy_references]

    checked_sprites = 0
    for binding in bindings:
        if binding["kind"] != "sprite" or binding["status"] != "bound":
            continue
        descriptor_path = REPOSITORY_ROOT / "assets_dev" / binding["asset"]
        if not descriptor_path.exists():
            continue
        descriptor = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
        expected_frames = [frame["resource"] for frame in binding["sprite"]["frames"]]
        assert descriptor["schema"] == "openyamm.effectSprite.v2"
        assert descriptor["frames"] == expected_frames, binding["legacy"]
        assert descriptor["framesPerSecond"] == binding["sprite"]["framesPerSecond"]
        assert descriptor["logicalWidth"] == binding["sprite"]["logicalWidth"]
        assert descriptor["logicalHeight"] == binding["sprite"]["logicalHeight"]
        for resource in descriptor["frames"]:
            texture_binding = next(candidate for candidate in bindings if candidate["resource"] == resource)
            assert texture_binding["kind"] == "texture"
            assert texture_binding["status"] == "bound"
            texture_path = REPOSITORY_ROOT / "assets_dev" / texture_binding["asset"]
            assert texture_path.is_file()
            with Image.open(texture_path) as texture:
                width_scale, width_remainder = divmod(texture.width, descriptor["logicalWidth"])
                height_scale, height_remainder = divmod(texture.height, descriptor["logicalHeight"])
                assert width_remainder == 0 and height_remainder == 0, texture_binding["legacy"]
                assert width_scale == height_scale and width_scale > 0, texture_binding["legacy"]
        checked_sprites += 1
    sprite_root = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/sprites"
    assert checked_sprites == len(list(sprite_root.rglob("*.yml"))), checked_sprites


def check_restoration_overlay() -> None:
    document = yaml.safe_load((REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/resource_bindings.yml").read_text())
    bindings = {binding["legacy"]: binding for binding in document["bindings"]}
    assert load_restorations(REPOSITORY_ROOT, bindings) == {}, "discarded restoration must not be active"
    binding = dict(bindings["spritetextures/bluering.dtx"])
    binding["source"] = dict(binding["source"], path=str(REPOSITORY_ROOT / binding["source"]["path"]))
    with tempfile.TemporaryDirectory(prefix="openyamm-restoration-import-") as temporary_directory:
        temporary = Path(temporary_directory)
        manifest_path = temporary / "tools/mm9_import_discovery/mm9_effect_restorations.yml"
        manifest_path.parent.mkdir(parents=True)
        archive = REPOSITORY_ROOT / "level_generation/sprites/mm9_fxf_effects/spell_reaver/archived_overlay.yml"
        overlay = yaml.safe_load(archive.read_text())
        manifest_path.write_text(yaml.safe_dump(overlay))
        (temporary / "level_generation").symlink_to(REPOSITORY_ROOT / "level_generation", target_is_directory=True)
        (temporary / "mm9").symlink_to(REPOSITORY_ROOT / "mm9", target_is_directory=True)
        restorations = load_restorations(temporary, bindings)
        assert len(restorations) == 22
        restoration = dict(restorations[binding["resource"]])
        restoration["artwork"] = str(REPOSITORY_ROOT / restoration["artwork"])
        output = temporary / "assets_dev" / binding["asset"]
        provenance = temporary / "assets_dev/engine/effects/mm9/import/textures/bluering"
        assert import_texture(temporary, binding, None) == "converted"
        native_bytes = output.read_bytes()
        assert import_texture(temporary, binding, restoration) == "restored"
        assert sha256(output) == restoration["sha256"]
        with Image.open(provenance / "mips/00.png") as native_mip, Image.open(output) as restored:
            assert native_mip.size == (64, 64) and restored.size == (128, 128)
        report = yaml.safe_load((provenance / "texture_import.yml").read_text())
        assert report["restoration"]["sha256"] == restoration["sha256"]
        assert report["conversion"]["decodedAlphaChanged"] is False
        assert import_texture(temporary, binding, restoration) == "restored"
        assert sha256(output) == restoration["sha256"], "reimport lost accepted artwork"
        assert import_texture(temporary, binding, None) == "converted"
        assert output.read_bytes() == native_bytes, "native selection did not restore the original texture"
        assert "restoration" not in yaml.safe_load((provenance / "texture_import.yml").read_text())

        overlay["textures"][0]["sha256"] = "0" * 64
        manifest_path.write_text(yaml.safe_dump(overlay))
        try:
            load_restorations(temporary, bindings)
        except ValueError as error:
            assert "artwork changed" in str(error)
        else:
            raise AssertionError("changed artwork was accepted without matching review")
        assert len(load_restorations(temporary, bindings, verify_artwork=False)) == 22, \
            "explicit native selection should not depend on restored artwork validity"


def check_sprite_orientations() -> None:
    library_path = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/library.yml"
    library = yaml.safe_load(library_path.read_text(encoding="utf-8"))
    world_planes = [
        (effect["id"], component)
        for effect in library["effects"]
        for component in effect["components"]
        if component.get("alignment") == "world_plane"
    ]
    assert len(world_planes) == 12, len(world_planes)
    reaver_components = [
        component
        for effect_id, component in world_planes
        if effect_id == "mm9:spell_reaver"
    ]
    assert len(reaver_components) == 2, reaver_components
    for component in reaver_components:
        assert component["plane_right"] == [0.0, 1.0, 0.0]
        assert component["plane_up"] == [1.0, 0.0, 0.0]


def check_hardcoded_melee_blood() -> None:
    bindings_path = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/resource_bindings.yml"
    bindings = yaml.safe_load(bindings_path.read_text(encoding="utf-8"))["bindings"]
    by_legacy = {binding["legacy"]: binding for binding in bindings}
    for legacy, dimensions in {
        "sprites/bloodhit1.spr": (32, 32),
        "sprites/bloodspray1.spr": (16, 16),
    }.items():
        binding = by_legacy[legacy]
        assert binding["origin"] == "hardcoded_melee_contact"
        assert (binding["sprite"]["logicalWidth"], binding["sprite"]["logicalHeight"]) == dimensions

    library_path = REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/library.yml"
    effects = yaml.safe_load(library_path.read_text(encoding="utf-8"))["effects"]
    blood = next(effect for effect in effects if effect["id"] == "mm9:melee_blood")
    assert blood["duration_seconds"] == 1.0
    assert [component["type"] for component in blood["components"]] == ["sprite", "sprite_system"]
    spray = blood["components"][1]
    assert spray["sprites_per_emission"] == 10
    assert spray["particle_lifetime_seconds"] == 1.0
    assert spray["velocity"] == 256.0


def referenced_effect_groups() -> set[str]:
    """FXF group names MM9 plays: MONSTERS.txt FX0/FX1/FX2/ResurrectFX and the scripts' DoClientFX names."""
    import csv
    import re

    extracted = REPOSITORY_ROOT / "mm9/extracted"
    with (extracted / "DATA/DATA/MONSTERS.txt").open(encoding="latin-1", newline="") as monsters:
        rows = list(csv.reader(monsters, delimiter="\t"))
    columns = [index for index, name in enumerate(rows[0]) if name in ("FX0", "FX1", "FX2", "ResurrectFX")]
    names = {row[index].strip() for row in rows[1:] for index in columns if index < len(row) and row[index].strip()}
    definitions: dict[str, str] = {}
    arguments = []
    for script in (extracted / "SCRIPTS/SCRIPTS").rglob("*"):
        if not script.is_file():
            continue
        text = script.read_text(encoding="latin-1")
        definitions.update(re.findall(r'#string\s+(\w+)\s*=\s*"([^"]*)"', text))
        arguments += [line.split(",")[1].strip() for line in re.findall(r"(?im)^\s*DoClientFX\b([^\r\n]*)", text)]
    for argument in arguments:
        # A bare word that is not a #string (GreaterDemon) is the group name itself.
        names.add(argument.strip('"') if argument.startswith('"') else definitions.get(argument, argument))
    return names


def check_library_completeness() -> None:
    from compile_effect_library import effect_id

    library = yaml.safe_load((REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/library.yml").read_text())
    ids = {effect["id"] for effect in library["effects"]}
    referenced = referenced_effect_groups()
    assert {"redyeldots", "LichKingRes", "greenyeldots", "bluedots", "GreaterDemon"} <= referenced, referenced
    missing = sorted(name for name in referenced if effect_id(name) not in ids)
    assert not missing, f"MM9 plays effects the library lacks: {missing}"
    # PROJECTILE.txt: Lightning and ScreamingSkull explode as "Sparks".
    sparks = next(effect for effect in library["effects"] if effect["id"] == "mm9:explosion_sparks")
    assert [component["type"] for component in sparks["components"]] == ["sprite", "sprite_system"]
    assert sparks["components"][1]["sprites_per_emission"] == 20
    anchored = next(effect for effect in library["effects"] if effect["id"] == "mm9:redyeldots")
    assert anchored["anchor_fallback"] == "origin"
    assert [component["body_anchor"] for component in anchored["components"]] == ["left_hand", "right_hand"]
    capabilities = yaml.safe_load((REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/capabilities.yml").read_text())
    unsupported = {effect["sourceName"] for effect in capabilities["effects"] if effect["status"] != "supported_one_shot"}
    assert unsupported == {"spell-death's touch", "jarjarb setup", "fg spell-eye of the storm", "ghost", "blobby",
                           "spell-armor"}, unsupported


def check_native_additive_components() -> None:
    """MM9's additive light ignores the texture's alpha (LithTech ONE/ONE); its alpha-blended sprites keep it."""
    library = yaml.safe_load((REPOSITORY_ROOT / "assets_dev/engine/effects/mm9/library.yml").read_text())
    additive = 0
    for effect in library["effects"]:
        for component in effect["components"]:
            if component["type"] not in ("sprite", "sprite_system"):
                continue
            native = component.get("additive_texture_alpha", True) is False
            assert native == (component["blend"] == "additive"), (effect["id"], component["id"])
            additive += native
    assert additive > 50, additive


def main() -> int:
    check_model_fixture()
    check_texture_conversion()
    check_sprite_bindings()
    check_restoration_overlay()
    check_sprite_orientations()
    check_hardcoded_melee_blood()
    check_library_completeness()
    check_native_additive_components()
    print("effect asset pipeline checks passed: fixture hashes, RGBA/mips, SPR descriptors, orientations, completeness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
