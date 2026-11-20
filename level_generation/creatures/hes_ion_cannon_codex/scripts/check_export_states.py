#!/usr/bin/env python3
"""Local handoff checks using a synthetic GLB; this is not a production geometry/visual gate."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

PROJECT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = load("export_states")
viewer = load("prepare_viewer")
config = exporter.CONFIG
with tempfile.TemporaryDirectory(prefix="ion_cannon_check_") as directory:
    root = Path(directory)
    binary = bytearray(struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0))
    doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(binary)}],
           "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(binary)}],
           "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
                          "min": [0, 0, 0], "max": [1, 1, 0]}],
           "materials": [{"name": "GC_" + zone} for zone in config["zones"]],
           "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": i}]}
                      for i in range(len(config["zones"]))],
           "nodes": [{"mesh": i} for i in range(len(config["zones"]))],
           "scene": 0, "scenes": [{"nodes": list(range(len(config["zones"])))}]}
    source = root / "fixture.glb"
    exporter.write_glb(source, doc, binary)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    outputs = exporter.export_states(source, root / "export")
    assert len(outputs) == 7
    expected_lit = [set(), {"breech"}, {"breech", "pods"}, {"breech", "pods", "ring1", "ring2"},
                    set(config["zones"]) - {"muzzle"}, set(config["zones"]), set()]
    for (state, _), path, lit in zip(config["states"].items(), outputs, expected_lit):
        result, payload = exporter.read_glb(path)
        assert payload == binary and result["meshes"] == doc["meshes"] and result["nodes"] == doc["nodes"]
        for zone, material in zip(config["zones"], result["materials"]):
            strength = material["extensions"]["KHR_materials_emissive_strength"]["emissiveStrength"]
            expected = 0 if state == "dark" else 16 if state == "c5" and zone == "muzzle" else 10 if zone in lit else 2
            assert strength == expected, (state, zone, strength, expected)
            assert "emissiveTexture" not in material
        assert not result.get("animations")
    # Only c5 may draw the optional arc node; the shared source and material states remain intact.
    with_arcs = copy.deepcopy(doc)
    with_arcs["nodes"].append({"name": "GC_Arcs", "mesh": 0})
    with_arcs["scenes"][0]["nodes"].append(len(with_arcs["nodes"]) - 1)
    arc_source = root / "arc_fixture.glb"
    exporter.write_glb(arc_source, with_arcs, bytearray(binary))
    arc_outputs = exporter.export_states(arc_source, root / "arc_export")
    for state, path in zip(config["states"], arc_outputs):
        result, payload = exporter.read_glb(path)
        assert ("mesh" in result["nodes"][-1]) == (state == "c5"), state
        assert payload == binary
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    for fault in ("missing_zone", "emissive_texture", "animated", "baked_glow"):
        bad = copy.deepcopy(doc)
        if fault == "missing_zone":
            bad["materials"][0]["name"] = "wrong"
        elif fault == "emissive_texture":
            bad["materials"][0]["emissiveTexture"] = {"index": 0}
        elif fault == "animated":
            bad["animations"] = [{"name": "unexpected"}]
        else:
            bad["materials"][0]["pbrMetallicRoughness"] = {"baseColorTexture": {"index": 0}}
        path = root / (fault + ".glb")
        exporter.write_glb(path, bad, bytearray(binary))
        destination = root / fault
        try:
            exporter.export_states(path, destination)
        except ValueError:
            assert not list(destination.glob("*.glb"))
        else:
            raise AssertionError("Accepted " + fault)
    viewer.PROJECT = root
    calls = []
    viewer.command = lambda *args: calls.append(args)
    (root / "review/viewer").mkdir(parents=True)
    viewer.prepare()
    manifest = json.loads((root / "review/viewer/manifest.json").read_text())
    assert len(calls) == len(manifest["models"]) == 7
    for model in manifest["models"]:
        path = root / "review/viewer" / model["url"].split("?")[0]
        result, payload = exporter.read_glb(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == model["sha256"]
        assert result["meshes"] == doc["meshes"]
        assert result["animations"][0]["name"] == "Standing"
        assert payload[:len(binary)] == binary
    (root / "export/hes_great_cannon.glb").unlink()
    try:
        viewer.prepare()
    except ValueError as error:
        assert "Awaiting final Meshy exports" in str(error)
    else:
        raise AssertionError("Accepted missing runtime export")
print("PASS: seven states, unchanged source/geometry/payload, malformed inputs refused, seven static viewer copies.")

