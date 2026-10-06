#!/usr/bin/env python3
"""Check compiled GLSL shadow variants and the model's integer joint-input contract."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="compiled GLSL directory, e.g. build/runtime/shaders/glsl")
    args = parser.parse_args()
    names = (
        "fs_outdoor_textured_fog", "fs_outdoor_terrain_fog", "fs_outdoor_bmodel_baked",
        "fs_outdoor_terrain_baked", "fs_terrain_decoration", "fs_terrain_decoration_baked",
    )
    for name in names:
        ordinary = (args.directory / f"{name}.bin").read_bytes()
        shadowed = (args.directory / f"{name}_shadow.bin").read_bytes()
        assert ordinary[:3] == shadowed[:3] == b"FSH", f"{name}: invalid fragment shader"
        assert ordinary[:12] == shadowed[:12], f"{name}: vertex/fragment interfaces differ"
        for binding in (b"u_sunShadowParams", b"u_sunShadowMatrices", b"s_sunShadowNear", b"s_sunShadowFar"):
            assert binding not in ordinary, f"{name}: ordinary scenes still carry {binding!r}"
            assert binding in shadowed, f"{name}: shadow receiver missing {binding!r}"
    print(f"Verified {len(names)} receiver-free/shadowed GLSL pairs with matching interfaces.")
    for name in ("vs_model", "vs_model_shadow"):
        shader = (args.directory / f"{name}.bin").read_bytes()
        assert shader[:3] == b"VSH", f"{name}: invalid vertex shader"
        # Unnormalized Uint16 vertex buffers use integer attributes on the GL backend.
        # Float declarations reinterpret bone ids near zero and leave the mesh in its bind pose.
        for attribute in (b"a_indices", b"a_texcoord5"):
            assert b"in uvec4 " + attribute + b";" in shader, f"{name}: {attribute!r} must be unsigned integer"
        for attribute in (b"a_weight", b"a_texcoord3"):
            assert b"in vec4 " + attribute + b";" in shader, f"{name}: missing four skin weights"
    print("Verified integer joint inputs and eight skin-weight slots in model and shadow shaders.")


if __name__ == "__main__":
    main()
