"""Geometry passes of the model cook (tools/cook_models.py), applied to a source GLB's document and binary chunk.

1. Hidden back faces. Creature exports mark every material double-sided, so the GPU rasterizes and shades every back
   face that draws before the surface covering it. For each opaque double-sided primitive the cooker
   (openyamm_model_texture_cook --geometry, CookModelGeometry.cpp) casts rays from just behind each triangle over its
   back hemisphere; when every ray hits an opaque triangle of the same mesh, no outside viewer can see that back (in
   the bind pose). The primitive then draws with a single-sided copy of its material (and of every
   KHR_materials_variants tier material), and each triangle whose back can be seen (capes, wings, skirts, open
   sleeves and necks) gets a reversed copy on duplicated vertices with negated normals, as two-sided cloth is usually
   modelled. It stays one draw in its slot. A primitive where more than MAX_BACK_COPY_SHARE of the triangles show
   their back keeps its double-sided material (cheaper than the copies). Alpha-tested and blended primitives are
   unchanged and do not block rays; dedicated shadow meshes (`openyamm_shadow_lods`) are unchanged. The test sees only
   the bind pose: a model whose posed shell opens where the bind pose is closed (the first-person arms, whose fist
   shows the palm's inside through the thumb's web) skips this pass with `back_faces: keep` in its .cook.yml.
2. Burn order. A primitive drawn with a burn map (material extras `openyamm_burn_map`, burn deaths) gets a
   `_BURN_ORDER` vertex attribute: the map's red channel at the vertex's TEXCOORD_0, the order in which a burn reaches
   it (normalized unsigned byte, nearest texel with wrapped UVs, as the game sampled the PNG before). The game reads
   it on the CPU for the flames of a burn death (WorldFxSystem::buildActorBurnSurface), so the burn map itself cooks
   like any other texture. Every material variant of a primitive must use the same burn map.
3. Vertex cache order. Every triangle primitive except blended materials (whose triangle order is their draw order)
   is reordered for the GPU's post-transform vertex cache, as GltfModelLoader does for uncooked models.

Primitives keep their slots (code and tests address them by index). GEOMETRY_RECIPE goes into the cook receipts, so a
change here re-cooks every model.
"""
import copy
import hashlib
import io
import math
from pathlib import Path
import struct
import subprocess
import tempfile

import numpy as np
from PIL import Image

RAY_COUNT = 64
# Nearly the whole back hemisphere: a back face can be seen at a grazing angle (thin tubes along a wing membrane).
MAX_RAY_ANGLE_DEGREES = 89.0
EPSILON_SCALE = 1e-4
MAX_BACK_COPY_SHARE = 0.25
TRIANGLES = 4
BURN_ORDER_ATTRIBUTE = "_BURN_ORDER"
# The in-place tool used before this pass existed (2026-10-12) marked the GLBs it processed.
LEGACY_MARKER = "openyamm_backface_split"
COMPONENT_DTYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32,
                    5126: np.float32}
TYPE_COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


def recipe():
    source = Path(__file__).read_bytes()
    return {"geometry_pass": hashlib.sha256(source).hexdigest()[:16], "rays": RAY_COUNT,
            "max_ray_angle": MAX_RAY_ANGLE_DEGREES, "epsilon_scale": EPSILON_SCALE,
            "max_back_copy_share": MAX_BACK_COPY_SHARE}


def accessor_array(document, binary, index):
    accessor = document["accessors"][index]
    if "sparse" in accessor or "bufferView" not in accessor:
        raise ValueError(f"accessor {index} is sparse or has no buffer view")
    view = document["bufferViews"][accessor["bufferView"]]
    dtype = np.dtype(COMPONENT_DTYPES[accessor["componentType"]])
    components = TYPE_COUNTS[accessor["type"]]
    element = dtype.itemsize * components
    stride = view.get("byteStride", element)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    if count == 0:
        return np.zeros((0, components), dtype=dtype)
    raw = np.frombuffer(binary, dtype=np.uint8, count=(count - 1) * stride + element, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, shape=(count, element), strides=(stride, 1))
    return np.ascontiguousarray(rows).view(dtype).reshape(count, components)


class Writer:
    """New accessors' data; compact() rebuilds the binary chunk from what is still referenced."""

    def __init__(self, document, binary):
        self.document = document
        self.binary = binary
        self.pending = {}

    def add_accessor(self, array, template):
        accessor = {key: template[key] for key in ("componentType", "type", "normalized") if key in template}
        accessor["count"] = int(array.shape[0])
        if "min" in template or "max" in template:
            accessor["min"] = array.min(axis=0).tolist() if len(array) else template.get("min")
            accessor["max"] = array.max(axis=0).tolist() if len(array) else template.get("max")
        self.document["accessors"].append(accessor)
        index = len(self.document["accessors"]) - 1
        dtype = COMPONENT_DTYPES[accessor["componentType"]]
        self.pending[index] = np.ascontiguousarray(array.astype(dtype)).tobytes()
        return index

    def array(self, index):
        """An accessor's values, including those added by an earlier pass and still pending."""
        if index not in self.pending:
            return accessor_array(self.document, self.binary, index)
        accessor = self.document["accessors"][index]
        dtype = COMPONENT_DTYPES[accessor["componentType"]]
        return np.frombuffer(self.pending[index], dtype=dtype).reshape(accessor["count"], TYPE_COUNTS[accessor["type"]])

    def add_indices(self, indices, vertex_count):
        component = 5123 if vertex_count < 65536 else 5125
        return self.add_accessor(np.asarray(indices).reshape(-1, 1), {"componentType": component, "type": "SCALAR"})

    def compact(self):
        document = self.document
        used = set()
        for mesh in document.get("meshes", []):
            for primitive in mesh["primitives"]:
                used.update(primitive["attributes"].values())
                if "indices" in primitive:
                    used.add(primitive["indices"])
                for target in primitive.get("targets", []):
                    used.update(target.values())
        for skin in document.get("skins", []):
            if "inverseBindMatrices" in skin:
                used.add(skin["inverseBindMatrices"])
        for animation in document.get("animations", []):
            for sampler in animation["samplers"]:
                used.update((sampler["input"], sampler["output"]))
        order = sorted(used)
        accessor_map = {old: new for new, old in enumerate(order)}
        out, views, view_map = bytearray(), [], {}

        def append_view(data, template):
            out.extend(b"\0" * (-len(out) % 4))
            view = {key: template[key] for key in ("byteStride", "target", "name", "extras") if key in template}
            view.update(buffer=0, byteOffset=len(out), byteLength=len(data))
            out.extend(data)
            views.append(view)
            return len(views) - 1

        def copy_view(index):
            if index not in view_map:
                view = document["bufferViews"][index]
                start = view.get("byteOffset", 0)
                view_map[index] = append_view(self.binary[start:start + view["byteLength"]], view)
            return view_map[index]
        accessors = []
        for old in order:
            accessor = document["accessors"][old]
            if old in self.pending:
                accessor["bufferView"] = append_view(self.pending[old], {})
                accessor.pop("byteOffset", None)
            else:
                accessor["bufferView"] = copy_view(accessor["bufferView"])
            accessors.append(accessor)
        for image in document.get("images", []):
            if "bufferView" in image:
                image["bufferView"] = copy_view(image["bufferView"])
        for mesh in document.get("meshes", []):
            for primitive in mesh["primitives"]:
                primitive["attributes"] = {key: accessor_map[value] for key, value in primitive["attributes"].items()}
                if "indices" in primitive:
                    primitive["indices"] = accessor_map[primitive["indices"]]
                if "targets" in primitive:
                    primitive["targets"] = [{key: accessor_map[value] for key, value in target.items()}
                                            for target in primitive["targets"]]
        for skin in document.get("skins", []):
            if "inverseBindMatrices" in skin:
                skin["inverseBindMatrices"] = accessor_map[skin["inverseBindMatrices"]]
        for animation in document.get("animations", []):
            for sampler in animation["samplers"]:
                sampler["input"] = accessor_map[sampler["input"]]
                sampler["output"] = accessor_map[sampler["output"]]
        document["accessors"] = accessors
        document["bufferViews"] = views
        document["buffers"] = [{"byteLength": len(out)}] if out else []
        return bytes(out)


def mapped_materials(document, primitive):
    indices = [primitive.get("material")]
    variants = primitive.get("extensions", {}).get("KHR_materials_variants")
    if variants:
        indices += [mapping["material"] for mapping in variants["mappings"]]
    return [document["materials"][index] for index in indices if index is not None]


def alpha_mode(material):
    return material.get("alphaMode", "OPAQUE")


def is_triangle_list(primitive):
    return primitive.get("mode", TRIANGLES) == TRIANGLES and "indices" in primitive


def run_cooker(cooker, request):
    with tempfile.TemporaryDirectory(prefix="cook-geometry-") as scratch:
        request_path = Path(scratch) / "request.bin"
        response_path = Path(scratch) / "response.bin"
        request_path.write_bytes(request)
        result = subprocess.run([str(cooker), "--geometry", str(request_path), str(response_path)], text=True,
                                capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "the geometry cook failed")
        response = response_path.read_bytes()
    if response[:4] != b"OYGR":
        raise RuntimeError("invalid geometry response")
    return response[4:]


def single_sided_material(document, copies, index):
    if index not in copies:
        material = copy.deepcopy(document["materials"][index])
        material.pop("doubleSided", None)
        document["materials"].append(material)
        copies[index] = len(document["materials"]) - 1
    return copies[index]


def with_single_sided_materials(document, copies, primitive):
    primitive = copy.deepcopy(primitive)
    if "material" in primitive:
        primitive["material"] = single_sided_material(document, copies, primitive["material"])
    variants = primitive.get("extensions", {}).get("KHR_materials_variants")
    if variants:
        for mapping in variants["mappings"]:
            mapping["material"] = single_sided_material(document, copies, mapping["material"])
    return primitive


def with_back_copies(document, binary, writer, primitive, triangles, hidden):
    """Every triangle as it is, plus a reversed copy of each one whose back can be seen, on duplicated vertices with
    negated normals (what a double-sided material draws for a back face)."""
    shown = triangles[~hidden]
    duplicated, local = np.unique(shown.reshape(-1), return_inverse=True)
    vertex_count = document["accessors"][primitive["attributes"]["POSITION"]]["count"]
    flipped = (local.reshape(-1, 3) + vertex_count)[:, [0, 2, 1]]

    def extended(index, name, delta):
        values = accessor_array(document, binary, index)
        extra = values[duplicated].copy()
        if name == "NORMAL":
            if extra.dtype.kind != "f":
                raise ValueError("quantized normals are not supported")
            extra = -extra
        elif name == "TANGENT" and not delta:
            extra[:, 3] = -extra[:, 3]    # the bitangent keeps its direction on the reversed face
        return writer.add_accessor(np.concatenate([values, extra]), document["accessors"][index])
    result = {key: copy.deepcopy(value) for key, value in primitive.items()
              if key not in ("attributes", "indices", "targets")}
    result["attributes"] = {name: extended(index, name, False) for name, index in primitive["attributes"].items()}
    if "targets" in primitive:
        result["targets"] = [{name: extended(index, name, True) for name, index in target.items()}
                             for target in primitive["targets"]]
    indices = np.concatenate([triangles.reshape(-1), flipped.reshape(-1)]).astype(np.uint32)
    result["indices"] = writer.add_indices(indices, vertex_count + len(duplicated))
    return result


def cull_hidden_back_faces(document, binary, writer, cooker):
    """Pass 1. Returns (checked triangles, culled triangles, back copies)."""
    if document.get("asset", {}).get("extras", {}).get(LEGACY_MARKER):
        return 0, 0, 0
    shadow_meshes = {index for mesh in document.get("meshes", [])
                     for index in mesh.get("extras", {}).get("openyamm_shadow_lods", [])}
    groups = []
    request = bytearray()
    for mesh_index, mesh in enumerate(document.get("meshes", [])):
        if mesh_index in shadow_meshes:
            continue
        candidates = [index for index, primitive in enumerate(mesh["primitives"]) if is_triangle_list(primitive)
                      and mapped_materials(document, primitive)
                      and all(material.get("doubleSided") and alpha_mode(material) == "OPAQUE"
                              for material in mapped_materials(document, primitive))]
        if not candidates:
            continue
        group = bytearray()
        sent, geometry = [], {}
        for index, primitive in enumerate(mesh["primitives"]):
            if not is_triangle_list(primitive):
                continue
            opaque = all(alpha_mode(material) == "OPAQUE" for material in mapped_materials(document, primitive))
            if not opaque and index not in candidates:
                continue
            positions = accessor_array(document, binary, primitive["attributes"]["POSITION"]).astype(np.float32)
            triangles = accessor_array(document, binary, primitive["indices"]).reshape(-1, 3).astype(np.uint32)
            geometry[index] = triangles
            flags = (1 if opaque else 0) | (2 if index in candidates else 0)
            group += struct.pack("<III", flags, len(positions), len(triangles))
            group += positions.tobytes() + triangles.tobytes()
            sent.append(index)
        request += struct.pack("<I", len(sent)) + group
        groups.append((mesh_index, candidates, geometry))
    if not groups:
        return 0, 0, 0
    header = b"OYGQ" + struct.pack("<IIIIff", 1, 1, len(groups), RAY_COUNT, MAX_RAY_ANGLE_DEGREES, EPSILON_SCALE)
    response = run_cooker(cooker, header + bytes(request))
    offset = 0
    copies = {}
    checked = culled = back_copies = 0
    for mesh_index, candidates, geometry in groups:
        primitives = document["meshes"][mesh_index]["primitives"]
        for index in candidates:
            triangles = geometry[index]
            hidden = np.frombuffer(response, dtype=np.uint8, count=len(triangles), offset=offset).astype(bool)
            offset += len(triangles)
            checked += len(triangles)
            if not hidden.any() or 1.0 - hidden.mean() > MAX_BACK_COPY_SHARE:
                continue
            culled += int(hidden.sum())
            back_copies += int((~hidden).sum())
            primitive = primitives[index]
            if not hidden.all():
                primitive = with_back_copies(document, binary, writer, primitive, triangles, hidden)
            primitives[index] = with_single_sided_materials(document, copies, primitive)
    if offset != len(response):
        raise RuntimeError("geometry response size mismatch")
    return checked, culled, back_copies


def burn_map_red(document, binary, material, decoded):
    """The red channel of the material's burn map (rows from the top), or None without one."""
    burn = material.get("extras", {}).get("openyamm_burn_map")
    if burn is None:
        return None
    if burn.get("texCoord", 0) != 0:
        raise ValueError("a burn map must use TEXCOORD_0")
    image_index = document["textures"][burn["index"]]["source"]
    if image_index not in decoded:
        view = document["bufferViews"][document["images"][image_index]["bufferView"]]
        start = view.get("byteOffset", 0)
        png = binary[start:start + view["byteLength"]]
        decoded[image_index] = (hashlib.sha256(png).hexdigest(),
                                np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))[:, :, 0].copy())
    return decoded[image_index]


def bake_burn_order(document, binary, writer):
    """Pass 2, after pass 1 (whose back copies duplicate the texture coordinates). Returns the primitives baked."""
    decoded = {}
    baked = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            maps = [burn_map_red(document, binary, material, decoded)
                    for material in mapped_materials(document, primitive)]
            maps = {found[0]: found[1] for found in maps if found is not None}
            if not maps:
                continue
            if len(maps) > 1:
                raise ValueError(f"mesh {mesh.get('name')!r}: material variants use different burn maps")
            if "TEXCOORD_0" not in primitive["attributes"]:
                raise ValueError(f"mesh {mesh.get('name')!r}: a burned primitive needs TEXCOORD_0")
            red = next(iter(maps.values()))
            uv = writer.array(primitive["attributes"]["TEXCOORD_0"])
            if uv.dtype != np.float32:
                raise ValueError(f"mesh {mesh.get('name')!r}: quantized texture coordinates are not supported")
            height, width = red.shape
            # The game's float32 arithmetic: the fraction of the wrapped coordinate times the size, truncated.
            fraction = uv - np.floor(uv)
            x = np.minimum((fraction[:, 0] * np.float32(width)).astype(np.int64), width - 1)
            y = np.minimum((fraction[:, 1] * np.float32(height)).astype(np.int64), height - 1)
            order = red[y, x].reshape(-1, 1)
            primitive["attributes"][BURN_ORDER_ATTRIBUTE] = writer.add_accessor(
                order, {"componentType": 5121, "type": "SCALAR", "normalized": True})
            baked += 1
    return baked


def order_for_vertex_cache(document, binary, writer, cooker):
    """Pass 3, on the document after pass 1 (whose new accessors are still pending in the writer)."""
    jobs = []
    request = bytearray()
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            if not is_triangle_list(primitive) or any(alpha_mode(material) == "BLEND"
                                                      for material in mapped_materials(document, primitive)):
                continue
            index = primitive["indices"]
            indices = (np.frombuffer(writer.pending[index], dtype=COMPONENT_DTYPES[
                document["accessors"][index]["componentType"]]) if index in writer.pending
                else accessor_array(document, binary, index).reshape(-1)).astype(np.uint32)
            vertex_count = document["accessors"][primitive["attributes"]["POSITION"]]["count"]
            request += struct.pack("<II", vertex_count, len(indices)) + indices.tobytes()
            jobs.append((primitive, len(indices), vertex_count))
    if not jobs:
        return
    response = run_cooker(cooker, b"OYGQ" + struct.pack("<III", 1, 2, len(jobs)) + bytes(request))
    offset = 0
    for primitive, count, vertex_count in jobs:
        reordered = np.frombuffer(response, dtype=np.uint32, count=count, offset=offset)
        offset += count * 4
        primitive["indices"] = writer.add_indices(reordered, vertex_count)
    if offset != len(response):
        raise RuntimeError("geometry response size mismatch")


def cook_geometry(document, binary, cooker, cull_back_faces=True):
    """Applies the passes; returns the new binary chunk and a summary for the cooked GLB's extras. Without
    cull_back_faces (a model's .cook.yml `back_faces: keep`) pass 1 is skipped and double-sided materials stay so."""
    writer = Writer(document, binary)
    checked, culled, back_copies = cull_hidden_back_faces(document, binary, writer, cooker) if cull_back_faces \
        else (0, 0, 0)
    burn_order = bake_burn_order(document, binary, writer)
    order_for_vertex_cache(document, binary, writer, cooker)
    summary = {"checked_triangles": checked, "culled_triangles": culled, "back_copies": back_copies,
               "vertex_cache": True}
    if burn_order:
        summary["burn_order_primitives"] = burn_order
    return writer.compact(), summary
