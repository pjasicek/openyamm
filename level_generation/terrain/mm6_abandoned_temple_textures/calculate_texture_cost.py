"""Count texture payload bytes, including every mip; this is not an FPS benchmark."""

import json
from pathlib import Path


base = Path(__file__).resolve().parent
manifest = json.loads((base / "full_manifest.json").read_text())


def payload(width, height, block=None, block_bytes=16, mipmaps=True):
    total = 0
    while True:
        total += (width * height * 4 if block is None else
                  ((width + block - 1) // block) * ((height + block - 1) // block) * block_bytes)
        if not mipmaps or width == height == 1:
            return total
        width, height = max(1, width // 2), max(1, height // 2)


# Small mips still occupy whole compressed blocks, including rectangular textures.
assert payload(4, 4) == 84
assert payload(4, 4, 4) == 48
assert payload(4, 4, 4, 8) == 24
assert payload(8, 1, 4) == 80
assert payload(1024, 1024, 4, mipmaps=False) == 1024 * 1024
assert len(manifest["textures"]) == manifest["count"] == 62

rows = []
baseline = sum(payload(*texture["runtime_size"]) for texture in manifest["textures"])
for scale in (2, 4):
    sizes = [(t["native_size"][0] * scale, t["native_size"][1] * scale) for t in manifest["textures"]]
    for codec, block, block_bytes in (("BGRA8/RGBA8", None, 16), ("BC7/BC3/ASTC4x4", 4, 16), ("BC1", 4, 8)):
        total = sum(payload(w, h, block, block_bytes) for w, h in sizes)
        rows.append(dict(scale=scale, codec=codec, mip_payload_bytes=total, mip_payload_mib=total / 1048576,
                         relative_to_current_2x=total / baseline,
                         base_payload_bytes=sum(payload(w, h, block, block_bytes, False) for w, h in sizes)))

result = dict(
    map=manifest["map"], texture_count=62,
    scope="Static texture payload only; excludes water, sky, actors, UI, geometry, render targets and driver overhead.",
    resolution="2x and 4x mean each native width and height multiplied by 2 or 4, with unchanged logical UV size.",
    current_upload="PNG decoded to BGRA8 on desktop / RGBA8 on Android; full CPU-generated mip chain uploaded.",
    mip_rule="Halve each dimension down to 1, retaining a minimum of 1; round compressed dimensions to whole blocks.",
    formats=rows,
    decoded_base_copy_bytes={str(scale): sum(t["native_size"][0] * t["native_size"][1] * scale * scale * 4
                                           for t in manifest["textures"]) for scale in (2, 4)},
    png_disk_bytes=dict(candidate_2x=sum((base / "runtime" / (t["name"] + ".png")).stat().st_size
                                       for t in manifest["textures"]),
                        baseline_2x=sum((base / "references" / (t["name"] + "_before.png")).stat().st_size
                                       for t in manifest["textures"])),
    fps="Unmeasured. Texture payload size does not determine texture bandwidth or total frame time.",
    illustrative_fps_model="FPS_new/FPS_old = 1 / (1 + f * (r - 1)); f is old frame time fraction affected, r its cost ratio.",
    illustrative_examples=[dict(affected_fraction=f, affected_cost_ratio=r,
                                fps_loss_percent=100 * (1 - 1 / (1 + f * (r - 1))))
                           for f, r in ((0.1, 1.5), (0.1, 2), (0.1, 4))],
    implementation="Compressed wall-texture direct upload is not implemented in the current PNG path; no runtime changes here.",
    sources=["game/indoor/IndoorRenderer.cpp:10206", "game/render/TextureFiltering.cpp:226",
             "engine/ImageMipmaps.cpp:87", "engine/ImageAssetLoader.cpp:105",
             "https://learn.microsoft.com/en-us/windows/win32/direct3d11/texture-block-compression-in-direct3d-11",
             "https://registry.khronos.org/webgl/extensions/WEBGL_compressed_texture_astc/"])
(base / "review/full_texture_cost.json").write_text(json.dumps(result, indent=2) + "\n")
for row in rows:
    print(f'{row["scale"]}x {row["codec"]}: {row["mip_payload_mib"]:.3f} MiB, '
          f'{row["relative_to_current_2x"]:.4f}x current texture payload')
