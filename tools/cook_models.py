#!/usr/bin/env python3
"""Cook source model GLBs (assets_source) into runtime GLBs: geometry passes and GPU block-compressed textures.

The desktop profile writes each cooked GLB and its textures into assets_dev; the android profile writes only its own
textures into assets_cooked/android (the GLB is identical across profiles). A cooked GLB references its textures as
textures/<key>.oytex beside it; the key depends on the source image and how the model samples it, never on the
codec, so identical images used the same way are stored once and every profile shares one GLB. The geometry passes
(tools/cook_model_geometry.py: hidden back faces culled, burn order baked per vertex, vertex cache order) run
before the textures.

The cook is incremental and idempotent: a model whose source, rules, COOKER_REVISION and cook scripts are unchanged,
and whose outputs are intact, is skipped without being read further; anything else is cooked again, and the same
inputs give the same bytes. A full run (no --only) also removes cooked GLBs whose source is gone and textures that no
model references. assets_dev then holds only cooked models; sources live in assets_source.

  tools/cook_models.py --plan [--only PATTERN]       decisions and projected sizes; writes nothing
  tools/cook_models.py --profile desktop|android     cook changed models (receipts in assets_source/.cook-cache)
  tools/cook_models.py --verify                      validate the cooked runtime files without sources
  tools/cook_models.py --migrate [--apply]           list (or move) models that exist only in assets_dev

Decisions come from tools/cook/model_textures.yml and optional <model>.cook.yml sidecars. See ASSET_COOKING_PLAN.md.
"""
import argparse
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import time

import numpy as np
import yaml
from PIL import Image

import cook_model_geometry

ROOT = Path(__file__).resolve().parent.parent
GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
COOKED_EXTRAS = "openyamm_cooked"
DEFAULT_OUTPUT = {"desktop": "assets_dev", "android": "assets_cooked/android"}
# Bump when the cooker (openyamm_model_texture_cook: cook_model_textures_main.cpp, CookModelGeometry.cpp,
# TextureBlockEncode.cpp) writes different output for the same inputs. Receipts record this instead of the binary's
# hash, which changed with every rebuild of openyamm_engine and made the next cook redo every texture.
COOKER_REVISION = 1


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_glb(data):
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2 or length != len(data):
        raise ValueError("not a glTF 2.0 binary")
    document, binary, offset = None, b"", 12
    while offset < len(data):
        size, kind = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8:offset + 8 + size]
        if kind == CHUNK_JSON:
            document = json.loads(chunk)
        elif kind == CHUNK_BIN:
            binary = chunk
        offset += 8 + size
    if document is None:
        raise ValueError("GLB has no JSON chunk")
    return document, binary


def write_glb(document, binary):
    text = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    text += b" " * (-len(text) % 4)
    binary = binary + b"\0" * (-len(binary) % 4)
    chunks = struct.pack("<II", len(text), CHUNK_JSON) + text
    if binary:
        chunks += struct.pack("<II", len(binary), CHUNK_BIN) + binary
    return struct.pack("<III", GLB_MAGIC, 2, 12 + len(chunks)) + chunks


def image_bytes(document, binary, index):
    image = document["images"][index]
    if "bufferView" not in image:
        raise ValueError(f"image {index} is not embedded; source GLBs embed their PNG textures")
    view = document["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    data = binary[start:start + view["byteLength"]]
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"image {index} is not a PNG")
    return data


def sampler_uses_mips(document, texture):
    sampler = document.get("samplers", [])[texture["sampler"]] if "sampler" in texture else {}
    minimum = sampler.get("minFilter", 0)
    return minimum == 0 or minimum >= 9984


def texture_uses(document):
    """Every (material, slot, texture index, semantic, alpha cutoff) the engine samples, mirroring
    ModelRenderer::prepare and GltfModelLoader. Unsampled slots are rejected rather than silently dropped."""
    uses = []
    for material_index, material in enumerate(document.get("materials", [])):
        if "occlusionTexture" in material:
            raise ValueError(f"material {material_index} uses occlusionTexture, which the engine does not sample")
        if any("Texture" in key for extension in material.get("extensions", {}).values() for key in extension):
            raise ValueError(f"material {material_index} has a texture in a material extension")
        pbr = material.get("pbrMetallicRoughness", {})
        if "baseColorTexture" in pbr:
            cutoff = 0
            if material.get("alphaMode") == "MASK":
                # The renderer's float32 arithmetic, so boundary values such as 0.2 * 255 round the same way.
                factor = np.float32(pbr.get("baseColorFactor", [1, 1, 1, 1])[3])
                value = np.ceil(np.float32(material.get("alphaCutoff", 0.5)) * np.float32(255)
                                / max(factor, np.float32(1.0e-6)))
                cutoff = int(min(max(value, 1.0), 255.0))
            uses.append((material_index, ("pbrMetallicRoughness", "baseColorTexture"), pbr["baseColorTexture"]["index"],
                         "srgb", cutoff, material.get("alphaMode", "OPAQUE") != "OPAQUE"))
        if "normalTexture" in material:
            uses.append((material_index, ("normalTexture",), material["normalTexture"]["index"], "normal", 0, False))
        if "metallicRoughnessTexture" in pbr:
            uses.append((material_index, ("pbrMetallicRoughness", "metallicRoughnessTexture"),
                         pbr["metallicRoughnessTexture"]["index"], "linear", 0, False))
        mask = material.get("extras", {}).get("openyamm_region_mask")
        if mask is not None:
            uses.append((material_index, ("extras", "openyamm_region_mask"), mask["index"], "linear", 0, False))
        burn = material.get("extras", {}).get("openyamm_burn_map")
        if burn is not None:
            uses.append((material_index, ("extras", "openyamm_burn_map"), burn["index"], "linear", 0, False))
        if "emissiveTexture" in material:
            # Emission (sRGB, like a colour map): the glow of energy parts, ModelMaterial::emissiveImageIndex.
            uses.append((material_index, ("emissiveTexture",), material["emissiveTexture"]["index"], "srgb", 0,
                         False))
    return uses



def role_of(slot):
    return {"baseColorTexture": "colour", "normalTexture": "normal", "metallicRoughnessTexture": "metallic_roughness",
            "openyamm_region_mask": "region_mask", "openyamm_burn_map": "burn_map",
            "emissiveTexture": "emissive"}[slot[-1]]


class Rules:
    def __init__(self, path):
        self.text = path.read_bytes()
        self.data = yaml.safe_load(self.text)
        if self.data.get("version") != 1:
            raise ValueError(f"Unsupported rules version in {path}")

    def model_class(self, relative):
        for entry in self.data["classes"]:
            if fnmatch.fnmatch(relative, entry["match"]):
                return entry
        raise ValueError(f"No asset class in the cook rules matches {relative}")


def per_profile(value, profile):
    return value[profile] if isinstance(value, dict) else value


def reduced_max_size(reductions, role, size, hints):
    """Size cap from the rules' `reductions` (classes with `reduce: true`): visually lossless shrinking measured on the
    source image. hints: lods (LOD levels sampling the texture), prop (a held attachment), psnr (dB after a 2x
    down-and-up resample), empty (fraction of near-black texels)."""
    largest = 1 << (max(size).bit_length() - 1)
    cap = largest
    lods = hints["lods"]
    if lods and 0 not in lods:
        caps = reductions.get("prop_lod_caps" if hints["prop"] else "lod_caps", {})
        cap = min(cap, caps.get(min(lods), cap))
    if hints["prop"] and role != "region_mask":
        cap = min(cap, reductions.get("prop_max_size", cap))
    if role in ("colour", "metallic_roughness", "emissive") and hints["psnr"] >= reductions.get("flat_psnr", 99):
        cap = min(cap, reductions.get("flat_max_size", cap))
    if role == "metallic_roughness" and hints["psnr"] >= reductions.get("halve_psnr", 99) \
            and largest >= reductions.get("halve_min_size", 1 << 30):
        cap = min(cap, largest // 2)
    if role == "colour" and hints["empty"] >= reductions.get("empty_fraction", 2) \
            and largest > reductions.get("empty_min_size", 1 << 30):
        cap = min(cap, largest // 2)
    return max(1, cap)


def texture_hints(png, role, lods, prop):
    image = Image.open(io.BytesIO(png)).convert("RGB")
    w, h = image.size
    psnr, empty = 99.0, 0.0
    if role in ("colour", "metallic_roughness", "emissive") and w >= 8 and h >= 8:
        a = np.asarray(image, dtype=np.float32)
        b = np.asarray(image.resize((w // 2, h // 2), Image.BOX).resize((w, h), Image.BICUBIC), dtype=np.float32)
        mse = float(np.mean((a - b) ** 2))
        psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
        empty = float(np.mean(a.max(axis=2) < 4))
    return {"lods": sorted(lods), "prop": prop, "psnr": round(float(psnr), 2), "empty": round(empty, 4)}


def material_lods(document):
    """Material index -> LOD levels of the meshes that draw it (mesh name ..._LOD<n>, else 0; variants included)."""
    lods = {}
    for mesh in document.get("meshes", []):
        found = re.search(r"LOD(\d)", mesh.get("name") or "", re.I)
        level = int(found.group(1)) if found else 0
        for primitive in mesh["primitives"]:
            materials = {primitive["material"]} if "material" in primitive else set()
            for mapping in primitive.get("extensions", {}).get("KHR_materials_variants", {}).get("mappings", []):
                materials.add(mapping["material"])
            for material in materials:
                lods.setdefault(material, set()).add(level)
    return lods


_ATTACHMENTS = {}


def is_attachment(relative):
    """True for a model that actors.yml uses only as an attachment (a held weapon, shield or prop)."""
    parts = Path(relative).parts
    if len(parts) < 3 or parts[0] != "worlds":
        return False
    world = parts[1]
    if world not in _ATTACHMENTS:
        bodies, props = set(), set()
        path = ROOT / "assets_dev" / "worlds" / world / "models" / "actors.yml"
        if path.exists():
            for actor in (yaml.safe_load(path.read_text()) or {}).get("actors", []):
                bodies.add(Path(actor["model"]).name)
                for attachment in actor.get("attachments") or []:
                    props.add(Path(attachment["model"]).name)
        _ATTACHMENTS[world] = props - bodies
    return Path(relative).name in _ATTACHMENTS[world]


def decide(rules, relative, sidecar, image_name, role, uses_alpha, profile, size, hints=None):
    entry = rules.model_class(relative)
    quality = sidecar.get("quality", entry["quality"])
    max_size = per_profile(sidecar.get("max_size", entry["max_size"]), profile)
    override = sidecar.get("images", {}).get(image_name, {})
    if role == "normal":
        # Normal maps carry fine relief, not colour: by default they cook at half the source's (power-of-two) size.
        scale = per_profile(sidecar.get("normal_scale", entry.get("normal_scale", rules.data.get("normal_scale", 1))),
                            profile)
        largest = 1 << (max(size).bit_length() - 1)
        max_size = min(max_size, max(1, int(largest * scale)))
    if role in entry.get("role_max_size", {}):
        max_size = min(max_size, per_profile(entry["role_max_size"][role], profile))
    if hints is not None and entry.get("reduce"):
        max_size = min(max_size, reduced_max_size(rules.data.get("reductions", {}), role, size, hints))
    max_size = per_profile(override.get("max_size", max_size), profile)
    codecs = rules.data["codecs"][profile]
    if role == "colour":
        key = "colour_alpha" if uses_alpha else ("colour_hero" if quality == "hero" else "colour")
    elif role == "emissive":
        # An emission map cooks as an opaque colour map of the model's quality.
        key = "colour_hero" if quality == "hero" else "colour"
    else:
        key = role
    codec = per_profile(override["codec"], profile) if "codec" in override else codecs[key]
    # Unsharp mask on the colour mips below the first (cook_model_textures_main.cpp sharpenMips); 0 = plain filtering.
    sharpening = float(per_profile(sidecar.get("colour_mip_sharpening", entry.get("colour_mip_sharpening", 0)),
                                   profile)) if role == "colour" else 0.0
    # Never below one 4x4 block: bgfx counts a compressed texture's mips from its size rounded up to whole blocks, so
    # a smaller mipped texture is read past its end (a 4x4 normal map at normal_scale 0.5 crashed SwiftShader).
    return codec, max(int(max_size), 4), sharpening


def normal_relief(png):
    """90th percentile of a normal map's tangent-plane tilt |xy| over its relief texels: flat padding (|xy| <= 0.01)
    and invalid texels (|xy| >= 0.9) are left out."""
    texels = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), dtype=np.float32)[..., :2] / 127.5 - 1.0
    tilt = np.hypot(texels[..., 0], texels[..., 1])
    relief = tilt[(tilt > 0.01) & (tilt < 0.9)]
    return float(np.percentile(relief, 90)) if relief.size else 0.0


def normal_strength(rules, relative, sidecar, png):
    """Multiplier of a material's glTF normalTexture.scale in the cooked model. A sidecar's `normal_strength` fixes it;
    a class's `normal_relief` ({target, max}) lifts weak maps toward the target relief (normal_relief) and never weakens
    one; otherwise 1 (as authored)."""
    if "normal_strength" in sidecar:
        return float(sidecar["normal_strength"])
    lift = rules.model_class(relative).get("normal_relief")
    if not lift:
        return 1.0
    relief = normal_relief(png)
    return round(min(float(lift["max"]), max(1.0, float(lift["target"]) / relief)) if relief > 0 else 1.0, 3)


def alpha_in_use(png, threshold):
    image = Image.open(io.BytesIO(png))
    if image.mode not in ("RGBA", "LA", "PA") and "transparency" not in image.info:
        return False
    return image.convert("RGBA").getchannel("A").getextrema()[0] < threshold


def plan_model(rules, source_root, path, profiles, cooker=None):
    """The cooked document, BIN and the textures it needs, per profile. With the cooker, the geometry passes run
    first (a cook); without it (a plan) the geometry is left as it is."""
    relative = path.relative_to(source_root).as_posix()
    data = path.read_bytes()
    document, binary = read_glb(data)
    sidecar_path = path.with_suffix(".cook.yml")
    sidecar = yaml.safe_load(sidecar_path.read_text()) if sidecar_path.exists() else {}
    if sidecar.get("back_faces", "cull") not in ("cull", "keep"):
        raise ValueError(f"{sidecar_path}: back_faces must be cull or keep")
    geometry = None
    if cooker is not None:
        binary, geometry = cook_model_geometry.cook_geometry(document, binary, cooker,
                                                             cull_back_faces=sidecar.get("back_faces") != "keep")
    for name in document.get("extensionsUsed", []):
        if name.startswith(("EXT_meshopt", "KHR_draco", "KHR_texture")):
            raise ValueError(f"{relative}: unsupported extension {name}")
    if any("sparse" in accessor for accessor in document.get("accessors", [])):
        raise ValueError(f"{relative}: sparse accessors are not supported by the cooker")
    threshold = rules.data["alpha_threshold"]
    textures, images, new_textures = {}, [], []
    image_by_key, texture_by_pair = {}, {}
    uses = texture_uses(document)
    # Measured on the source images, before the texture slots are remapped to the cooked ones.
    normal_strengths, by_image = {}, {}
    for index, material in enumerate(document.get("materials", [])):
        if "normalTexture" in material:
            source = document["textures"][material["normalTexture"]["index"]]["source"]
            if source not in by_image:
                by_image[source] = normal_strength(rules, relative, sidecar, image_bytes(document, binary, source))
            normal_strengths[index] = by_image[source]
    lods_by_material = material_lods(document)
    image_lods = {}  # by image content: identical bytes in two image slots share one cooked texture
    for material_index, _, texture_index, _, _, _ in uses:
        content = sha256(image_bytes(document, binary, document["textures"][texture_index]["source"]))
        image_lods.setdefault(content, set()).update(lods_by_material.get(material_index, {0}))
    prop = is_attachment(relative)
    for material_index, slot, texture_index, semantic, cutoff, blended in uses:
        texture = document["textures"][texture_index]
        source_index = texture["source"]
        png = image_bytes(document, binary, source_index)
        mips = sampler_uses_mips(document, texture)
        key = sha256(png + f"|{semantic}|{cutoff}|{int(mips)}".encode())[:32]
        role = role_of(slot)
        uses_alpha = role == "colour" and blended and alpha_in_use(png, threshold)
        name = document["images"][source_index].get("name", str(source_index))
        if key not in textures:
            size = Image.open(io.BytesIO(png)).size
            textures[key] = {"key": key, "png": png, "png_sha256": sha256(png), "semantic": semantic,
                             "cutoff": cutoff, "mips": mips, "role": role, "alpha": uses_alpha, "name": name,
                             "size": size, "decisions": {}}
            hints = texture_hints(png, role, image_lods.get(sha256(png), {0}), prop) \
                if rules.model_class(relative).get("reduce") else None
            textures[key]["hints"] = hints
            for profile in profiles:
                textures[key]["decisions"][profile] = decide(rules, relative, sidecar, name, role, uses_alpha,
                                                             profile, size, hints)
        if key not in image_by_key:
            image_by_key[key] = len(images)
            images.append({"name": name, "uri": f"textures/{key}.oytex"})
        pair = (texture.get("sampler"), image_by_key[key])
        if pair not in texture_by_pair:
            texture_by_pair[pair] = len(new_textures)
            entry = {"source": image_by_key[key]}
            if texture.get("sampler") is not None:
                entry["sampler"] = texture["sampler"]
            new_textures.append(entry)
        target = document["materials"][material_index]
        for part in slot:
            target = target[part]
        target["index"] = texture_by_pair[pair]
    for material, strength in normal_strengths.items():
        if strength != 1:
            target = document["materials"][material]["normalTexture"]
            target["scale"] = round(target.get("scale", 1.0) * strength, 6)
    # Drop the embedded image buffer views and compact the binary chunk.
    image_views = {image["bufferView"] for image in document.get("images", []) if "bufferView" in image}
    remap, views, compacted = {}, [], bytearray()
    for index, view in enumerate(document.get("bufferViews", [])):
        if index in image_views:
            continue
        start = view.get("byteOffset", 0)
        compacted += b"\0" * (-len(compacted) % 4)
        moved = dict(view, byteOffset=len(compacted))
        compacted += binary[start:start + view["byteLength"]]
        remap[index] = len(views)
        views.append(moved)
    for accessor in document.get("accessors", []):
        if "bufferView" in accessor:
            accessor["bufferView"] = remap[accessor["bufferView"]]
    document["bufferViews"] = views
    if document.get("buffers"):
        document["buffers"] = [{"byteLength": len(compacted)}]
    document["images"] = images
    document["textures"] = new_textures
    if not images:
        document.pop("images")
        document.pop("textures")
    extras = document.setdefault("asset", {}).setdefault("extras", {})
    extras.pop(cook_model_geometry.LEGACY_MARKER, None)
    extras[COOKED_EXTRAS] = {"source": relative, "source_sha256": sha256(data)}
    if geometry is not None:
        extras[COOKED_EXTRAS]["geometry"] = geometry
    return {"relative": relative, "source_sha256": sha256(data), "document": document,
            "binary": bytes(compacted), "textures": list(textures.values())}


# Folders whose GLBs are models: every package's models/ and the engine's first-person view model.
MODEL_FOLDERS = ("models", "view_model")


def source_models(source_root, only):
    paths = sorted(path for path in source_root.rglob("*.glb")
                   if ".cook-cache" not in path.parts and path.parent.name in MODEL_FOLDERS)
    if only:
        paths = [path for path in paths if fnmatch.fnmatch(path.relative_to(source_root).as_posix(), only)]
    return paths


def reconcile(rules, models, profiles):
    """One decision per texture key: a texture shared by models of different classes takes the larger size and the
    higher-quality codec (more bytes per texel) of its uses. Returns the keys whose decisions were unified."""
    rates = rules.data["estimate_bytes_per_texel"]
    chosen, unified = {}, set()
    for model in models:
        for texture in model["textures"]:
            for profile in profiles:
                decision = tuple(texture["decisions"][profile])
                best = chosen.get((texture["key"], profile))
                if best is None:
                    chosen[(texture["key"], profile)] = decision
                elif best != decision:
                    unified.add(texture["key"])
                    chosen[(texture["key"], profile)] = (max(best[0], decision[0], key=lambda name: rates[name]),
                                                         max(best[1], decision[1]), max(best[2], decision[2]))
    for model in models:
        for texture in model["textures"]:
            for profile in profiles:
                texture["decisions"][profile] = chosen[(texture["key"], profile)]
    return unified


def print_plan(rules, models, profiles):
    rates = rules.data["estimate_bytes_per_texel"]
    totals = {profile: 0.0 for profile in profiles}
    seen, source_bytes, unique_bytes = set(), 0, 0
    for model in models:
        print(model["relative"])
        for texture in model["textures"]:
            # The cooker resamples non-power-of-two sources down to powers of two (see cook_model_textures_main).
            width, height = (1 << (side.bit_length() - 1) for side in texture["size"])
            source_bytes += len(texture["png"])
            line = f"  {texture['role']:<18} {texture['size'][0]}x{texture['size'][1]} {'alpha ' if texture['alpha'] else ''}" \
                   f"{texture['name'][:28]:<28}"
            for profile in profiles:
                codec, max_size, _ = texture["decisions"][profile]
                scale = 1.0
                while max(width, height) * scale > max_size:
                    scale /= 2
                estimate = width * height * scale * scale * 4 / 3 * rates[codec]
                line += f"  {profile} {codec} {int(width * scale)}x{int(height * scale)} ~{estimate / 1e6:.2f} MB"
                if texture["key"] not in seen:
                    totals[profile] += estimate
            if texture["key"] in seen:
                line += "  (shared)"
            else:
                unique_bytes += len(texture["png"])
            seen.add(texture["key"])
            print(line)
    print(f"\n{len(models)} models, {len(seen)} unique textures; source PNG {source_bytes / 1e6:.0f} MB "
          f"({unique_bytes / 1e6:.0f} MB unique)")
    for profile in profiles:
        print(f"  {profile}: ~{totals[profile] / 1e6:.0f} MB of cooked textures (estimate)")


def texture_fingerprint(recipe, texture, profile):
    codec, max_size, sharpening = texture["decisions"][profile]
    return dict(recipe, png=texture["png_sha256"], codec=codec, max_size=max_size, sharpening=sharpening,
                semantic=texture["semantic"],
                cutoff=texture["cutoff"], mips=texture["mips"])


def texture_receipt(texture, profile):
    """What a model receipt keeps of a texture: enough to reconcile and check it without the source PNG."""
    return {key: texture[key] for key in ("key", "png_sha256", "semantic", "cutoff", "mips", "role", "alpha", "name")} \
        | {"size": list(texture["size"]), "decision": list(texture["decisions"][profile])}


def model_inputs(base, path):
    sidecar = path.with_suffix(".cook.yml")
    return dict(base, source=sha256(path.read_bytes()),
                sidecar=sha256(sidecar.read_bytes()) if sidecar.exists() else None)


def intact(cache, output_root, relative, receipt, texture_recipe, profile):
    """True when the model's outputs are exactly what its receipt recorded."""
    if profile == "desktop":
        target = output_root / relative
        if not target.exists() or sha256(target.read_bytes()) != receipt["output"]:
            return False
    directory = output_root / Path(relative).parent / "textures"
    for texture in receipt["textures"]:
        target = directory / f"{texture['key']}.oytex"
        entry = cache.get(str(target.relative_to(output_root)))
        expected = texture_fingerprint(texture_recipe, dict(texture, decisions={profile: tuple(texture["decision"])}),
                                       profile)
        if not entry or entry["inputs"] != expected or not target.exists() \
                or sha256(target.read_bytes()) != entry["output"]:
            return False
    return True


class Progress:
    """Cooked/total textures with rate and remaining time: a rewritten line on a terminal, otherwise a line every
    30 seconds (build logs)."""

    def __init__(self, profile, total):
        self.profile = profile
        self.total = total
        self.started = time.monotonic()
        self.shown = 0.0
        self.terminal = sys.stdout.isatty()

    def update(self, done):
        now = time.monotonic()
        if done < self.total and now - self.shown < (1 if self.terminal else 30):
            return
        self.shown = now
        elapsed = now - self.started
        line = f"Model cook ({self.profile}): {done}/{self.total} textures ({100 * done // self.total}%)"
        if done and elapsed > 1:
            rate = done / elapsed
            line += f", {rate * 60:.0f}/min"
            if done < self.total:
                line += f", about {max(1, round((self.total - done) / rate / 60))} min left"
        print(("\r" + line + " " * 8) if self.terminal else line, end="\n" if not self.terminal or done == self.total
              else "", flush=True)


def save_cache(path, cache):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n")
    os.replace(temporary, path)


def cook(args, rules, paths):
    profile = args.profile
    output_root = (args.output or ROOT / DEFAULT_OUTPUT[profile]).resolve()
    source_root = args.source.resolve()
    if source_root == output_root or source_root in output_root.parents or output_root in source_root.parents:
        raise ValueError("Source and output roots must be separate, non-nested directories")
    cooker = args.cooker.resolve(strict=True)
    cache_path = source_root / ".cook-cache" / "models" / f"{profile}.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() and not args.force else {}
    # A texture's receipt holds its decision (codec, size, sharpening), which is all the rules change in its bytes, so
    # an edit of the rules file re-cooks only the textures whose decision it changes; the model receipts keep the
    # rules' hash (normal_relief changes the cooked GLB). Migration: texture receipts written before 2026-11-14 also
    # recorded the rules' hash.
    for key, receipt in cache.items():
        if not key.startswith("model:"):
            receipt["inputs"].pop("rules", None)
    texture_recipe = {"cooker": COOKER_REVISION, "profile": profile}
    scripts = sha256(Path(__file__).read_bytes() + Path(cook_model_geometry.__file__).read_bytes())
    model_recipe = dict(texture_recipe, rules=sha256(rules.text), scripts=scripts,
                        geometry=cook_model_geometry.recipe())

    # Unchanged models with intact outputs are taken from their receipts; the rest are planned (geometry included).
    models, skipped = [], 0
    for path in paths:
        relative = path.relative_to(source_root).as_posix()
        inputs = model_inputs(model_recipe, path)
        receipt = cache.get("model:" + relative)
        if receipt and receipt["inputs"] == inputs and intact(cache, output_root, relative, receipt, texture_recipe,
                                                              profile):
            textures = [dict(texture, size=tuple(texture["size"]), decisions={profile: tuple(texture["decision"])})
                        for texture in receipt["textures"]]
            models.append({"relative": relative, "path": path, "inputs": inputs, "receipt": receipt,
                           "textures": textures})
            skipped += 1
        else:
            models.append(dict(plan_model(rules, source_root, path, [profile], cooker), path=path, inputs=inputs))
    # A shared texture takes the largest decision of its uses; a skipped model whose decision that changes is cooked.
    while True:
        reconcile(rules, models, [profile])
        changed = [index for index, model in enumerate(models) if "receipt" in model
                   and any(texture["decisions"][profile] != tuple(texture["decision"])
                           for texture in model["textures"])]
        if not changed:
            break
        for index in changed:
            models[index] = dict(plan_model(rules, source_root, models[index]["path"], [profile], cooker),
                                 path=models[index]["path"], inputs=models[index]["inputs"])
            skipped -= 1

    jobs, written, retained = [], 0, 0
    with tempfile.TemporaryDirectory(prefix="cook-models-") as scratch:
        scratch = Path(scratch)
        for model in models:
            if "receipt" in model:
                continue
            directory = output_root / Path(model["relative"]).parent
            for texture in model["textures"]:
                codec, max_size, sharpening = texture["decisions"][profile]
                fingerprint = texture_fingerprint(texture_recipe, texture, profile)
                target = directory / "textures" / f"{texture['key']}.oytex"
                receipt = cache.get(str(target.relative_to(output_root)))
                if receipt and receipt["inputs"] == fingerprint and target.exists() \
                        and sha256(target.read_bytes()) == receipt["output"]:
                    continue
                if any(job[1] == target for job in jobs):
                    continue
                png_path = scratch / f"{texture['key']}.png"
                png_path.write_bytes(texture["png"])
                linear = texture["role"] in ("metallic_roughness", "region_mask", "burn_map")
                jobs.append((png_path, target, codec, texture["semantic"], texture["cutoff"], texture["mips"],
                             max_size, linear, texture["png_sha256"][:16], fingerprint, sharpening))
            if profile == "desktop":
                glb = write_glb(model["document"], model["binary"])
                target = output_root / model["relative"]
                model["output"] = sha256(glb)
                if target.exists() and target.read_bytes() == glb:
                    retained += 1
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_suffix(".glb.tmp")
                    temporary.write_bytes(glb)
                    os.replace(temporary, target)
                    written += 1
        failed = set()
        if jobs:
            job_file = scratch / "jobs.tsv"
            job_file.write_text("".join(
                f"{job[0]}\t{job[1]}\t{job[2]}\t{job[3]}\t{job[4]}\t{int(job[5])}\t{job[6]}\t{int(job[7])}\t{job[8]}"
                + (f"\tmodel\t{job[10]:g}" if job[10] > 0 else "") + "\n"
                for job in jobs))
            # The cooker reports each finished texture on stdout; its errors go straight to stderr. Each texture's
            # receipt is kept as it finishes and saved every 30 seconds and on an interruption, so a stopped cook
            # resumes where it stopped.
            done = set()
            fingerprints = {job[1]: job[9] for job in jobs}
            progress = Progress(profile, len(jobs))
            saved = time.monotonic()
            try:
                with subprocess.Popen([str(cooker), str(job_file)], text=True, stdout=subprocess.PIPE) as process:
                    for line in process.stdout:
                        if line.startswith("cooked\t"):
                            target = Path(line.split("\t")[1])
                            done.add(target)
                            cache[str(target.relative_to(output_root))] = {"inputs": fingerprints[target],
                                                                           "output": sha256(target.read_bytes())}
                            progress.update(len(done))
                            if time.monotonic() - saved > 30:
                                save_cache(cache_path, cache)
                                saved = time.monotonic()
            finally:
                save_cache(cache_path, cache)
            if progress.terminal and len(done) < len(jobs):
                print(flush=True)
            failed = {job[1] for job in jobs if job[1] not in done}
        # Model receipts, only for models whose every texture is in place.
        for model in models:
            if "receipt" in model:
                continue
            directory = output_root / Path(model["relative"]).parent / "textures"
            if any(directory / f"{texture['key']}.oytex" in failed for texture in model["textures"]):
                cache.pop("model:" + model["relative"], None)
                continue
            cache["model:" + model["relative"]] = {
                "inputs": model["inputs"], "output": model.get("output"),
                "textures": [texture_receipt(texture, profile) for texture in model["textures"]]}
    pruned = removed_models = 0
    if not args.only:
        wanted = {output_root / Path(model["relative"]).parent / "textures" / f"{texture['key']}.oytex"
                  for model in models for texture in model["textures"]}
        for directory in sorted({path.parent for path in wanted}):
            for path in directory.glob("*.oytex"):
                if path not in wanted:
                    path.unlink()
                    cache.pop(str(path.relative_to(output_root)), None)
                    pruned += 1
        # Cooked models whose source is gone (sources that are still there were all listed).
        current = {model["relative"] for model in models}
        if profile == "desktop":
            for path, document in cooked_models(output_root):
                relative = path.relative_to(output_root).as_posix()
                if relative not in current:
                    path.unlink()
                    removed_models += 1
        for key in [key for key in cache if key.startswith("model:") and key[len("model:"):] not in current]:
            del cache[key]
    save_cache(cache_path, cache)
    print(f"Model cook ({profile}): {len(models)} models ({skipped} unchanged and skipped, {written} GLBs "
          f"written, {retained} rewritten identically), {len(jobs)} textures cooked, {pruned} unreferenced textures "
          f"and {removed_models} models without a source removed, into {output_root}")
    if failed:
        raise SystemExit(f"{len(failed)} of {len(jobs)} textures failed to cook")


def cooked_models(dev_root, only=None):
    for path in source_models(dev_root, only):
        document, _ = read_glb(path.read_bytes())
        if COOKED_EXTRAS in document.get("asset", {}).get("extras", {}):
            yield path, document


def verify(args):
    dev_root = (args.dev or ROOT / DEFAULT_OUTPUT["desktop"]).resolve()
    roots = {"desktop": dev_root, "android": (args.android or ROOT / DEFAULT_OUTPUT["android"]).resolve()}
    profiles = [args.profile] if args.profile else ["desktop", "android"]
    cooker = args.cooker.resolve(strict=True)
    problems, expected, referenced = [], {}, set()
    count = 0
    for path, document in cooked_models(dev_root, args.only):
        count += 1
        for _, _, texture_index, semantic, cutoff, _ in texture_uses(document):
            texture = document["textures"][texture_index]
            uri = document["images"][texture["source"]]["uri"]
            relative = (path.parent / uri).relative_to(dev_root)
            expected[relative] = (semantic, cutoff, sampler_uses_mips(document, texture))
            referenced.add(relative)
    for root in (roots[profile] for profile in profiles):
        files = [root / relative for relative in sorted(expected)]
        missing = [str(path) for path in files if not path.exists()]
        problems += [f"missing {path}" for path in missing]
        present = [path for path in files if path.exists()]
        for start in range(0, len(present), 500):
            batch = present[start:start + 500]
            result = subprocess.run([str(cooker), "--verify", *map(str, batch)], text=True, capture_output=True)
            problems += [line for line in result.stderr.splitlines() if line]
            for line in result.stdout.splitlines():
                name, codec, semantic, cutoff, width, height, levels = line.split("\t")[:7]
                want = expected[Path(name).relative_to(root)]
                if (semantic, int(cutoff), int(levels) > 1) != want:
                    problems.append(f"{name} was cooked as {semantic}/{cutoff}/{levels} levels, used as {want}")
        # A selected model does not own every texture in its shared directory.
        for textures in sorted({(root / relative).parent for relative in expected}) if not args.only else []:
            for path in sorted(textures.glob("*.oytex")):
                if path.relative_to(root) not in referenced:
                    problems.append(f"unreferenced {path}")
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"Verified {count} cooked models and {len(expected)} textures per profile: {len(problems)} problems")
    return 1 if problems else 0


def migrate(args):
    """Models only in the runtime root: every uncooked model GLB under --dev without a source at the same relative path
    under --source moves there (same inode, so hard links to creature project outputs keep pointing at it). Without
    --apply it only lists them. Uncooked runtime copies of existing sources stay; the cook replaces them."""
    dev_root = (args.dev or ROOT / DEFAULT_OUTPUT["desktop"]).resolve()
    source_root = args.source.resolve()
    moves, copies = [], 0
    for path in source_models(dev_root, args.only):
        if "fixtures" in path.parts:
            continue
        document, _ = read_glb(path.read_bytes())
        if COOKED_EXTRAS in document.get("asset", {}).get("extras", {}):
            continue
        target = source_root / path.relative_to(dev_root)
        if target.exists():
            copies += 1
        else:
            moves.append((path, target))
    for path, target in moves:
        print(f"{'move' if args.apply else 'would move'} {path.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
    if args.apply:
        for path, target in moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(path, target)
    print(f"{len(moves)} models without a source {'moved' if args.apply else 'to move'}; {copies} uncooked runtime "
          f"copies of existing sources (the cook replaces them)")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=ROOT / "assets_source")
    parser.add_argument("--output", type=Path, help="Output root (default assets_dev for desktop, "
                                                    "assets_cooked/android for android)")
    parser.add_argument("--profile", choices=("desktop", "android"))
    parser.add_argument("--dev", type=Path, help="--verify: the desktop runtime root (default assets_dev)")
    parser.add_argument("--android", type=Path, help="--verify: the android overlay (default assets_cooked/android)")
    parser.add_argument("--rules", type=Path, default=ROOT / "tools/cook/model_textures.yml")
    parser.add_argument("--cooker", type=Path, default=ROOT / ("build/game/openyamm_model_texture_cook"
                                                               + (".exe" if os.name == "nt" else "")))
    parser.add_argument("--only", help="Only models whose relative path matches (also selects WIP ground items)")
    parser.add_argument("--plan", action="store_true", help="Print decisions and projected sizes; write nothing")
    parser.add_argument("--verify", action="store_true", help="Validate cooked runtime files without sources")
    parser.add_argument("--force", action="store_true", help="Ignore receipts and re-cook every model and texture")
    parser.add_argument("--migrate", action="store_true",
                        help="List the uncooked models in --dev (default assets_dev) without a source in --source")
    parser.add_argument("--apply", action="store_true", help="--migrate: move them (the same inode, so hard links "
                                                             "to creature project outputs keep pointing at them)")
    args = parser.parse_args()
    if args.verify:
        return verify(args)
    if args.migrate:
        return migrate(args)
    rules = Rules(args.rules)
    profiles = [args.profile] if args.profile else ["desktop", "android"]
    paths = source_models(args.source.resolve(), args.only)
    if not paths:
        raise SystemExit(f"No source models under {args.source}")
    if args.plan:
        models = [plan_model(rules, args.source.resolve(), path, profiles) for path in paths]
        unified = reconcile(rules, models, profiles)
        print_plan(rules, models, profiles)
        if unified:
            print(f"  {len(unified)} shared textures had differing decisions; each takes its larger size and "
                  f"higher-quality codec")
        return 0
    if not args.profile:
        raise SystemExit("Choose --profile desktop or android (or --plan)")
    cook(args, rules, paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
