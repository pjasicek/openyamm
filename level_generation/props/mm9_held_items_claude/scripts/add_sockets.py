#!/usr/bin/env python3
"""MM9's sockets (an ABC's Sockets section: AttachProp's attach points) as nodes `Socket_<name>` on our creature models.

A socket is a frame relative to one node of MM9's skeleton. Our models are that skeleton mirrored on x at about 1/40,
in a rest pose of their own and with bone axes of their own, but they play MM9's animations: a bone's world rotation in
our clip differs from MM9's (mirrored) by a constant turn. That turn is measured over a clip both play (matched by
name, else by pose signature as generate_mm9_monster_sounds.py does) and carries the socket's frame onto our bone,
anchored at our bone (its rest position may differ from MM9's). The node's scale takes an item exported at
heldlib.ITEM_SCALE to the model's own. A piece cut from the model (Ercc's cup, build_items.py) gets a socket at its
node's frame relative to the nearest ancestor we have.

    python3 level_generation/props/mm9_held_items_claude/scripts/add_sockets.py [model ...]   # export/<model>.glb

Install each with tools/install_model.py --world mm9; rerunning starts again from the installed source (sockets of the
same name are replaced).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import heldlib
from heldlib import abc

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(heldlib.ROOT / "tools/mm9_import_discovery"))
import generate_mm9_monster_sounds as sounds  # noqa: E402

# model: (its ABC, the sockets to carry: ABC socket names, or ("node", <ABC node>) for a cut piece's node, preferred
# clip pairs [(our clip, MM9 animation)] for the turn)
CREATURES = {
    "mm9_monk": ("MONK.abc", ["Hoe", "Broom", "Hammer", "Cloth"], [("Hoe", "hoe"), ("Sweep", "sweep"),
                                                                    ("Wash", "wash")]),
    "mm9_peasantdm1": ("PEASANTDM1.abc", ["RHand1"], []),
    "mm9_peasantdm2": ("PEASANTDM2.abc", ["RHand1"], []),
    "mm9_dwarf": ("DWARF.abc", ["RHand1"], []),
    "mm9_honkm": ("HONKMALE.abc", ["pamphlet"], []),
    "mm9_honkf": ("HONKFEMALE.abc", ["pamphlet"], []),
    "mm9_peasantm2": ("PROPS/ERCC.abc", [("node", "cup01")], [("ercc01a", "ercc01a")]),
    # The Argument (ARG_Kira.scr): her sword on the sheath once she stands, in her right hand from Sc2_Kira17's key.
    "mm9_kira": ("KIRA.abc", ["sheath", "RHand1"], [("Sc2_Kira17", "Sc2_Kira17"), ("Sc2_KIRA16b", "Sc2_KIRA16b"),
                                                  ("Standing", "stand")]),
}
SOCKET_NAMES = {("node", "cup01"): "Cup", "sheath": "Sheath"}


def animations_with_children(path: Path) -> tuple[object, list]:
    model = abc.read_abc(path)
    animations = [(model, animation) for animation in model.animations]
    for child in sounds.child_models(path):
        child_path = next((p for p in heldlib.MODELS.rglob("*.abc") if p.name.lower() == Path(child).name.lower()),
                          None)
        if child_path is None:
            continue
        child_model = abc.read_abc(child_path)
        animations += [(child_model, animation) for animation in child_model.animations]
    return model, animations


def clip_pairs(glb: Path, document: dict, blob: bytes, abc_path: Path, preferred) -> list[tuple[str, object, object]]:
    """[(our clip, the ABC model holding the animation, the animation)], preferred pairs first."""
    model, animations = animations_with_children(abc_path)
    by_name = {animation.name.lower(): (owner, animation) for owner, animation in animations}
    clips = {clip["name"] for clip in document.get("animations", [])}
    pairs = [(ours, *by_name[theirs.lower()]) for ours, theirs in preferred
             if ours in clips and theirs.lower() in by_name]
    if pairs:
        return pairs
    source_animations = sounds.read_source_animations(abc_path)
    for child in sounds.child_models(abc_path):
        child_path = next((p for p in heldlib.MODELS.rglob("*.abc") if p.name.lower() == Path(child).name.lower()),
                          None)
        if child_path is not None:
            source_animations += sounds.read_source_animations(child_path)
    sources = sounds.clip_sources(sounds.read_glb_clips(glb), source_animations)
    for ours, source in sources.items():
        if source.name.lower() in by_name and ours not in ("Dead", "Death", "Death2"):
            pairs.append((ours, *by_name[source.name.lower()]))
    return pairs


def socket_frame(model, socket) -> tuple[str, np.ndarray]:
    """The socket's parent node name and its frame relative to it (MM9's frame)."""
    if isinstance(socket, tuple):
        nodes = {node.name: index for index, node in enumerate(model.nodes)}
        index = nodes[socket[1]]
        bind = heldlib.abc_pose(model, None, 0.0)
        parent = model.nodes[index].parent_index
        return model.nodes[parent].name, np.linalg.inv(bind[parent]) @ bind[index]
    found = next(item for item in model.sockets if item.name == socket)
    return model.nodes[found.node_index].name, heldlib.trs(found.translation, found.rotation, [1, 1, 1])


def main() -> int:
    only = set(sys.argv[1:])
    if only - set(CREATURES):
        raise SystemExit(f"unknown models: {sorted(only - set(CREATURES))}")
    for name, (abc_name, sockets, preferred) in CREATURES.items():
        if only and name not in only:
            continue
        source = heldlib.ROOT / f"assets_source/worlds/mm9/models/{name}.glb"
        document, blob = heldlib.read_glb(source)
        abc_path = heldlib.abc_file(abc_name)
        model = abc.read_abc(abc_path)
        scale = heldlib.frame_scale(document, model)
        nodes = {node.get("name"): index for index, node in enumerate(document["nodes"])}
        pairs = clip_pairs(source, document, blob, abc_path, preferred)
        if not pairs:
            raise SystemExit(f"{name}: no clip pairs its ABC's animations")
        for socket in sockets:
            parent_name, relative = socket_frame(model, socket)
            node_name = "Socket_" + SOCKET_NAMES.get(socket, socket if isinstance(socket, str) else socket[1])
            parent = nodes[parent_name]
            mirrored_rotation = heldlib.MIRROR @ relative[:3, :3] @ heldlib.MIRROR
            locals_ = []
            for ours, owner, animation in pairs[:3]:
                clip = heldlib.glb_clip(document, ours)
                seconds = heldlib.glb_clip_seconds(document, blob, clip)
                owner_nodes = {node.name: index for index, node in enumerate(owner.nodes)}
                if parent_name not in owner_nodes:
                    continue
                theirs_seconds = max(key.time_ms for key in animation.keyframes) / 1000.0
                for fraction in (0.0, 0.25, 0.5, 0.75):
                    world = heldlib.glb_pose(document, blob, clip, fraction * seconds)[parent]
                    theirs = heldlib.abc_pose(owner, animation, fraction * theirs_seconds)[owner_nodes[parent_name]]
                    theirs_rotation = heldlib.MIRROR @ heldlib.rotation_of(theirs) @ heldlib.MIRROR
                    target = np.eye(4)
                    target[:3, :3] = theirs_rotation @ mirrored_rotation * (scale / heldlib.ITEM_SCALE)
                    target[:3, 3] = world[:3, 3] + scale * (heldlib.MIRROR @ heldlib.rotation_of(theirs)
                                                            @ relative[:3, 3])
                    locals_.append(np.linalg.inv(world) @ target)
            if not locals_:
                raise SystemExit(f"{name}: no clip moves {parent_name}")
            stack = np.array(locals_)
            local = stack.mean(0)
            spread_t = float(np.linalg.norm(stack[:, :3, 3] - local[:3, 3], axis=1).max())
            rotation = local[:3, :3]
            node_scale = float(np.cbrt(np.linalg.det(rotation)))
            u, _, vt = np.linalg.svd(rotation / node_scale)
            rotation = u @ vt
            angles = [float(np.degrees(np.arccos(np.clip((np.trace(rotation.T @ (item[:3, :3] / node_scale)) - 1) / 2,
                                                         -1, 1)))) for item in stack]
            entry = {"name": node_name, "translation": [float(x) for x in local[:3, 3]],
                     "rotation": heldlib.matrix_quat(rotation), "scale": [node_scale] * 3}
            if node_name in nodes:
                document["nodes"][nodes[node_name]] = {**entry, **({"children": document["nodes"][nodes[node_name]]
                                                                    ["children"]}
                                                                   if "children" in document["nodes"][nodes[node_name]]
                                                                   else {})}
            else:
                document["nodes"].append(entry)
                nodes[node_name] = len(document["nodes"]) - 1
                document["nodes"][parent].setdefault("children", []).append(nodes[node_name])
            print(f"{name}: {node_name} on {parent_name}, scale {node_scale:.3f}, over {len(stack)} poses of "
                  f"{[pair[0] for pair in pairs[:3]]}: spread {spread_t:.4f} units, {max(angles):.1f} degrees")
        heldlib.write_glb(PROJECT / "export" / f"{name}.glb", document, blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
