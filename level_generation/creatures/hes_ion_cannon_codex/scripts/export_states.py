#!/usr/bin/env python3
"""Export the Crown's seven material states from a prepared static cannon; never authors geometry."""
import copy
import json
from pathlib import Path
import struct
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parents[2] / "tools"))
from merge_head_material import read_glb, write_glb

CONFIG = json.loads((PROJECT / "charging_states.json").read_text())


def export_states(source, destination):
    raw = source.read_bytes()
    if len(raw) < 28 or struct.unpack_from("<III", raw) != (0x46546C67, 2, len(raw)):
        raise ValueError("Expected a complete GLB 2 file")
    doc, binary = read_glb(source)
    if len(doc.get("buffers", [])) != 1 or "uri" in doc["buffers"][0]:
        raise ValueError("The prepared GLB must contain one embedded buffer")
    if any("uri" in image for image in doc.get("images", [])):
        raise ValueError("Embed the shared texture set before exporting states")
    if doc.get("skins") or doc.get("animations"):
        raise ValueError("The decoration source must be static")
    materials = doc.get("materials", [])
    used = {primitive.get("material") for mesh in doc.get("meshes", []) for primitive in mesh["primitives"]}
    zones = {}
    for zone in CONFIG["zones"]:
        matches = [i for i, material in enumerate(materials) if material.get("name") == "GC_" + zone]
        if len(matches) != 1 or matches[0] not in used:
            raise ValueError("Expected one used, independent material: GC_" + zone)
        zones[zone] = matches[0]
    for index, material in enumerate(materials):
        if "emissiveTexture" in material:
            raise ValueError("Factor-only emission required; remove baked emission during material preparation")
        if index not in zones.values() and any(material.get("emissiveFactor", [])):
            raise ValueError("Unexpected emission outside the four functional glow zones")
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    for state, spec in CONFIG["states"].items():
        result = copy.deepcopy(doc)
        extensions = result.setdefault("extensionsUsed", [])
        if "KHR_materials_emissive_strength" not in extensions:
            extensions.append("KHR_materials_emissive_strength")
        for zone, index in zones.items():
            level = "dark" if state == "dark" else "dim"
            if zone in spec["lit"]:
                level = "hot" if zone == "muzzle" and state == "c5" else "lit"
            settings = CONFIG["levels"][level]
            material = result["materials"][index]
            pbr = material.setdefault("pbrMetallicRoughness", {})
            if "baseColorTexture" in pbr:
                raise ValueError("Glow surfaces need untextured dark glass, not baked white energy")
            pbr.update(baseColorFactor=[0.03, 0.01, 0.06, 1], metallicFactor=0, roughnessFactor=0.25)
            material["emissiveFactor"] = settings["factor"]
            material.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {
                "emissiveStrength": settings["strength"]}
            material.setdefault("extras", {}).update(openyamm_bloom=level != "dark", openyamm_edge_darkening=0)
        for node in result.get("nodes", []):
            if node.get("name") == "GC_Arcs" and state != "c5":
                node.pop("mesh", None)
        target = destination / spec["file"]
        if target.resolve() == source.resolve():
            raise ValueError("Preserve the prepared source; export to a different path")
        write_glb(target, result, bytearray(binary))
        outputs.append(target)
    return outputs


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: export_states.py <prepared-static-GLB>")
    for path in export_states(Path(sys.argv[1]), PROJECT / "export"):
        print(path.relative_to(PROJECT))
